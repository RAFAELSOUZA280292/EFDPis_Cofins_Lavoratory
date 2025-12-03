import zipfile
import io
import pandas as pd

# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------

def _to_str(val):
    if val is None:
        return ""
    return str(val).strip()

def _to_float(val):
    try:
        val = str(val).strip().replace(".", "").replace(",", ".")
        return float(val)
    except:
        return 0.0

def _decode_bytes(b):
    try:
        return b.decode("utf-8")
    except:
        return b.decode("latin-1")


def _extract_txt_from_zip(uploaded_file):
    txt_lines = []
    with zipfile.ZipFile(uploaded_file) as zf:
        for name in zf.namelist():
            if name.lower().endswith(".txt"):
                txt = zf.read(name)
                decoded = _decode_bytes(txt)
                lines = decoded.splitlines()
                txt_lines.extend(lines)
    return txt_lines


def load_efd_from_upload(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".zip"):
        return _extract_txt_from_zip(uploaded_file)
    elif name.endswith(".txt"):
        content = uploaded_file.read()
        decoded = _decode_bytes(content)
        return decoded.splitlines()
    else:
        raise ValueError("Formato inválido. Envie .txt ou .zip contendo .txt")


# -----------------------------------------------------------
# Metadata extractors
# -----------------------------------------------------------

def _extract_metadata_0000(lines):
    """
    Retorna (competencia, empresa)
    """
    competencia = "00/0000"
    empresa = ""
    for line in lines:
        p = line.split("|")
        if len(p) > 9 and p[1] == "0000":
            dt_ini = p[6]  # ddmmaaaa
            if len(dt_ini) == 8:
                competencia = dt_ini[2:4] + "/" + dt_ini[4:]
            empresa = p[7]
            break
    return competencia, empresa

def _build_maps(lines):
    """
    Cria mapas:
    0150 - participantes
    0200 - itens (NCM)
    """
    map_part = {}
    map_item_ncm = {}

    for l in lines:
        p = l.split("|")
        if len(p) < 3:
            continue

        reg = p[1]

        # Registro 0150 - Participante
        if reg == "0150":
            cod = p[2]
            nome = p[3] if len(p) > 3 else ""
            map_part[cod] = nome

        # Registro 0200 - Itens
        if reg == "0200":
            cod_item = p[2]
            ncm = p[7] if len(p) > 7 else ""
            map_item_ncm[cod_item] = ncm

    return map_part, map_item_ncm


# ===========================================================
# PARSER PRINCIPAL
# ===========================================================

def parse_efd_piscofins(lines):
    competencia, empresa = _extract_metadata_0000(lines)
    map_part_nome, map_item_ncm = _build_maps(lines)

    records_c100 = []
    records_out = []
    records_ap_pis = []
    records_cred_pis = []

    current_c100 = None
    current_a100 = None
    current_c500 = None
    current_d100 = None
    current_f100 = None

    # Acumuladores energia elétrica
    c500_bc_pis = 0.0
    c500_aliq_pis = 0.0
    c500_vl_pis = 0.0

    c500_bc_cof = 0.0
    c500_aliq_cof = 0.0
    c500_vl_cof = 0.0

    def finalize_c500():
        nonlocal c500_bc_pis, c500_aliq_pis, c500_vl_pis
        nonlocal c500_bc_cof, c500_aliq_cof, c500_vl_cof
        nonlocal current_c500

        if current_c500 is None:
            return

        if (
            c500_bc_pis == 0
            and c500_vl_pis == 0
            and c500_bc_cof == 0
            and c500_vl_cof == 0
        ):
            current_c500 = None
            c500_bc_pis = c500_aliq_pis = c500_vl_pis = 0.0
            c500_bc_cof = c500_aliq_cof = c500_vl_cof = 0.0
            return

        p = current_c500
        cod_part = p[4]
        num_doc = p[8]
        dt_doc = p[9]
        vl_doc = p[11]

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
                "VL_BC_PIS": c500_bc_pis,
                "ALIQ_PIS": c500_aliq_pis,
                "VL_PIS": c500_vl_pis,
                "CST_COFINS": "",
                "VL_BC_COFINS": c500_bc_cof,
                "ALIQ_COFINS": c500_aliq_cof,
                "VL_COFINS": c500_vl_cof,
            }
        )

        current_c500 = None
        c500_bc_pis = c500_aliq_pis = c500_vl_pis = 0.0
        c500_bc_cof = c500_aliq_cof = c500_vl_cof = 0.0


    # Loop principal
    for line in lines:
        p = line.split("|")
        if len(p) < 2:
            continue

        reg = p[1]

        # ------------------------ C100 ------------------------
        if reg == "C100":
            current_c100 = p
            continue

        # ------------------------ C170 ------------------------
        if reg == "C170" and current_c100:
            ind_oper = current_c100[4]  # 0 = entrada
            if ind_oper != "0":
                continue

            cod_part = current_c100[3]
            modelo = current_c100[5]
            sit = current_c100[6]
            num_doc = current_c100[8]
            dt_doc = current_c100[9]
            dt_entr = current_c100[10]
            vl_doc = current_c100[11]

            num_item = p[2]
            cod_item = p[3]
            descr_item = p[4]
            cfop = p[11]

            # PIS campos
            cst_pis = p[12]
            vl_bc_pis = p[13]
            aliq_pis = p[14]
            vl_pis = p[15]

            # COFINS campos
            cst_cof = p[18]
            vl_bc_cof = p[19]
            aliq_cof = p[20]
            vl_cof = p[21]

            if (
                _to_float(vl_bc_pis) == 0
                and _to_float(vl_pis) == 0
                and _to_float(vl_bc_cof) == 0
                and _to_float(vl_cof) == 0
            ):
                continue

            records_c100.append(
                {
                    "COMPETENCIA": competencia,
                    "EMPRESA": empresa,
                    "DOC": num_doc,
                    "DT_DOC": dt_doc,
                    "DT_ENTR": dt_entr,
                    "COD_PART": cod_part,
                    "NOME_PART": map_part_nome.get(cod_part, ""),
                    "MODELO": modelo,
                    "SIT": sit,
                    "COD_ITEM": cod_item,
                    "NCM": map_item_ncm.get(cod_item, ""),
                    "DESCR_ITEM": descr_item,
                    "CFOP": cfop,
                    "NUM_ITEM": num_item,
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

        # ------------------------ A100 ------------------------
        if reg == "A100":
            current_a100 = p
            continue

        # ------------------------ A170 (CORRIGIDO) ------------------------
        if reg == "A170" and current_a100:
            cod_part = current_a100[4]
            num_doc = current_a100[8]
            dt_doc = current_a100[9]
            vl_doc = current_a100[11]

            # Layout oficial A170
            cst_pis = p[9]
            vl_bc_pis = p[10]
            aliq_pis = p[11]
            vl_pis = p[12]

            cst_cof = p[13]
            vl_bc_cof = p[14]
            aliq_cof = p[15]
            vl_cof = p[16]

            if (
                _to_float(vl_bc_pis) == 0
                and _to_float(vl_pis) == 0
                and _to_float(vl_bc_cof) == 0
                and _to_float(vl_cof) == 0
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
                    "CFOP": "",
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

        # ------------------------ C500 ------------------------
        if reg == "C500":
            finalize_c500()
            current_c500 = p
            continue

        # ------------------------ C501 (PIS energia) ------------------------
        if reg == "C501":
            c500_bc_pis += _to_float(p[7])
            c500_aliq_pis = _to_float(p[8])
            c500_vl_pis += _to_float(p[9])
            continue

        # ------------------------ C505 (COFINS energia) ------------------------
        if reg == "C505":
            c500_bc_cof += _to_float(p[7])
            c500_aliq_cof = _to_float(p[8])
            c500_vl_cof += _to_float(p[9])
            continue

        # ------------------------ D100 ------------------------
        if reg == "D100":
            current_d100 = p
            continue

        # ------------------------ D101 (PIS frete) ------------------------
        if reg == "D101" and current_d100:
            cod_part = current_d100[4]
            num_doc = current_d100[7]
            dt_doc = current_d100[8]
            vl_doc = current_d100[9]

            cst_pis = p[2]
            vl_bc_pis = p[3]
            aliq_pis = p[4]
            vl_pis = p[5]

            if _to_float(vl_pis) == 0 and _to_float(vl_bc_pis) == 0:
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
                    "VL_BC_COFINS": 0,
                    "ALIQ_COFINS": 0,
                    "VL_COFINS": 0,
                }
            )
            continue

        # ------------------------ D105 (COFINS frete) ------------------------
        if reg == "D105" and current_d100:
            cod_part = current_d100[4]
            num_doc = current_d100[7]
            dt_doc = current_d100[8]
            vl_doc = current_d100[9]

            cst_cof = p[2]
            vl_bc_cof = p[3]
            aliq_cof = p[4]
            vl_cof = p[5]

            if _to_float(vl_cof) == 0 and _to_float(vl_bc_cof) == 0:
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
                    "VL_BC_PIS": 0,
                    "ALIQ_PIS": 0,
                    "VL_PIS": 0,
                    "CST_COFINS": cst_cof,
                    "VL_BC_COFINS": vl_bc_cof,
                    "ALIQ_COFINS": aliq_cof,
                    "VL_COFINS": vl_cof,
                }
            )
            continue

        # ------------------------ F100 ------------------------
        if reg == "F100":
            current_f100 = p
            continue

        # ------------------------ F120 (CORRIGIDO) ------------------------
        if reg == "F120" and current_f100:
            cod_part = current_f100[3]
            num_doc = current_f100[5]
            dt_doc = current_f100[6]
            vl_doc = current_f100[7]

            cst_pis = p[8]
            vl_bc_pis = p[9]
            aliq_pis = p[10]
            vl_pis = p[11]

            cst_cof = p[12]
            vl_bc_cof = p[13]
            aliq_cof = p[14]
            vl_cof = p[15]

            if (
                _to_float(vl_bc_pis) == 0
                and _to_float(vl_pis) == 0
                and _to_float(vl_bc_cof) == 0
                and _to_float(vl_cof) == 0
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
                    "CFOP": "",
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

        # ------------------------ M200 ------------------------
        if reg == "M200":
            M200_HEADERS = [
                "REG", "VL_TOT_CONT_NC_PER", "VL_CONT_NC_REC",
                "VL_TOT_CRED_DESC", "VL_TOT_CONT_REAL",
                "VL_CONT_NC_REST", "VL_CONT_NC_RET",
                "VL_CONT_NC_SUSP", "VL_CONT_NC_ADIC"
            ]
            row = {}
            for i, col in enumerate(M200_HEADERS):
                if i < len(p):
                    row[col] = _to_float(p[i])
                else:
                    row[col] = 0.0
            row["COMPETENCIA"] = competencia
            row["EMPRESA"] = empresa
            records_ap_pis.append(row)
            continue

        # ------------------------ M105 ------------------------
        if reg == "M105":
            nat = p[2]
            cst = p[3]
            vl_bc = p[4]
            aliq = p[5]
            vl_cred = p[6]

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

    finalize_c500()

    df_c100 = pd.DataFrame(records_c100)
    df_outros = pd.DataFrame(records_out)
    df_ap_pis = pd.DataFrame(records_ap_pis)
    df_cred_pis = pd.DataFrame(records_cred_pis)

    return df_c100, df_outros, df_ap_pis, df_cred_pis, competencia, empresa
