"""
Parser de EFD PIS/COFINS focado em créditos de entradas.

Registros tratados:
- C100/C170: NF-e de entrada (itens)
- A100/A170: serviços tomados
- C500/C501/C505: energia elétrica
- D100/D101/D105: fretes / CT-e
- F100/F120: demais documentos geradores de crédito
- M200: apuração do PIS
- M105: créditos de PIS por natureza

Pensado para trabalhar em conjunto com o app Streamlit (app.py).
"""

import io
import zipfile
from typing import List, Tuple, Dict

import pandas as pd


# =====================================================================
# Helpers básicos
# =====================================================================

def _to_str(v) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _to_float(v) -> float:
    try:
        s = str(v).strip()
        if s == "":
            return 0.0
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except Exception:
        return 0.0


def _decode_bytes(b: bytes) -> str:
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("latin-1", errors="ignore")


def _extract_txt_from_zip(uploaded_file) -> List[str]:
    lines: List[str] = []
    with zipfile.ZipFile(uploaded_file) as zf:
        for name in zf.namelist():
            if name.lower().endswith(".txt"):
                raw = zf.read(name)
                decoded = _decode_bytes(raw)
                lines.extend(decoded.splitlines())
    return lines


def load_efd_from_upload(uploaded_file) -> List[str]:
    """
    Recebe um arquivo subido no Streamlit (txt ou zip) e devolve
    a lista de linhas do(s) arquivo(s) .txt contido(s).
    """
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()

    if name.endswith(".zip"):
        buffer = io.BytesIO(raw)
        return _extract_txt_from_zip(buffer)

    if name.endswith(".txt"):
        decoded = _decode_bytes(raw)
        return decoded.splitlines()

    raise ValueError("Arquivo inválido. Envie .txt ou .zip contendo .txt de EFD PIS/COFINS.")


# =====================================================================
# Metadados (0000, 0150, 0200)
# =====================================================================

def _extract_0000_metadata(lines: List[str]) -> Tuple[str, str]:
    """
    Extrai COMPETENCIA (MM/AAAA) e NOME da empresa do registro 0000.
    """
    competencia = ""
    empresa = ""
    for line in lines:
        p = line.strip().split("|")
        if len(p) < 9:
            continue
        if p[1] == "0000":
            dt_ini = _to_str(p[6])
            # dt_ini: AAAAMMDD
            if len(dt_ini) == 8:
                competencia = dt_ini[4:6] + "/" + dt_ini[0:4]  # MM/AAAA
            empresa = _to_str(p[7])
            break
    return competencia, empresa


def _build_maps(lines: List[str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Cria:
    - map_part_nome: COD_PART -> NOME (0150)
    - map_coditem_ncm: COD_ITEM -> NCM (0200)
    """
    map_part_nome: Dict[str, str] = {}
    map_coditem_ncm: Dict[str, str] = {}

    for line in lines:
        p = line.strip().split("|")
        if len(p) < 3:
            continue
        reg = p[1]

        if reg == "0150":
            cod_part = _to_str(p[2])
            nome = _to_str(p[3]) if len(p) > 3 else ""
            if cod_part:
                map_part_nome[cod_part] = nome

        if reg == "0200":
            cod_item = _to_str(p[2])
            ncm = _to_str(p[7]) if len(p) > 7 else ""
            if cod_item:
                map_coditem_ncm[cod_item] = ncm

    return map_part_nome, map_coditem_ncm


# =====================================================================
# Formatador BR (pra não ferrar o to_float do app)
# =====================================================================

def _fmt_brl(x: float) -> str:
    """
    Converte float -> string no formato BR "9999,99"
    (sem separador de milhar).
    """
    return f"{x:.2f}".replace(".", ",")


# =====================================================================
# Parser principal
# =====================================================================

def parse_efd_piscofins(lines: List[str]):
    """
    Faz o parsing das linhas de EFD PIS/COFINS e retorna:

    df_c100:   detalhamento de NF-e de entrada (C100/C170)
    df_outros: créditos de serviços, energia, fretes, F100/F120 etc.
    df_ap_pis: M200
    df_cred_pis: M105
    competencia, empresa
    """
    competencia, empresa = _extract_0000_metadata(lines)
    map_part_nome, map_coditem_ncm = _build_maps(lines)

    records_c100 = []
    records_out = []
    records_ap_pis = []
    records_cred_pis = []

    current_c100 = None
    current_a100 = None
    current_c500 = None
    current_d100 = None
    current_f100 = None

    # Acumuladores de energia elétrica (C500/C501/C505)
    c500_pis_bc = 0.0
    c500_pis_aliq = 0.0
    c500_pis_val = 0.0

    c500_cof_bc = 0.0
    c500_cof_aliq = 0.0
    c500_cof_val = 0.0

    def _get(p, idx, default=""):
        try:
            return p[idx]
        except IndexError:
            return default

    def finalize_c500():
        """
        Grava uma linha consolidando PIS (C501) e COFINS (C505)
        para o cabeçalho C500 atual.
        """
        nonlocal current_c500, c500_pis_bc, c500_pis_aliq, c500_pis_val
        nonlocal c500_cof_bc, c500_cof_aliq, c500_cof_val

        if current_c500 is None:
            return

        if (
            c500_pis_bc == 0.0
            and c500_pis_val == 0.0
            and c500_cof_bc == 0.0
            and c500_cof_val == 0.0
        ):
            # nada a gravar
            current_c500 = None
            c500_pis_bc = c500_pis_aliq = c500_pis_val = 0.0
            c500_cof_bc = c500_cof_aliq = c500_cof_val = 0.0
            return

        # Exemplo real:
        # |C500|F10372|06|00|3||150918139|14022025|14022025|5947,47|0||98,13|452,01||
        cod_part = _get(current_c500, 2)
        num_doc = _get(current_c500, 7)
        dt_doc = _get(current_c500, 8)
        vl_doc = _get(current_c500, 10)

        records_out.append(
            {
                "COMPETENCIA": competencia,
                "EMPRESA": empresa,
                "TIPO": "C500/C501/C505",
                "DOC": num_doc,
                "DT_DOC": dt_doc,
                "COD_PART": cod_part,
                "NOME_PART": map_part_nome.get(cod_part, ""),
                "VL_DOC": vl_doc,
                "CFOP": "",
                "CST_PIS": "",
                "VL_BC_PIS": _fmt_brl(c500_pis_bc),
                "ALIQ_PIS": _fmt_brl(c500_pis_aliq),
                "VL_PIS": _fmt_brl(c500_pis_val),
                "CST_COFINS": "",
                "VL_BC_COFINS": _fmt_brl(c500_cof_bc),
                "ALIQ_COFINS": _fmt_brl(c500_cof_aliq),
                "VL_COFINS": _fmt_brl(c500_cof_val),
            }
        )

        current_c500 = None
        c500_pis_bc = c500_pis_aliq = c500_pis_val = 0.0
        c500_cof_bc = c500_cof_aliq = c500_cof_val = 0.0

    # ----------------------------------------------------------
    # Loop principal nas linhas do arquivo
    # ----------------------------------------------------------
    for line in lines:
        p = line.strip().split("|")
        if len(p) < 3:
            continue
        reg = p[1]

        # ----------------- C100 / C170 (NF-e entradas) -----------------
        if reg == "C100":
            current_c100 = p
            continue

        if reg == "C170" and current_c100:
            ind_oper = _get(current_c100, 2)  # 0=entrada, 1=saída
            if ind_oper != "0":
                # só entradas geram crédito de PIS/COFINS
                continue

            cod_part = _get(current_c100, 4)
            modelo = _get(current_c100, 5)
            situacao = _get(current_c100, 9)
            num_doc = _get(current_c100, 8)
            dt_doc = _get(current_c100, 10)
            dt_entr = _get(current_c100, 11)
            vl_doc = _get(current_c100, 12)

            # C170 (layout PIS/COFINS)
            num_item = _get(p, 2)
            cod_item = _get(p, 3)
            descr_item = _get(p, 4)
            cfop = _get(p, 11)

            cst_pis = _get(p, 12)
            vl_bc_pis = _get(p, 13)
            aliq_pis = _get(p, 14)
            vl_pis = _get(p, 15)

            cst_cof = _get(p, 18)
            vl_bc_cof = _get(p, 19)
            aliq_cof = _get(p, 20)
            vl_cof = _get(p, 21)

            if (
                _to_float(vl_pis) == 0.0
                and _to_float(vl_cof) == 0.0
                and _to_float(vl_bc_pis) == 0.0
                and _to_float(vl_bc_cof) == 0.0
            ):
                continue

            records_c100.append(
                {
                    "COMPETENCIA": competencia,
                    "EMPRESA": empresa,
                    "IND_OPER": ind_oper,
                    "COD_PART": cod_part,
                    "NOME_PART": map_part_nome.get(cod_part, ""),
                    "MODELO": modelo,
                    "SIT_DOC": situacao,
                    "NUM_DOC": num_doc,
                    "DT_DOC": dt_doc,
                    "DT_ENTR": dt_entr,
                    "VL_DOC": vl_doc,
                    "NUM_ITEM": num_item,
                    "COD_ITEM": cod_item,
                    "DESCR_ITEM": descr_item,
                    "NCM": map_coditem_ncm.get(cod_item, ""),
                    "CFOP": cfop,
                    "CST_PIS": cst_pis,
                    "VL_BC_PIS": vl_bc_pis,
                    "ALIQ_PIS": aliq_pis,
                    "VL_PIS": vl_pis,
                    "CST_COFINS": cst_cof,
                    "VL_BC_COFINS": vl_bc_cof,
                    "ALIQ_COFINS": aliq_cof,
                    "VL_COFINS": vl_cof,
                }
            )
            continue

        # ----------------- A100 / A170 (serviços tomados) -----------------
        if reg == "A100":
            current_a100 = p
            continue

        if reg == "A170" and current_a100:
            cod_part = _get(current_a100, 4)
            num_doc = _get(current_a100, 8)
            dt_doc = _get(current_a100, 9)
            vl_doc = _get(current_a100, 11)

            # A170 (layout oficial GP 1.35):
            # 09 CST_PIS, 10 VL_BC_PIS, 11 ALIQ_PIS, 12 VL_PIS
            # 13 CST_COFINS, 14 VL_BC_COFINS, 15 ALIQ_COFINS, 16 VL_COFINS
            cfop = ""  # A170 não possui CFOP próprio
            cst_pis = _get(p, 9)
            vl_bc_pis = _get(p, 10)
            aliq_pis = _get(p, 11)
            vl_pis = _get(p, 12)

            cst_cof = _get(p, 13)
            vl_bc_cof = _get(p, 14)
            aliq_cof = _get(p, 15)
            vl_cof = _get(p, 16)

            if (
                _to_float(vl_pis) == 0.0
                and _to_float(vl_cof) == 0.0
                and _to_float(vl_bc_pis) == 0.0
                and _to_float(vl_bc_cof) == 0.0
            ):
                continue

            records_out.append(
                {
                    "COMPETENCIA": competencia,
                    "EMPRESA": empresa,
                    "TIPO": "A100/A170",
                    "DOC": num_doc,
                    "DT_DOC": dt_doc,
                    "COD_PART": cod_part,
                    "NOME_PART": map_part_nome.get(cod_part, ""),
                    "VL_DOC": vl_doc,
                    "CFOP": cfop,
                    "CST_PIS": cst_pis,
                    "VL_BC_PIS": vl_bc_pis,
                    "ALIQ_PIS": aliq_pis,
                    "VL_PIS": vl_pis,
                    "CST_COFINS": cst_cof,
                    "VL_BC_COFINS": vl_bc_cof,
                    "ALIQ_COFINS": aliq_cof,
                    "VL_COFINS": vl_cof,
                }
            )
            continue

        # ----------------- C500 / C501 / C505 (energia elétrica) -----------------
        if reg == "C500":
            # Fecha o C500 anterior (se houver) e inicia um novo
            finalize_c500()
            current_c500 = p
            continue

        if reg == "C501":
            # |C501|50|5947,47|01|5947,47|1,65|98,13|...|
            # 02 CST_PIS
            # 03 VL_ITEM
            # 04 NAT_BC_CRED
            # 05 VL_BC_PIS
            # 06 ALIQ_PIS
            # 07 VL_PIS
            if current_c500 is not None:
                c500_pis_bc += _to_float(_get(p, 5))
                c500_pis_aliq = _to_float(_get(p, 6))
                c500_pis_val += _to_float(_get(p, 7))
            continue

        if reg == "C505":
            # |C505|50|5947,47|01|5947,47|7,6|452,01|...|
            # 02 CST_COFINS
            # 03 VL_ITEM
            # 04 NAT_BC_CRED
            # 05 VL_BC_COFINS
            # 06 ALIQ_COFINS
            # 07 VL_COFINS
            if current_c500 is not None:
                c500_cof_bc += _to_float(_get(p, 5))
                c500_cof_aliq = _to_float(_get(p, 6))
                c500_cof_val += _to_float(_get(p, 7))
            continue

        # ----------------- D100 / D101 / D105 (fretes / CT-e) -----------------
        if reg == "D100":
            current_d100 = p
            continue

        if reg == "D101":
            if current_d100 is None:
                continue
            d100 = current_d100

            cod_part = _get(d100, 4)
            num_doc = _get(d100, 8)
            dt_doc = _get(d100, 10)
            vl_doc = _get(d100, 12)

            cst_pis = _get(p, 3)
            vl_bc_pis = _get(p, 4)
            aliq_pis = _get(p, 5)
            vl_pis = _get(p, 6)

            if _to_float(vl_pis) == 0.0 and _to_float(vl_bc_pis) == 0.0:
                continue

            records_out.append(
                {
                    "COMPETENCIA": competencia,
                    "EMPRESA": empresa,
                    "TIPO": "D100/D101",
                    "DOC": num_doc,
                    "DT_DOC": dt_doc,
                    "COD_PART": cod_part,
                    "NOME_PART": map_part_nome.get(cod_part, ""),
                    "VL_DOC": vl_doc,
                    "CFOP": "",
                    "CST_PIS": cst_pis,
                    "VL_BC_PIS": vl_bc_pis,
                    "ALIQ_PIS": aliq_pis,
                    "VL_PIS": vl_pis,
                    "CST_COFINS": "",
                    "VL_BC_COFINS": 0.0,
                    "ALIQ_COFINS": 0.0,
                    "VL_COFINS": 0.0,
                }
            )
            continue

        if reg == "D105":
            if current_d100 is None:
                continue
            d100 = current_d100

            cod_part = _get(d100, 4)
            num_doc = _get(d100, 8)
            dt_doc = _get(d100, 10)
            vl_doc = _get(d100, 12)

            cst_cof = _get(p, 3)
            vl_bc_cof = _get(p, 4)
            aliq_cof = _get(p, 5)
            vl_cof = _get(p, 6)

            if _to_float(vl_cof) == 0.0 and _to_float(vl_bc_cof) == 0.0:
                continue

            records_out.append(
                {
                    "COMPETENCIA": competencia,
                    "EMPRESA": empresa,
                    "TIPO": "D100/D105",
                    "DOC": num_doc,
                    "DT_DOC": dt_doc,
                    "COD_PART": cod_part,
                    "NOME_PART": map_part_nome.get(cod_part, ""),
                    "VL_DOC": vl_doc,
                    "CFOP": "",
                    "CST_PIS": "",
                    "VL_BC_PIS": 0.0,
                    "ALIQ_PIS": 0.0,
                    "VL_PIS": 0.0,
                    "CST_COFINS": cst_cof,
                    "VL_BC_COFINS": vl_bc_cof,
                    "ALIQ_COFINS": aliq_cof,
                    "VL_COFINS": vl_cof,
                }
            )
            continue

        # ----------------- F100 / F120 (demais docs / créditos) -----------------
        if reg == "F100":
            current_f100 = p
            continue

        if reg == "F120":
            if current_f100 is None:
                continue
            f100 = current_f100

            cod_part = _get(f100, 3)
            num_doc = _get(f100, 5)
            dt_doc = _get(f100, 6)
            vl_doc = _get(f100, 7)

            # F120 (layout oficial):
            # 08 CST_PIS, 09 VL_BC_PIS, 10 ALIQ_PIS, 11 VL_PIS
            # 12 CST_COFINS, 13 VL_BC_COFINS, 14 ALIQ_COFINS, 15 VL_COFINS
            cst_pis = _get(p, 8)
            vl_bc_pis = _get(p, 9)
            aliq_pis = _get(p, 10)
            vl_pis = _get(p, 11)

            cst_cof = _get(p, 12)
            vl_bc_cof = _get(p, 13)
            aliq_cof = _get(p, 14)
            vl_cof = _get(p, 15)

            if (
                _to_float(vl_pis) == 0.0
                and _to_float(vl_cof) == 0.0
                and _to_float(vl_bc_pis) == 0.0
                and _to_float(vl_bc_cof) == 0.0
            ):
                continue

            records_out.append(
                {
                    "COMPETENCIA": competencia,
                    "EMPRESA": empresa,
                    "TIPO": "F100/F120",
                    "DOC": num_doc,
                    "DT_DOC": dt_doc,
                    "COD_PART": cod_part,
                    "NOME_PART": map_part_nome.get(cod_part, ""),
                    "VL_DOC": vl_doc,
                    "CST_PIS": cst_pis,
                    "VL_BC_PIS": vl_bc_pis,
                    "ALIQ_PIS": aliq_pis,
                    "VL_PIS": vl_pis,
                    "CST_COFINS": cst_cof,
                    "VL_BC_COFINS": vl_bc_cof,
                    "ALIQ_COFINS": aliq_cof,
                    "VL_COFINS": vl_cof,
                }
            )
            continue

        # ----------------- M200 (Apuração PIS) -----------------
        if reg == "M200":
            row = {
                "COMPETENCIA": competencia,
                "EMPRESA": empresa,
                "VL_TOT_CONT_NC_PER": _to_float(_get(p, 2)),
                "VL_CONT_NC_REC": _to_float(_get(p, 3)),
                "VL_TOT_CRED_DESC": _to_float(_get(p, 4)),
                "VL_TOT_CONT_REAL": _to_float(_get(p, 5)),
                "VL_CONT_NC_REST": _to_float(_get(p, 6)),
                "VL_CONT_NC_RET": _to_float(_get(p, 7)),
                "VL_CONT_NC_SUSP": _to_float(_get(p, 8)),
                "VL_CONT_NC_ADIC": _to_float(_get(p, 9)),
            }
            records_ap_pis.append(row)
            continue

        # ----------------- M105 (Créditos PIS por natureza) -----------------
        if reg == "M105":
            nat = _get(p, 2)
            cst = _get(p, 3)
            vl_bc = _get(p, 4)
            aliq = _get(p, 5)
            vl_cred = _get(p, 6)

            records_cred_pis.append(
                {
                    "COMPETENCIA": competencia,
                    "EMPRESA": empresa,
                    "NAT_BC_CRED": nat,
                    "CST": cst,
                    "VL_BC": vl_bc,
                    "ALIQ": aliq,
                    "VL_CRED": vl_cred,
                }
            )
            continue

    # Finaliza eventual C500 pendente
    finalize_c500()

    df_c100 = pd.DataFrame(records_c100)
    df_outros = pd.DataFrame(records_out)
    df_ap_pis = pd.DataFrame(records_ap_pis)
    df_cred_pis = pd.DataFrame(records_cred_pis)

    return df_c100, df_outros, df_ap_pis, df_cred_pis, competencia, empresa
