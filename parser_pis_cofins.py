# parser_pis_cofins.py

import io
import zipfile
from typing import Tuple, List, Dict

import pandas as pd


def _to_str(s) -> str:
    return "" if s is None else str(s)


def _to_float(s) -> float:
    s = _to_str(s).strip()
    if not s:
        return 0.0
    # Trata decimal com vírgula e ponto
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _get(parts: List[str], idx: int) -> str:
    return parts[idx] if len(parts) > idx else ""


def _decode_bytes(file_bytes: bytes) -> str:
    """
    Tenta decodificar bytes do arquivo em texto.
    Prioriza latin-1 (muito comum em SPED), depois utf-8.
    """
    for enc in ("latin-1", "utf-8-sig", "utf-8"):
        try:
            return file_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    # fallback bruto
    return file_bytes.decode("latin-1", errors="ignore")


def _extract_txt_from_zip(uploaded_bytes: bytes) -> bytes:
    """
    Recebe os bytes de um .zip e retorna o conteúdo do primeiro .txt encontrado.
    """
    with zipfile.ZipFile(io.BytesIO(uploaded_bytes), "r") as zf:
        txt_names = [n for n in zf.namelist() if n.lower().endswith(".txt")]
        if not txt_names:
            raise ValueError("Nenhum arquivo .txt encontrado dentro do .zip.")
        with zf.open(txt_names[0]) as f:
            return f.read()


def load_efd_from_upload(uploaded_file) -> List[str]:
    """
    Recebe o arquivo enviado pelo Streamlit (st.file_uploader) e devolve a lista de linhas.
    Aceita .txt ou .zip (com 1 .txt dentro).
    """
    raw = uploaded_file.read()
    name = uploaded_file.name.lower()

    if name.endswith(".zip"):
        raw_txt = _extract_txt_from_zip(raw)
    elif name.endswith(".txt"):
        raw_txt = raw
    else:
        raise ValueError("Formato de arquivo não suportado. Envie .txt ou .zip.")

    text = _decode_bytes(raw_txt)
    lines = text.splitlines()
    return lines


def _extract_metadata_0000(lines: List[str]) -> Dict[str, str]:
    """
    Lê o registro 0000 para extrair:
      - competência (MM/AAAA, ex.: 07/2025)
      - empresa (razão social)
    """
    competencia = ""
    empresa = ""

    for line in lines:
        p = line.strip().split("|")
        if len(p) > 1 and p[1] == "0000":
            # Exemplo:
            # |0000|006|0|||01072025|31072025|EMPRESA ...|
            dt_ini = _get(p, 6)
            empresa = _get(p, 8)
            if len(dt_ini) == 8:
                mes = dt_ini[2:4]
                ano = dt_ini[4:]
                competencia = f"{mes}/{ano}"
            break

    return {"competencia": competencia, "empresa": empresa}


def parse_efd_piscofins(lines: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame, str, str]:
    """
    Faz o parser do EFD PIS/COFINS e devolve:
      - df_c100: itens de NF-e de entrada com crédito (C100/C170)
      - df_outros: demais documentos com crédito (A100/A170, C500/C501/C505, D100/D101/D105, F100/F120)
      - competencia: string "MM/AAAA"
      - empresa: razão social do contribuinte
    """

    # ---------- Metadados (0000) ----------
    meta = _extract_metadata_0000(lines)
    competencia = meta.get("competencia", "")
    empresa = meta.get("empresa", "")

    # ---------- Mapas auxiliares: participantes e itens ----------
    map_part_nome: Dict[str, str] = {}
    map_coditem_ncm: Dict[str, str] = {}

    for line in lines:
        p = line.strip().split("|")
        if len(p) <= 1:
            continue
        reg = p[1]

        # 0150 - Participantes
        if reg == "0150":
            cod = _get(p, 2)
            nome = _get(p, 3)
            if cod:
                map_part_nome[cod] = nome

        # 0200 - Itens
        if reg == "0200":
            cod_item = _get(p, 2)
            ncm = _get(p, 8)
            if cod_item:
                map_coditem_ncm[cod_item] = ncm

    # ---------- C100 / C170 - NF-e de entrada ----------
    records_c100: List[dict] = []
    current_c100 = None
    current_ind_oper = None

    for line in lines:
        p = line.strip().split("|")
        if len(p) <= 1:
            continue
        reg = p[1]

        if reg == "C100":
            current_c100 = p
            current_ind_oper = _get(p, 2)  # 0 = entrada, 1 = saída
            continue

        if reg == "C170" and current_c100 is not None and current_ind_oper == "0":
            c100 = current_c100
            c170 = p

            ind_oper = _get(c100, 2)
            ind_emit = _get(c100, 3)
            cod_part = _get(c100, 4)
            cod_mod = _get(c100, 5)
            cod_sit = _get(c100, 6)
            serie = _get(c100, 7)
            num_doc = _get(c100, 8)
            chv_nfe = _get(c100, 9)
            dt_doc = _get(c100, 10)
            dt_es = _get(c100, 11)
            vl_doc = _get(c100, 12)
            vl_merc = _get(c100, 16)
            vl_pis_doc = _get(c100, 26)
            vl_cofins_doc = _get(c100, 27)

            num_item = _get(c170, 2)
            cod_item = _get(c170, 3)
            descr_compl = _get(c170, 4)
            qtd = _get(c170, 5)
            unid = _get(c170, 6)
            vl_item = _get(c170, 7)
            cfop = _get(c170, 11)

            cst_pis = _get(c170, 25)
            vl_bc_pis = _get(c170, 26)
            aliq_pis = _get(c170, 27)
            vl_pis = _get(c170, 30)

            cst_cofins = _get(c170, 31)
            vl_bc_cofins = _get(c170, 32)
            aliq_cofins = _get(c170, 33)
            vl_cofins = _get(c170, 36)

            # somente itens com base ou crédito > 0
            if (
                _to_float(vl_pis) == 0.0
                and _to_float(vl_cofins) == 0.0
                and _to_float(vl_bc_pis) == 0.0
                and _to_float(vl_bc_cofins) == 0.0
            ):
                continue

            ncm = map_coditem_ncm.get(cod_item, "")
            fornecedor = map_part_nome.get(cod_part, "")

            records_c100.append(
                {
                    "COMPETENCIA": competencia,
                    "EMPRESA": empresa,
                    "TIPO_REG": "C100/C170",
                    "IND_OPER": ind_oper,
                    "IND_EMIT": ind_emit,
                    "COD_PART": cod_part,
                    "FORNECEDOR": fornecedor,
                    "COD_MOD": cod_mod,
                    "COD_SIT": cod_sit,
                    "SERIE": serie,
                    "NUM_DOC": num_doc,
                    "CHV_NFE": chv_nfe,
                    "DT_DOC": dt_doc,
                    "DT_E_S": dt_es,
                    "VL_DOC": vl_doc,
                    "VL_MERC": vl_merc,
                    "VL_PIS_DOC": vl_pis_doc,
                    "VL_COFINS_DOC": vl_cofins_doc,
                    "NUM_ITEM": num_item,
                    "COD_ITEM": cod_item,
                    "NCM": ncm,
                    "DESCR_COMPL": descr_compl,
                    "QTD": qtd,
                    "UNID": unid,
                    "VL_ITEM": vl_item,
                    "CFOP": cfop,
                    "CST_PIS": cst_pis,
                    "VL_BC_PIS": vl_bc_pis,
                    "ALIQ_PIS": aliq_pis,
                    "VL_PIS": vl_pis,
                    "CST_COFINS": cst_cofins,
                    "VL_BC_COFINS": vl_bc_cofins,
                    "ALIQ_COFINS": aliq_cofins,
                    "VL_COFINS": vl_cofins,
                }
            )

    df_c100 = pd.DataFrame(records_c100)

    # ---------- OUTROS DOCUMENTOS (A100, C500/C501/C505, D100, F100) ----------
    records_out: List[dict] = []
    currentA100 = None
    currentC500 = None
    currentD100 = None
    currentF100 = None

    # acumuladores para C500 (energia)
    c500_pis_bc = ""
    c500_pis_aliq = ""
    c500_pis_val = ""
    c500_cof_bc = ""
    c500_cof_aliq = ""
    c500_cof_val = ""

    def finalize_c500():
        nonlocal currentC500, c500_pis_bc, c500_pis_aliq, c500_pis_val, c500_cof_bc, c500_cof_aliq, c500_cof_val
        if currentC500 is None:
            return

        # Só grava se houver PIS ou COFINS
        if (
            _to_float(c500_pis_val) == 0.0
            and _to_float(c500_cof_val) == 0.0
            and _to_float(c500_pis_bc) == 0.0
            and _to_float(c500_cof_bc) == 0.0
        ):
            return

        cod_part = _get(currentC500, 2)
        num_doc = _get(currentC500, 7)
        dt_doc = _get(currentC500, 8)
        vl_doc = _get(currentC500, 10)

        records_out.append(
            {
                "COMPETENCIA": competencia,
                "EMPRESA": empresa,
                "TIPO": "C500/C501/C505",
                "COD_PART": cod_part,
                "FORNECEDOR": map_part_nome.get(cod_part, ""),
                "NUM_DOC": num_doc,
                "DT_DOC": dt_doc,
                "VL_DOC": vl_doc,
                "COD_ITEM": "",
                "VL_BC_PIS": c500_pis_bc,
                "ALIQ_PIS": c500_pis_aliq,
                "VL_PIS": c500_pis_val,
                "VL_BC_COFINS": c500_cof_bc,
                "ALIQ_COFINS": c500_cof_aliq,
                "VL_COFINS": c500_cof_val,
            }
        )

    for line in lines:
        p = line.strip().split("|")
        if len(p) <= 1:
            continue
        reg = p[1]

        # ===== A100 / A170 - Serviços tomados =====
        if reg == "A100":
            currentA100 = p

        elif reg == "A170" and currentA100 is not None:
            cod_part = _get(currentA100, 4)
            num_doc = _get(currentA100, 8)
            dt_doc = _get(currentA100, 10)
            vl_doc = _get(currentA100, 12)
            cod_item = _get(p, 3)

            # layout deduzido:
            # 10:VL_BC_PIS, 11:ALIQ_PIS, 12:VL_PIS
            # 14:VL_BC_COF, 15:ALIQ_COF, 16:VL_COF
            vl_bc_pis = _get(p, 10)
            aliq_pis = _get(p, 11)
            vl_pis = _get(p, 12)
            vl_bc_cof = _get(p, 14)
            aliq_cof = _get(p, 15)
            vl_cof = _get(p, 16)

            if _to_float(vl_pis) > 0.0 or _to_float(vl_cof) > 0.0:
                records_out.append(
                    {
                        "COMPETENCIA": competencia,
                        "EMPRESA": empresa,
                        "TIPO": "A100/A170",
                        "COD_PART": cod_part,
                        "FORNECEDOR": map_part_nome.get(cod_part, ""),
                        "NUM_DOC": num_doc,
                        "DT_DOC": dt_doc,
                        "VL_DOC": vl_doc,
                        "COD_ITEM": cod_item,
                        "VL_BC_PIS": vl_bc_pis,
                        "ALIQ_PIS": aliq_pis,
                        "VL_PIS": vl_pis,
                        "VL_BC_COFINS": vl_bc_cof,
                        "ALIQ_COFINS": aliq_cof,
                        "VL_COFINS": vl_cof,
                    }
                )

        # ===== C500 / C501 / C505 - Energia elétrica =====
        if reg == "C500":
            # Finaliza o C500 anterior (se houver)
            finalize_c500()
            currentC500 = p
            # zera acumuladores
            c500_pis_bc = ""
            c500_pis_aliq = ""
            c500_pis_val = ""
            c500_cof_bc = ""
            c500_cof_aliq = ""
            c500_cof_val = ""

        elif reg == "C501" and currentC500 is not None:
            # PIS da energia
            # Exemplo:
            # |C501|50|9020,15|04|9020,15|1,65|148,83|4.8.01.002.011|
            c500_pis_bc = _get(p, 3)     # VL_BC_PIS
            c500_pis_aliq = _get(p, 6)   # ALIQ_PIS
            c500_pis_val = _get(p, 7)    # VL_PIS

        elif reg == "C505" and currentC500 is not None:
            # COFINS da energia
            # Exemplo:
            # |C505|50|9020,15|04|9020,15|7,6|685,53|4.8.01.002.011|
            c500_cof_bc = _get(p, 3)     # VL_BC_COFINS
            c500_cof_aliq = _get(p, 6)   # ALIQ_COFINS
            c500_cof_val = _get(p, 7)    # VL_COFINS

        # ===== D100 / D101 / D105 - CT-e (fretes) =====
        if reg == "D100":
            currentD100 = p

        elif reg == "D101" and currentD100 is not None:
            cod_part = _get(currentD100, 4)
            num_doc = _get(currentD100, 9)
            dt_doc = _get(currentD100, 11)
            vl_doc = _get(currentD100, 13)

            # 6:VL_BC_PIS, 7:ALIQ_PIS, 8:VL_PIS
            vl_bc_pis = _get(p, 6)
            aliq_pis = _get(p, 7)
            vl_pis = _get(p, 8)

            if _to_float(vl_pis) > 0.0:
                records_out.append(
                    {
                        "COMPETENCIA": competencia,
                        "EMPRESA": empresa,
                        "TIPO": "D100/D101",
                        "COD_PART": cod_part,
                        "FORNECEDOR": map_part_nome.get(cod_part, ""),
                        "NUM_DOC": num_doc,
                        "DT_DOC": dt_doc,
                        "VL_DOC": vl_doc,
                        "COD_ITEM": "",
                        "VL_BC_PIS": vl_bc_pis,
                        "ALIQ_PIS": aliq_pis,
                        "VL_PIS": vl_pis,
                        "VL_BC_COFINS": "",
                        "ALIQ_COFINS": "",
                        "VL_COFINS": "",
                    }
                )

        elif reg == "D105" and currentD100 is not None:
            cod_part = _get(currentD100, 4)
            num_doc = _get(currentD100, 9)
            dt_doc = _get(currentD100, 11)
            vl_doc = _get(currentD100, 13)

            # 6:VL_BC_COF, 7:ALIQ_COF, 8:VL_COF
            vl_bc_cof = _get(p, 6)
            aliq_cof = _get(p, 7)
            vl_cof = _get(p, 8)

            if _to_float(vl_cof) > 0.0:
                records_out.append(
                    {
                        "COMPETENCIA": competencia,
                        "EMPRESA": empresa,
                        "TIPO": "D100/D105",
                        "COD_PART": cod_part,
                        "FORNECEDOR": map_part_nome.get(cod_part, ""),
                        "NUM_DOC": num_doc,
                        "DT_DOC": dt_doc,
                        "VL_DOC": vl_doc,
                        "COD_ITEM": "",
                        "VL_BC_PIS": "",
                        "ALIQ_PIS": "",
                        "VL_PIS": "",
                        "VL_BC_COFINS": vl_bc_cof,
                        "ALIQ_COFINS": aliq_cof,
                        "VL_COFINS": vl_cof,
                    }
                )

        # ===== F100 / F120 - Outros créditos =====
        if reg == "F100":
            currentF100 = p

        elif reg == "F120" and currentF100 is not None:
            cod_part = _get(currentF100, 3)
            num_doc = ""  # F100 não traz número de NF clássico
            dt_doc = _get(currentF100, 5)
            vl_doc = _get(currentF100, 6)

            # layout deduzido:
            # 9:VL_BC_PIS, 10:ALIQ_PIS, 11:VL_PIS
            # 13:VL_BC_COF, 14:ALIQ_COF, 15:VL_COF
            vl_bc_pis = _get(p, 9)
            aliq_pis = _get(p, 10)
            vl_pis = _get(p, 11)
            vl_bc_cof = _get(p, 13)
            aliq_cof = _get(p, 14)
            vl_cof = _get(p, 15)

            if _to_float(vl_pis) > 0.0 or _to_float(vl_cof) > 0.0:
                records_out.append(
                    {
                        "COMPETENCIA": competencia,
                        "EMPRESA": empresa,
                        "TIPO": "F100/F120",
                        "COD_PART": cod_part,
                        "FORNECEDOR": map_part_nome.get(cod_part, ""),
                        "NUM_DOC": num_doc,
                        "DT_DOC": dt_doc,
                        "VL_DOC": vl_doc,
                        "COD_ITEM": "",
                        "VL_BC_PIS": vl_bc_pis,
                        "ALIQ_PIS": aliq_pis,
                        "VL_PIS": vl_pis,
                        "VL_BC_COFINS": vl_bc_cof,
                        "ALIQ_COFINS": aliq_cof,
                        "VL_COFINS": vl_cof,
                    }
                )

    # Finaliza o último C500 do arquivo (se tiver)
    finalize_c500()

    df_outros = pd.DataFrame(records_out)

    return df_c100, df_outros, competencia, empresa
