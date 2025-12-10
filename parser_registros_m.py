"""
Parser SPED PIS/COFINS - Registros M (Apuração)
Processa registros: M200, M105, M210, M410, M600, M505, M610, M810
"""

import pandas as pd
import re
from pathlib import Path


# =========================
# Tabelas de Códigos
# =========================

# Cabeçalhos M200/M600 (conforme PVA)
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

M600_HEADERS = M200_HEADERS[:]  # mesma estrutura

# Tabela 4.3.5 – Código da Contribuição Social Apurada (COD_CONT)
COD_CONT_DESC = {
    "01": "Contribuição não-cumulativa apurada à alíquota básica",
    "02": "Contribuição não-cumulativa apurada à alíquota diferenciada/reduzida",
    "03": "Contribuição não-cumulativa – receitas com alíquota específica",
    "04": "Contribuição não-cumulativa – receitas sujeitas à alíquota zero",
    "05": "Contribuição não-cumulativa – receitas não alcançadas (isenção/suspensão)",
    "06": "Contribuição não-cumulativa – regime monofásico",
    "07": "Contribuição não-cumulativa – substituição tributária",
    "08": "Contribuição não-cumulativa – alíquota por unidade de medida",
    "09": "Contribuição não-cumulativa – outras hipóteses legais",
    "12": "Contribuição cumulativa – alíquota básica",
    "13": "Contribuição cumulativa – alíquota diferenciada",
    "14": "Contribuição cumulativa – alíquota zero",
    "15": "Contribuição cumulativa – outras hipóteses legais",
    "51": "Contribuição apurada – código 51 (ajuste conforme tabela interna/guia)",
}

# Natureza da receita / CODIGO_DET (M410/M810)
NAT_REC_DESC = {
    "309": "ZFM – Zona Franca de Manaus",
    "401": "Exportação de mercadorias para o exterior",
    "403": "Venda de óleo combustível, tipo bunker, MF – Marine Fuel (2710.19.22), óleo combustível, tipo bunker, MGO – Marine Gás Oil (2710.19.21) e óleo combustível, tipo bunker, ODM – Óleo Diesel Marítimo (2710.19.21), quando destinados à navegação de cabotagem e de apoio portuário e marítimo",
    "405": "Desperdícios, resíduos ou aparas de plástico, de papel ou cartão, de vidro, de ferro ou aço, de cobre, de níquel, de alumínio, de chumbo, de zinco e de estanho, e demais desperdícios e resíduos metálicos do Capítulo 81 da Tipi",
    "908": "Vendas de mercadorias destinadas ao consumo",
    "911": "Receitas financeiras, inclusive variação cambial ativa tributável",
    "999": "Código genérico – Operações tributáveis à alíquota zero/isenção/suspensão (especificar)",
}

# NAT_BC_CRED (M105/M505)
NAT_BC_CRED_DESC = {
    "01": "Aquisição de bens para revenda",
    "02": "Aquisição de bens e serviços utilizados como insumo",
    "03": "Energia elétrica e térmica, inclusive sob forma de vapor",
    "04": "Aluguéis de prédios",
    "05": "Aluguéis de máquinas e equipamentos",
    "06": "Armazenagem de mercadoria e frete na operação de venda",
    "07": "Contraprestações de arrendamento mercantil",
    "08": "Máquinas, equipamentos e outros bens incorporados ao ativo imobilizado (depreciação)",
    "09": "Edificações e benfeitorias em imóveis próprios ou de terceiros (depreciação/amortização)",
    "10": "Devolução de vendas sujeito à incidência não-cumulativa",
    "11": "Ativos intangíveis (amortização)",
    "12": "Encargos de depreciação, amortização e contraprestações de arrendamento no custo",
    "13": "Outras operações geradoras de crédito",
    "18": "Crédito presumido",
    "19": "Fretes na aquisição de insumos e bens para revenda",
    "20": "Armazenagem, seguros e vigilância na aquisição",
    "21": "Outros créditos vinculados à atividade",
}


# =========================
# Funções Auxiliares
# =========================

def only_digits(s: str) -> str:
    """Remove tudo exceto dígitos"""
    return re.sub(r"\D+", "", s or "")


def to_float_br(s) -> float:
    """Converte string brasileira para float"""
    if s is None:
        return 0.0
    s = str(s).strip()
    if s == "":
        return 0.0
    # Se tem vírgula e ponto: formato brasileiro (1.234,56)
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def competencia_from_dt(dt_ini: str, dt_fin: str) -> str:
    """Extrai competência MM/AAAA das datas"""
    for raw in (dt_ini or "", dt_fin or ""):
        dig = only_digits(raw)
        if len(dig) == 8:
            return f"{dig[2:4]}/{dig[4:8]}"
    return ""


def desc_cod_cont(codigo: str) -> str:
    """Retorna descrição do COD_CONT"""
    c = (codigo or "").strip()
    return COD_CONT_DESC.get(c, f"(Descrição não cadastrada: {c})")


def desc_nat_rec(codigo: str) -> str:
    """Retorna descrição do CODIGO_DET"""
    c = (codigo or "").strip()
    return NAT_REC_DESC.get(c, f"(Descrição não cadastrada: {c})")


def norm_nat_bc(codigo: str) -> str:
    """Normaliza NAT_BC_CRED para 2 dígitos"""
    d = only_digits((codigo or "").strip())
    if not d:
        return (codigo or "").strip()
    return d.zfill(2) if len(d) == 1 else d


def desc_nat_bc(codigo: str) -> str:
    """Retorna descrição do NAT_BC_CRED"""
    c = norm_nat_bc(codigo)
    return NAT_BC_CRED_DESC.get(c, f"(Descrição não cadastrada: {c})") if c else ""


# =========================
# Parser Principal
# =========================

def parse_sped_registros_m(conteudo: str, nome_arquivo: str = ""):
    """
    Parseia registros M do SPED PIS/COFINS
    
    Args:
        conteudo: Conteúdo do arquivo SPED
        nome_arquivo: Nome do arquivo (para referência)
        
    Returns:
        dict com 8 listas de registros + metadados
    """
    empresa_cnpj = ""
    dt_ini = ""
    dt_fin = ""
    competencia = ""
    
    ap_pis = []
    credito_pis = []
    receitas_pis = []
    rec_isentas_pis = []
    
    ap_cofins = []
    credito_cofins = []
    receitas_cofins = []
    rec_isentas_cofins = []
    
    linhas = conteudo.split('\n')
    
    for raw in linhas:
        if not raw or raw == "|":
            continue
            
        campos = raw.rstrip("\n").split("|")
        if len(campos) < 3:
            continue
            
        reg = (campos[1] or "").upper()
        
        # Registro 0000 - Extrai CNPJ e competência
        if reg == "0000":
            datas = [c for c in campos if re.fullmatch(r"\d{8}", c or "")]
            if len(datas) >= 2:
                dt_ini, dt_fin = datas[0], datas[1]
            else:
                dt_ini = campos[4] if len(campos) > 4 else ""
                dt_fin = campos[5] if len(campos) > 5 else ""
            competencia = competencia_from_dt(dt_ini, dt_fin)
            
            cand = [only_digits(c) for c in campos if len(only_digits(c)) == 14]
            if cand:
                empresa_cnpj = cand[0]
        
        # M200 - Apuração PIS
        elif reg == "M200":
            row = {
                "ARQUIVO": nome_arquivo,
                "COMPETENCIA": competencia,
                "CNPJ_ARQUIVO": empresa_cnpj
            }
            vals = campos[2:2+len(M200_HEADERS)]
            for titulo, val in zip(M200_HEADERS, vals):
                row[titulo] = to_float_br(val)
            ap_pis.append(row)
        
        # M105 - Crédito PIS
        elif reg == "M105":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            credito_pis.append({
                "ARQUIVO": nome_arquivo,
                "COMPETENCIA": competencia,
                "CNPJ_ARQUIVO": empresa_cnpj,
                "NAT_BC_CRED": nat,
                "NAT_BC_CRED_DESC": desc_nat_bc(nat),
                "CST_PIS": (campos[3] if len(campos) > 3 else "").strip(),
                "VL_BC": to_float_br(campos[4] if len(campos) > 4 else 0),
                "ALIQ": to_float_br(campos[5] if len(campos) > 5 else 0),
                "VL_CRED": to_float_br(campos[6] if len(campos) > 6 else 0),
            })
        
        # M210 - Receitas PIS
        elif reg == "M210":
            cod = (campos[2] if len(campos) > 2 else "").strip()
            receitas_pis.append({
                "ARQUIVO": nome_arquivo,
                "COMPETENCIA": competencia,
                "CNPJ_ARQUIVO": empresa_cnpj,
                "COD_CONT": cod,
                "DESCR_COD_CONT": desc_cod_cont(cod),
                "VL_REC_BRT": to_float_br(campos[3] if len(campos) > 3 else 0),
                "VL_BC_CONT": to_float_br(campos[4] if len(campos) > 4 else 0),
                "VL_BC_PIS": to_float_br(campos[7] if len(campos) > 7 else 0),
                "ALIQ_PIS": to_float_br(campos[8] if len(campos) > 8 else 0),
                "VL_CONT_APUR": to_float_br(campos[11] if len(campos) > 11 else 0),
                "VL_CONT_PER": to_float_br(campos[16] if len(campos) > 16 else 0),
            })
        
        # M410 - Receitas Isentas PIS
        elif reg == "M410":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            rec_isentas_pis.append({
                "ARQUIVO": nome_arquivo,
                "COMPETENCIA": competencia,
                "CNPJ_ARQUIVO": empresa_cnpj,
                "CODIGO_DET": nat,
                "DESCR_CODIGO_DET": desc_nat_rec(nat),
                "VL_REC": to_float_br(campos[3] if len(campos) > 3 else 0),
            })
        
        # M600 - Apuração COFINS
        elif reg == "M600":
            row = {
                "ARQUIVO": nome_arquivo,
                "COMPETENCIA": competencia,
                "CNPJ_ARQUIVO": empresa_cnpj
            }
            vals = campos[2:2+len(M600_HEADERS)]
            for titulo, val in zip(M600_HEADERS, vals):
                row[titulo] = to_float_br(val)
            ap_cofins.append(row)
        
        # M505 - Crédito COFINS
        elif reg == "M505":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            credito_cofins.append({
                "ARQUIVO": nome_arquivo,
                "COMPETENCIA": competencia,
                "CNPJ_ARQUIVO": empresa_cnpj,
                "NAT_BC_CRED": nat,
                "NAT_BC_CRED_DESC": desc_nat_bc(nat),
                "CST_COFINS": (campos[3] if len(campos) > 3 else "").strip(),
                "VL_BC": to_float_br(campos[4] if len(campos) > 4 else 0),
                "ALIQ": to_float_br(campos[5] if len(campos) > 5 else 0),
                "VL_CRED": to_float_br(campos[6] if len(campos) > 6 else 0),
            })
        
        # M610 - Receitas COFINS
        elif reg == "M610":
            cod = (campos[2] if len(campos) > 2 else "").strip()
            receitas_cofins.append({
                "ARQUIVO": nome_arquivo,
                "COMPETENCIA": competencia,
                "CNPJ_ARQUIVO": empresa_cnpj,
                "COD_CONT": cod,
                "DESCR_COD_CONT": desc_cod_cont(cod),
                "VL_REC_BRT": to_float_br(campos[3] if len(campos) > 3 else 0),
                "VL_BC_CONT": to_float_br(campos[4] if len(campos) > 4 else 0),
                "VL_BC_COFINS": to_float_br(campos[7] if len(campos) > 7 else 0),
                "ALIQ_COFINS": to_float_br(campos[8] if len(campos) > 8 else 0),
                "VL_CONT_APUR": to_float_br(campos[11] if len(campos) > 11 else 0),
                "VL_CONT_PER": to_float_br(campos[16] if len(campos) > 16 else 0),
            })
        
        # M810 - Receitas Isentas COFINS
        elif reg == "M810":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            rec_isentas_cofins.append({
                "ARQUIVO": nome_arquivo,
                "COMPETENCIA": competencia,
                "CNPJ_ARQUIVO": empresa_cnpj,
                "CODIGO_DET": nat,
                "DESCR_CODIGO_DET": desc_nat_rec(nat),
                "VL_REC": to_float_br(campos[3] if len(campos) > 3 else 0),
            })
    
    return {
        "ap_pis": ap_pis,
        "credito_pis": credito_pis,
        "receitas_pis": receitas_pis,
        "rec_isentas_pis": rec_isentas_pis,
        "ap_cofins": ap_cofins,
        "credito_cofins": credito_cofins,
        "receitas_cofins": receitas_cofins,
        "rec_isentas_cofins": rec_isentas_cofins,
        "competencia": competencia,
        "cnpj": empresa_cnpj
    }


def processar_multiplos_speds_m(arquivos_conteudo):
    """
    Processa múltiplos arquivos SPED
    
    Args:
        arquivos_conteudo: Lista de tuplas (nome_arquivo, conteudo)
        
    Returns:
        dict com DataFrames consolidados + índices
    """
    ap_pis_all = []
    cred_pis_all = []
    rec_pis_all = []
    rec_is_pis_all = []
    
    ap_cof_all = []
    cred_cof_all = []
    rec_cof_all = []
    rec_is_cof_all = []
    
    for nome_arquivo, conteudo in arquivos_conteudo:
        resultado = parse_sped_registros_m(conteudo, nome_arquivo)
        
        ap_pis_all.extend(resultado["ap_pis"])
        cred_pis_all.extend(resultado["credito_pis"])
        rec_pis_all.extend(resultado["receitas_pis"])
        rec_is_pis_all.extend(resultado["rec_isentas_pis"])
        
        ap_cof_all.extend(resultado["ap_cofins"])
        cred_cof_all.extend(resultado["credito_cofins"])
        rec_cof_all.extend(resultado["receitas_cofins"])
        rec_is_cof_all.extend(resultado["rec_isentas_cofins"])
    
    # Cria DataFrames
    df_ap_pis = pd.DataFrame(ap_pis_all)
    df_cred_pis = pd.DataFrame(cred_pis_all)
    df_rec_pis = pd.DataFrame(rec_pis_all)
    df_ri_pis = pd.DataFrame(rec_is_pis_all)
    
    df_ap_cof = pd.DataFrame(ap_cof_all)
    df_cred_cof = pd.DataFrame(cred_cof_all)
    df_rec_cof = pd.DataFrame(rec_cof_all)
    df_ri_cof = pd.DataFrame(rec_is_cof_all)
    
    # Cria índices de apoio
    df_idx_cod_cont = pd.DataFrame([
        {"COD_CONT": k, "DESCRICAO": v}
        for k, v in sorted(COD_CONT_DESC.items(), key=lambda x: x[0])
    ])
    
    df_idx_nat_rec = pd.DataFrame([
        {"CODIGO_DET": k, "DESCRICAO": v}
        for k, v in sorted(NAT_REC_DESC.items(), key=lambda x: x[0])
    ])
    
    df_idx_nat_bc = pd.DataFrame([
        {"NAT_BC_CRED": k, "DESCRICAO": v}
        for k, v in sorted(NAT_BC_CRED_DESC.items(), key=lambda x: x[0])
    ])
    
    return {
        "df_ap_pis": df_ap_pis,
        "df_cred_pis": df_cred_pis,
        "df_rec_pis": df_rec_pis,
        "df_ri_pis": df_ri_pis,
        "df_ap_cof": df_ap_cof,
        "df_cred_cof": df_cred_cof,
        "df_rec_cof": df_rec_cof,
        "df_ri_cof": df_ri_cof,
        "df_idx_cod_cont": df_idx_cod_cont,
        "df_idx_nat_rec": df_idx_nat_rec,
        "df_idx_nat_bc": df_idx_nat_bc
    }
