# parser_pis_cofins.py
"""
Parser de EFD PIS/COFINS focado em créditos de entradas
(C100/C170, A100/A170, C500/C501/C505, D100/D101/D105, F100/F120)
e nos registros de apuração de PIS (M200) e créditos PIS (M105).

Pensado para trabalhar em conjunto com o app Streamlit (app.py).
"""

import io
import zipfile
from typing import Tuple, List, Dict

import pandas as pd


# =========================
# Helpers básicos
# =========================


def _to_str(s) -> str:
    return "" if s is None else str(s)


def _to_float(s) -> float:
    """
    Converte string em número float, aceitando formatos BR (1.234,56).
    """
    s = _to_str(s).strip()
    if not s:
        return 0.0
    # trata "1.234,56" -> "1234.56"
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def _get(parts: List[str], idx: int) -> str:
    return parts[idx] if len(parts) > idx else ""


def _decode_bytes(data: bytes) -> str:
    """
    Decodifica bytes tentando latin-1 e depois utf-8.
    """
    for enc in ("latin-1", "utf-8"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("latin-1", errors="ignore")


def _extract_txt_from_zip(data: bytes) -> str:
    """
    Recebe bytes de um .zip e devolve o conteúdo (texto) do primeiro .txt encontrado.
    """
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if name.lower().endswith(".txt"):
                with z.open(name) as f:
                    return _decode_bytes(f.read())
    raise ValueError("Nenhum arquivo .txt encontrado dentro do .zip")


def load_efd_from_upload(uploaded_file) -> List[str]:
    """
    Recebe um UploadedFile do Streamlit (txt ou zip) e devolve
    uma lista de linhas do SPED.
    """
    raw = uploaded_file.read()
    name = uploaded_file.name.lower()

    if name.endswith(".zip"):
        text = _extract_txt_from_zip(raw)
    else:
        text = _decode_bytes(raw)

    # divide em linhas, removendo vazios extremos
    return [ln for ln in text.splitlines() if ln.strip()]


# =========================
# Metadados / mapas auxiliares
# =========================


def _extract_metadata_0000(lines: List[str]) -> Tuple[str, str]:
    """
    Extrai:
      - competência (MM/AAAA)
      - empresa (razão social)
    a partir do registro 0000.
    """
    competencia = ""
    empresa = ""

    for line in lines:
        p = line.strip().split("|")
        if len(p) > 1 and p[1] == "0000":
            # |0000|...|DT_INI|DT_FIN|NOME|
            dt_ini = _get(p, 6)
            empresa = _get(p, 8)
            if len(dt_ini) == 8 and dt_ini.isdigit():
                # formato ddmmaaaa
                competencia = f"{dt_ini[2:4]}/{dt_ini[4:8]}"
            break

    return competencia, empresa


def _build_maps(lines: List[str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Constrói:
      - mapa de participantes (0150): COD_PART -> NOME
      - mapa de itens (0200): COD_ITEM -> NCM
    """
    map_part_nome: Dict[str, str] = {}
    map_coditem_ncm: Dict[str, str] = {}

    for line in lines:
        p = line.strip().split("|")
        if len(p) < 3:
            continue
        reg = p[1]

        if reg == "0150":
            cod = _get(p, 2)
            nome = _get(p, 3)
            if cod:
                map_part_nome[cod] = nome

        elif reg == "0200":
            cod_item = _get(p, 2)
            ncm = _get(p, 8)
            if cod_item:
                map_coditem_ncm[cod_item] = ncm

    return map_part_nome, map_coditem_ncm


# =========================
# Parser principal
# =========================


M200_HEADERS = [
    "Valor Total da Contribuição Não-cumulativa do Período",
    "Valor do Crédito Descontado, Apurado no Próprio Período da Escrituração",
    "Valor do Crédito Descontado, Apurado em Período de Apuração Anterior",
    "Valor Total da Contribuição Não Cumulativa Devida",
    "Valor Retido na Fonte Deduzido no Período (Não Cumulativo)",
    "Outras Deduções do Regime Não Cumulativo no Período",
    "Valor da Contribuição Não Cumulativa a Recolher/Pagar",
    "Valor Total da Contribuição Cumulativa do Período",
    "Valor Retido na Fonte Deduzido no Período (Cumulativo)",
    "Outras Deduções do Regime Cumulativo no Período",
    "Valor da Contribuição Cumulativa a Recolher/Pagar",
    "Valor Total da Contribuição a Recolher/Pagar no Período",
]


def parse_efd_piscofins(
    lines: List[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]:
    """
    Faz o parsing das principais estruturas da EFD PIS/COFINS.

    Retorna:
      - df_c100: NF-e de entrada (C100/C170) com créditos de PIS/COFINS
      - df_outros: Serviços, energia, fretes, demais docs
      - df_ap_pis: Apuração PIS (M200)
      - df_cred_pis: Créditos PIS (M105)
      - competencia (MM/AAAA)
      - empresa (razão social)
    """
    competencia, empresa = _extract_metadata_0000(lines)
    map_part_nome, map_coditem_ncm = _build_maps(lines)

    records_c100: List[Dict] = []
    records_out: List[Dict] = []
    records_ap_pis: List[Dict] = []
    records_cred_pis: List[Dict] = []

    current_c100 = None  # última C100 lida
    current_a100 = None  # última A100 lida

    # Energia elétrica (C500/C501/C505)
    current_c500 = None
    c500_pis_bc = c500_pis_aliq = c500_pis_val = ""
    c500_cof_bc = c500_cof_aliq = c500_cof_val = ""

    def finalize_c500():
        nonlocal current_c500, c500_pis_bc, c500_pis_aliq, c500_pis_val
        nonlocal c500_cof_bc, c500_cof_aliq, c500_cof_val

        if not current_c500:
            return

        vl_pis = _to_float(c500_pis_val)
        vl_cof = _to_float(c500_cof_val)
        vl_bc_pis = _to_float(c500_pis_bc)
        vl_bc_cof = _to_float(c500_cof_bc)

        if vl_pis == 0 and vl_cof == 0 and vl_bc_pis == 0 and vl_bc_cof == 0:
            current_c500 = None
            c500_pis_bc = c500_pis_aliq = c500_pis_val = ""
            c500_cof_bc = c500_cof_aliq = c500_cof_val = ""
            return

        p = current_c500
        cod_part = _get(p, 3)
        cnpj_cpf = _get(p, 4)
        uf = _get(p, 5)
        num_doc = _get(p, 8)
        dt_doc = _get(p, 9)

        records_out.append(
            {
                "COMPETENCIA": competencia,
                "EMPRESA": empresa,
                "TIPO": "C500/C501/C505",
                "DOC": num_doc,
                "DT_DOC": dt_doc,
                "COD_PART": cod_part,
                "NOME_PART": map_part_nome.get(cod_part, ""),
                "CNPJ_CPF": cnpj_cpf,
                "UF": uf,
                "VL_BC_PIS": c500_pis_bc,
                "ALIQ_PIS": c500_pis_aliq,
                "VL_PIS": c500_pis_val,
                "VL_BC_COFINS": c500_cof_bc,
                "ALIQ_COFINS": c500_cof_aliq,
                "VL_COFINS": c500_cof_val,
            }
        )

        current_c500 = None
        c500_pis_bc = c500_pis_aliq = c500_pis_val = ""
        c500_cof_bc = c500_cof_aliq = c500_cof_val = ""

    # Loop principal
    for line in lines:
        p = line.strip().split("|")
        if len(p) < 3:
            continue
        reg = p[1]

        # ------------ C100 / C170 (NF-e entradas) ------------
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

            # C170
            num_item = _get(p, 2)
            cod_item = _get(p, 3)
            descr_item = _get(p, 4)
            cfop = _get(p, 11)

            # CST / bases / alíquotas / valores - PIS
            cst_pis = _get(p, 25)
            vl_bc_pis = _get(p, 26)
            aliq_pis = _get(p, 27)
            vl_pis = _get(p, 30)

            # CST / bases / alíquotas / valores - COFINS
            cst_cof = _get(p, 31)
            vl_bc_cof = _get(p, 32)
            aliq_cof = _get(p, 33)
            vl_cof = _get(p, 36)

            # só mantém linhas com base ou valor > 0
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

        # ------------ A100 / A170 (serviços tomados) ------------
        if reg == "A100":
            current_a100 = p
            continue

        if reg == "A170" and current_a100:
            cod_part = _get(current_a100, 4)
            num_doc = _get(current_a100, 8)
            dt_doc = _get(current_a100, 9)
            vl_doc = _get(current_a100, 11)

            cfop = _get(p, 4)
            cst_pis = _get(p, 7)
            vl_bc_pis = _get(p, 8)
            aliq_pis = _get(p, 9)
            vl_pis = _get(p, 12)

            cst_cof = _get(p, 13)
            vl_bc_cof = _get(p, 14)
            aliq_cof = _get(p, 15)
            vl_cof = _get(p, 18)

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

        # ------------ C500 / C501 / C505 (energia elétrica) ------------
        if reg == "C500":
            # fecha o C500 anterior, se houver
            finalize_c500()
            current_c500 = p
            continue

        if reg == "C501":
            c500_pis_bc = _get(p, 3)
            c500_pis_aliq = _get(p, 6)
            c500_pis_val = _get(p, 7)
            continue

        if reg == "C505":
            c500_cof_bc = _get(p, 3)
            c500_cof_aliq = _get(p, 6)
            c500_cof_val = _get(p, 7)
            continue

        # ------------ D100 / D101 / D105 (CT-e / fretes) ------------
        if reg == "D100":
            current_d100 = p  # definido dinâmico
            continue

        if reg == "D101":
            try:
                d100 = current_d100  # type: ignore[name-defined]
            except NameError:
                continue

            cod_part = _get(d100, 4)
            num_doc = _get(d100, 8)
            dt_doc = _get(d100, 10)
            vl_doc = _get(d100, 12)

            cst_pis = _get(p, 3)
            vl_bc_pis = _get(p, 4)
            aliq_pis = _get(p, 5)
            vl_pis = _get(p, 8)

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
                    "CST_PIS": cst_pis,
                    "VL_BC_PIS": vl_bc_pis,
                    "ALIQ_PIS": aliq_pis,
                    "VL_PIS": vl_pis,
                    "CST_COFINS": "",
                    "VL_BC_COFINS": "",
                    "ALIQ_COFINS": "",
                    "VL_COFINS": "",
                }
            )
            continue

        if reg == "D105":
            try:
                d100 = current_d100  # type: ignore[name-defined]
            except NameError:
                continue

            cod_part = _get(d100, 4)
            num_doc = _get(d100, 8)
            dt_doc = _get(d100, 10)
            vl_doc = _get(d100, 12)

            cst_cof = _get(p, 3)
            vl_bc_cof = _get(p, 4)
            aliq_cof = _get(p, 5)
            vl_cof = _get(p, 8)

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
                    "CST_PIS": "",
                    "VL_BC_PIS": "",
                    "ALIQ_PIS": "",
                    "VL_PIS": "",
                    "CST_COFINS": cst_cof,
                    "VL_BC_COFINS": vl_bc_cof,
                    "ALIQ_COFINS": aliq_cof,
                    "VL_COFINS": vl_cof,
                }
            )
            continue

        # ------------ F100 / F120 (demais documentos) ------------
        if reg == "F100":
            current_f100 = p  # type: ignore[assignment]
            continue

        if reg == "F120":
            try:
                f100 = current_f100  # type: ignore[name-defined]
            except NameError:
                continue

            cod_part = _get(f100, 3)
            num_doc = _get(f100, 5)
            dt_doc = _get(f100, 6)
            vl_doc = _get(f100, 7)

            cst_pis = _get(p, 9)
            vl_bc_pis = _get(p, 10)
            aliq_pis = _get(p, 11)
            vl_pis = _get(p, 14)

            cst_cof = _get(p, 15)
            vl_bc_cof = _get(p, 16)
            aliq_cof = _get(p, 17)
            vl_cof = _get(p, 20)

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

        # ------------ Bloco M – AP PIS (M200) e Créditos PIS (M105) ------------
        if reg == "M200":
            row = {
                "COMPETENCIA": competencia,
                "EMPRESA": empresa,
            }
            vals = p[2 : 2 + len(M200_HEADERS)]
            for titulo, val in zip(M200_HEADERS, vals):
                row[titulo] = _to_float(val)
            records_ap_pis.append(row)
            continue

        if reg == "M105":
            nat = _get(p, 2)
            row = {
                "COMPETENCIA": competencia,
                "EMPRESA": empresa,
                "NAT_BC_CRED": nat,
                "CST_PIS": _get(p, 3),
                "VL_BC": _to_float(_get(p, 4)),
                "ALIQ": _to_float(_get(p, 5)),
                "VL_CRED": _to_float(_get(p, 6)),
            }
            records_cred_pis.append(row)
            continue

    # Finaliza último C500
    finalize_c500()

    df_c100 = pd.DataFrame(records_c100)
    df_outros = pd.DataFrame(records_out)
    df_ap_pis = pd.DataFrame(records_ap_pis)
    df_cred_pis = pd.DataFrame(records_cred_pis)

    return df_c100, df_outros, df_ap_pis, df_cred_pis, competencia, empresa
