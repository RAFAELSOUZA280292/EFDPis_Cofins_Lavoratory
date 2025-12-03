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
    for line in lines:
        if line.startswith("|0000|"):
            parts = line.split("|")
            competencia = _get(parts, 7)  # DT_FIN (DDMMAAAA)
            empresa = _get(parts, 9)  # NOME_EMP
            return f"{competencia[2:4]}/{competencia[4:8]}", empresa
    return "N/A", "N/A"


def _extract_metadata_0200(lines: List[str]) -> Dict[str, str]:
    """
    Extrai:
      - mapa de itens (0200): COD_ITEM -> NCM
    """
    map_coditem_ncm = {}
    for line in lines:
        if line.startswith("|0200|"):
            parts = line.split("|")
            cod_item = _get(parts, 2)
            ncm = _get(parts, 8)
            if cod_item and ncm:
                map_coditem_ncm[cod_item] = ncm
    return map_coditem_ncm


def _extract_metadata_0150(lines: List[str]) -> Dict[str, str]:
    """
    Extrai:
      - mapa de participantes (0150): COD_PART -> NOME
    """
    map_part_nome = {}
    for line in lines:
        if line.startswith("|0150|"):
            parts = line.split("|")
            cod_part = _get(parts, 2)
            nome = _get(parts, 3)
            if cod_part and nome:
                map_part_nome[cod_part] = nome
    return map_part_nome


# =========================
# Parser principal
# =========================


def parse_efd_piscofins(
    lines: List[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]:
    """
    Recebe as linhas do SPED e retorna DataFrames com os dados de crédito.
    """
    competencia, empresa = _extract_metadata_0000(lines)
    map_coditem_ncm = _extract_metadata_0200(lines)
    map_part_nome = _extract_metadata_0150(lines)

    records_c100 = []  # NF-e de entrada (C100/C170)
    records_out = []  # Outros documentos (A100/A170, C500/C501/C505, D100/D101/D105, F100/F120)
    records_ap_pis = []  # M200
    records_cred_pis = []  # M105

    # Variáveis de estado para registros pais
    current_c100 = None  # última C100 lida
    current_a100 = None  # última A100 lida
    current_c500 = None  # última C500 lida
    current_d100 = None  # última D100 lida
    current_f100 = None  # última F100 lida

    # Headers para M200 (simplificado)
    M200_HEADERS = [
        "VL_TOT_CONT_PER",
        "VL_TOT_CRED_DESC",
        "VL_TOT_CRED_DESC_ANT",
        "VL_TOT_CRED_DESC_PER",
        "VL_TOT_CRED_DESC_FUT",
        "VL_TOT_CRED_DESC_COFINS",
        "VL_TOT_CRED_DESC_COFINS_ANT",
        "VL_TOT_CRED_DESC_COFINS_PER",
        "VL_TOT_CRED_DESC_COFINS_FUT",
    ]

    def finalize_c500():
        """Função auxiliar para finalizar o bloco C500/C501/C505."""
        nonlocal current_c500
        if current_c500 and len(current_c500) > 22:
            # Se for C500 (pai), adiciona o registro principal
            if _get(current_c500, 1) == "C500":
                # Campos C500:
                # 19: VL_BC_PIS, 20: VL_PIS, 21: VL_BC_COFINS, 22: VL_COFINS
                vl_bc_pis = _get(current_c500, 19)
                vl_pis = _get(current_c500, 20)
                vl_bc_cof = _get(current_c500, 21)
                vl_cof = _get(current_c500, 22)

                if _to_float(vl_pis) > 0.0 or _to_float(vl_cof) > 0.0:
                    records_out.append(
                        {
                            "COMPETENCIA": competencia,
                            "EMPRESA": empresa,
                            "TIPO": "C500/C501/C505",
                            "DOC": _get(current_c500, 13),  # NUM_DOC
                            "DT_DOC": _get(current_c500, 14),  # DT_DOC
                            "VL_BC_PIS": vl_bc_pis,
                            "VL_PIS": vl_pis,
                            "VL_BC_COFINS": vl_bc_cof,
                            "VL_COFINS": vl_cof,
                        }
                    )
            current_c500 = None

    for line in lines:
        p = line.split("|")
        reg = _get(p, 1)

        # Finaliza blocos anteriores
        if reg.startswith("C") and reg != "C500" and reg != "C501" and reg != "C505":
            finalize_c500()

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
            chv_nfe = _get(current_c100, 10) # CHV_NFE (Campo 10 do C100)

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

            # só mantém linhas com crédito real (PIS ou COFINS > 0)
            if (
                _to_float(vl_pis) == 0.0
                and _to_float(vl_cof) == 0.0
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
                    "CHV_NFE": chv_nfe,
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
            # A100 - Campos corretos (contando de 0):
            # 4: NUM_DOC, 10: DT_EMISSAO
            # 16: VL_BC_PIS, 17: VL_PIS, 18: VL_BC_COFINS, 19: VL_COFINS (geralmente 0)
            
            num_doc = _get(current_a100, 4)
            dt_doc = _get(current_a100, 10)
            
            # Extração dos campos principais (PIS/COFINS) do A100
            vl_bc_pis = _get(current_a100, 16)
            vl_pis = _get(current_a100, 17)
            vl_bc_cof = _get(current_a100, 18)
            vl_cof = _get(current_a100, 19)
            
            # Se COFINS estiver vazio ou zero, extrai do A170
            # A170 - Campos: [14]: VL_BC_COFINS, [15]: VL_COFINS (alíquota), [16]: VL_COFINS (valor)
            if _to_float(vl_cof) == 0.0 and len(p) > 16:
                vl_bc_cof = _get(p, 14)
                vl_cof = _get(p, 16)  # Campo correto do COFINS

            if _to_float(vl_pis) > 0.0 or _to_float(vl_cof) > 0.0:
                records_out.append(
                    {
                        "COMPETENCIA": competencia,
                        "EMPRESA": empresa,
                        "TIPO": "A100/A170",
                        "DOC": num_doc,
                        "DT_DOC": dt_doc,
                        "VL_BC_PIS": vl_bc_pis,
                        "VL_PIS": vl_pis,
                        "VL_BC_COFINS": vl_bc_cof,
                        "VL_COFINS": vl_cof,
                    }
                )
            current_a100 = None
            continue

        # ------------ C500 / C501 / C505 (Energia/Comunicação) ------------
        if reg == "C500":
            current_c500 = p
            continue

        if reg == "C501" or reg == "C505":
            # C501/C505 são registros filhos, o crédito está no C500 (pai)
            # Apenas marca que foi processado, sem duplicar dados
            if current_c500 is None:
                continue
            continue

        # ------------ D100 / D101 / D105 (Fretes) ------------
        if reg == "D100":
            current_d100 = p
            current_d101 = None  # Acumula PIS
            current_d105 = None  # Acumula COFINS
            continue

        if reg == "D101":
            if current_d100 is None:
                continue
            current_d101 = p
            continue

        if reg == "D105":
            if current_d100 is None:
                continue
            current_d105 = p
            
            # Quando encontra D105, consolida D101 + D105
            num_doc = _get(current_d100, 12)
            dt_doc = _get(current_d100, 13)
            
            # D101: [6]: Base, [7]: PIS, [8]: (?)
            # D105: [6]: Base, [7]: (alíquota?), [8]: COFINS
            vl_bc_pis = _get(current_d101, 6) if current_d101 else _get(p, 6)
            vl_pis = _get(current_d101, 7) if current_d101 else "0"
            vl_bc_cof = _get(p, 6)
            vl_cof = _get(p, 8)

            if _to_float(vl_pis) > 0.0 or _to_float(vl_cof) > 0.0:
                records_out.append(
                    {
                        "COMPETENCIA": competencia,
                        "EMPRESA": empresa,
                        "TIPO": "D100/D105",
                        "DOC": num_doc,
                        "DT_DOC": dt_doc,
                        "VL_BC_PIS": vl_bc_pis,
                        "VL_PIS": vl_pis,
                        "VL_BC_COFINS": vl_bc_cof,
                        "VL_COFINS": vl_cof,
                    }
                )
            continue

        # ------------ F100 / F120 (Outros) ------------
        if reg == "F100":
            current_f100 = p
            continue

        if reg == "F120":
            if current_f100 is None:
                continue
            
            # F100: 10: NUM_DOC, 11: DT_DOC
            num_doc = _get(current_f100, 10)
            dt_doc = _get(current_f100, 11)
            
            # F100 (baseado no exemplo do usuário):
            # 8: VL_BC_PIS, 10: VL_PIS, 12: VL_BC_COFINS, 14: VL_COFINS
            
            # Se for F100, usa os campos do F100 (pai)
            if _get(current_f100, 1) == "F100":
                vl_bc_pis = _get(current_f100, 8)
                vl_pis = _get(current_f100, 10)
                vl_bc_cof = _get(current_f100, 12)
                vl_cof = _get(current_f100, 14)
            else:
                # Se for F120, usa os campos do F120 (filho)
                # F120: 4: VL_BC_PIS, 5: VL_PIS, 7: VL_BC_COFINS, 8: VL_COFINS
                vl_bc_pis = _get(p, 4)
                vl_pis = _get(p, 5)
                vl_bc_cof = _get(p, 7)
                vl_cof = _get(p, 8)

            if _to_float(vl_pis) > 0.0 or _to_float(vl_cof) > 0.0:
                records_out.append(
                    {
                        "COMPETENCIA": competencia,
                        "EMPRESA": empresa,
                        "TIPO": "F100/F120",
                        "DOC": num_doc,
                        "DT_DOC": dt_doc,
                        "VL_BC_PIS": vl_bc_pis,
                        "VL_PIS": vl_pis,
                        "VL_BC_COFINS": vl_bc_cof,
                        "VL_COFINS": vl_cof,
                    }
                )
            current_f100 = None
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
