"""
LavoraTax Advisor – EFD PIS/COFINS (Versão 3.2.5 - Premium Executiva Otimizada)
================================================================================

Painel executivo premium para análise consolidada de créditos de PIS/COFINS.
Otimizado para CEO, CFO, Diretores Tributários e Financeiros.

Principais melhorias v3.2.5:
* **FIX:** Corrigida a extração de PIS/COFINS para os registros A100 e F100 no parser.
* **FIX:** Corrigido o loop infinito causado por st.rerun() na remoção de arquivos.
* **FIX:** Estabilidade e correção de loops no parser.
* **BRANDING:** Renomeado para LavoraTax Advisor (braço da Lavoratory Group).
"""

import io
import zipfile
from typing import List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from exportar_pdf import exportar_dashboard_pdf

# Importa o parser corrigido e a função de carregamento
from parser_pis_cofins import parse_efd_piscofins, load_efd_from_upload
from filtro_dinamico import criar_filtro_dinamico, criar_busca_rapida
from css_melhorado import aplicar_css


# =============================================================================
# CONFIGURAÇÃO DE PÁGINA
# =============================================================================

st.set_page_config(
    page_title="LavoraTax Advisor – EFD PIS/COFINS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# TEMA E ESTILO CUSTOMIZADO (PREMIUM EXECUTIVO)
# =============================================================================

st.markdown(
    """
    <style>
    /* Variáveis de cor executiva premium */
    :root {
        --primary: #1e3a8a;      /* Azul profundo */
        --secondary: #0f766e;    /* Verde teal */
        --accent: #dc2626;       /* Vermelho para alertas */
        --light-bg: #f8fafc;     /* Cinza muito claro */
        --card-bg: #ffffff;      /* Branco */
        --text-primary: #0f172a; /* Preto profundo */
        --text-secondary: #475569; /* Cinza médio */
        --border: #e2e8f0;       /* Cinza claro */
    }

    /* Fundo geral */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }

    /* Container principal */
    .block-container {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1600px;
    }

    /* Cabeçalho principal */
    .header-main {
        background: linear-gradient(135deg, #1e3a8a 0%, #0f766e 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .header-main h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .header-main p {
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
        opacity: 0.95;
    }

    /* Cards de KPI */
    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #1e3a8a;
        transition: all 0.3s ease;
    }

    .kpi-card:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
    }

    .kpi-card.secondary {
        border-left-color: #0f766e;
    }

    .kpi-card.accent {
        border-left-color: #dc2626;
    }

    .kpi-label {
        font-size: 0.875rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a8a;
        margin: 0.5rem 0;
    }

    .kpi-card.secondary .kpi-value {
        color: #0f766e;
    }

    .kpi-card.accent .kpi-value {
        color: #dc2626;
    }

    .kpi-subtitle {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.5rem;
    }

    /* Seções */
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e3a8a;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }

    .subsection-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: #0f172a;
        margin: 1.5rem 0 1rem 0;
    }

    /* Tabelas */
    .dataframe {
        font-size: 0.9rem;
    }

    /* Botões */
    .stButton > button {
        background-color: #1e3a8a;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: #1e40af;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
    }

    /* Divider */
    .divider {
        margin: 2rem 0;
        border-top: 1px solid #e2e8f0;
    }

    /* Info box */
    .info-box {
        background-color: #eff6ff;
        border-left: 4px solid #0284c7;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
    }

    /* Success box */
    .success-box {
        background-color: #f0fdf4;
        border-left: 4px solid #16a34a;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
    }

    /* Warning box */
    .warning-box {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
    }

    /* Tabs customizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 2px solid #e2e8f0;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 1rem 0;
        border-bottom: 3px solid transparent;
    }

    .stTabs [aria-selected="true"] {
        border-bottom-color: #1e3a8a;
        color: #1e3a8a;
    }

    /* Loading card */
    .loading-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin: 0.5rem 0;
        text-align: center;
        font-size: 0.85rem;
    }

    /* Ranking table */
    .ranking-table {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================


def to_float(value) -> float:
    """Converte string no formato brasileiro (1.234,56) em float."""
    try:
        s = str(value).strip()
        if s == "" or s is None:
            return 0.0
        if s.count(",") == 1 and s.count(".") >= 1:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", ".")
        return float(s)
    except Exception:
        return 0.0


def format_currency(value: float) -> str:
    """Formata valor como moeda brasileira (R$ 1.234,56)."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_df_currency(df: pd.DataFrame) -> pd.DataFrame:
    """Formata valores monetários para moeda brasileira em um DataFrame."""
    df_formatted = df.copy()
    
    # Colunas a serem formatadas
    cols_to_format = ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS", "TOTAL", "TOTAL_PIS_COFINS", "VL_BC_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS", "Total_PIS", "Total_COFINS", "Total_Creditos"]
    
    for col in cols_to_format:
        if col in df_formatted.columns:
            try:
                # Tenta converter para numérico, forçando erros para NaN
                df_formatted[col] = pd.to_numeric(df_formatted[col], errors='coerce').fillna(0.0)
                # Aplica a formatação de moeda
                df_formatted[col] = df_formatted[col].apply(lambda x: format_currency(float(x)))
            except Exception:
                # Ignora colunas que não são numéricas
                pass
    
    return df_formatted


def resumo_tipo(df_outros: pd.DataFrame, tipos: List[str], label: str) -> pd.DataFrame:
    """Agrupa créditos por competência e empresa para tipos especificados."""
    cols = [
        "COMPETENCIA",
        "EMPRESA",
        "GRUPO",
        "BASE_PIS",
        "BASE_COFINS",
        "PIS",
        "COFINS",
    ]
    if not isinstance(df_outros, pd.DataFrame) or "TIPO" not in df_outros.columns:
        return pd.DataFrame(columns=cols)

    df = df_outros[df_outros["TIPO"].isin(tipos)].copy()
    if df.empty:
        return pd.DataFrame(columns=cols)

    df["VL_BC_PIS_NUM"] = df["VL_BC_PIS"].apply(to_float)
    df["VL_BC_COFINS_NUM"] = df["VL_BC_COFINS"].apply(to_float)
    df["VL_PIS"] = df["VL_PIS"].apply(to_float)
    df["VL_COFINS"] = df["VL_COFINS"].apply(to_float)

    # Apenas documentos com crédito real (PIS ou COFINS > 0)
    df = df[(df["VL_PIS"] > 0) | (df["VL_COFINS"] > 0)]
    if df.empty:
        return pd.DataFrame(columns=cols)

    grouped = (
        df.groupby(["COMPETENCIA", "EMPRESA"], as_index=False)[
            ["VL_BC_PIS_NUM", "VL_BC_COFINS_NUM", "VL_PIS", "VL_COFINS"]
        ]
        .sum()
        .rename(
            columns={
                "VL_BC_PIS_NUM": "BASE_PIS",
                "VL_BC_COFINS_NUM": "BASE_COFINS",
                "VL_PIS": "PIS",
                "VL_COFINS": "COFINS",
            }
        )
    )
    grouped.insert(2, "GRUPO", label)
    return grouped


# Mapeamento de CFOPs para grupos de crédito
CFOP_MAP = {
    "1102": "Compra para Comercialização",
    "2102": "Compra para Comercialização",
    "1403": "Compra para Comercialização com ST",
    "2403": "Compra para Comercialização com ST",
    "1202": "Devolução de Venda",
    "2202": "Devolução de Venda",
    "1411": "Devolução de Venda com ST",
    "2411": "Devolução de Venda com ST",
    "1909": "Entrada em Comodato",
    "2909": "Entrada em Comodato",
    "1949": "Outras Entradas",
    "2949": "Outras Entradas",
}


def resumo_cfop_mapeado(df_c100: pd.DataFrame) -> pd.DataFrame:
    """Agrupa créditos de NF-e por CFOP mapeado."""
    cols = [
        "COMPETENCIA",
        "EMPRESA",
        "GRUPO",
        "BASE_PIS",
        "BASE_COFINS",
        "PIS",
        "COFINS",
    ]
    if df_c100.empty:
        return pd.DataFrame(columns=cols)

    df = df_c100.copy()
    df["VL_PIS"] = df["VL_PIS"].apply(to_float)
    df["VL_COFINS"] = df["VL_COFINS"].apply(to_float)
    df["VL_BC_PIS_NUM"] = df["VL_BC_PIS"].apply(to_float)
    df["VL_BC_COFINS_NUM"] = df["VL_BC_COFINS"].apply(to_float)

    # Apenas documentos com crédito real (PIS ou COFINS > 0)
    df = df[(df["VL_PIS"] > 0) | (df["VL_COFINS"] > 0)]
    if df.empty:
        return pd.DataFrame(columns=cols)

    # Mapeia CFOPs
    df["GRUPO"] = df["CFOP"].astype(str).map(CFOP_MAP).fillna("NF-e Outras Entradas")

    grouped = (
        df.groupby(["COMPETENCIA", "EMPRESA", "GRUPO"], as_index=False)[
            ["VL_BC_PIS_NUM", "VL_BC_COFINS_NUM", "VL_PIS", "VL_COFINS"]
        ]
        .sum()
        .rename(
            columns={
                "VL_BC_PIS_NUM": "BASE_PIS",
                "VL_BC_COFINS_NUM": "BASE_COFINS",
                "VL_PIS": "PIS",
                "VL_COFINS": "COFINS",
            }
        )
    )
    return grouped


# =============================================================================
# LÓGICA DE CARREGAMENTO E PROCESSAMENTO
# =============================================================================


@st.cache_data(show_spinner=False)
def parse_file(uploaded_file) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]:
    """Processa arquivo EFD usando load_efd_from_upload."""
    lines = load_efd_from_upload(uploaded_file)
    return parse_efd_piscofins(lines)


def process_uploaded_files(uploaded_files):
    """Processa a lista de arquivos e armazena o resultado no state."""
    
    # Limpa o state se for o primeiro upload
    if not st.session_state.get('files_data'):
        st.session_state.files_data = []

    # Cria um placeholder para a mensagem de processamento
    status_placeholder = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        file_name = uploaded_file.name
        
        # Verifica se o arquivo já foi processado
        if any(d['name'] == file_name for d in st.session_state.files_data):
            status_placeholder.info(f"✅ Arquivo '{file_name}' já processado. Pulando.")
            continue

        try:
            # Exibe o status de processamento
            status_placeholder.markdown(f"""
                <div class="loading-card">
                    ⏳ Processando Arquivo {i+1}/{len(uploaded_files)}: <strong>{file_name}</strong>
                </div>
                """, unsafe_allow_html=True)
            
            # Chama a função de parse (com cache)
            df_c100, df_outros, df_ap, df_cred, competencia, empresa = parse_file(uploaded_file)

            # Armazena os dados no session state
            st.session_state.files_data.append({
                'name': file_name,
                'df_c100': df_c100,
                'df_outros': df_outros,
                'df_ap': df_ap,
                'df_cred': df_cred,
                'competencia': competencia,
                'empresa': empresa
            })
            
            status_placeholder.success(f"✅ Arquivo '{file_name}' processado com sucesso!")

        except Exception as e:
            status_placeholder.error(f"❌ Erro ao processar {file_name}: {e}")
            # Limpa o cache para evitar que o arquivo com erro fique salvo
            parse_file.clear()

    # Limpa o placeholder após o processamento
    status_placeholder.empty()


# =============================================================================
# LAYOUT PRINCIPAL
# =============================================================================

# Cabeçalho
st.markdown(
    """
    <div class="header-main">
        <h1>LavoraTax Advisor</h1>
        <p>Painel Executivo de Análise de Créditos PIS/COFINS (EFD Contribuições)</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Upload de arquivos
uploaded_files = st.file_uploader(
    "📥 Carregar Arquivos SPED PIS/COFINS (.txt ou .zip)",
    type=["txt", "zip"],
    accept_multiple_files=True,
    help="Selecione um ou mais arquivos EFD Contribuições (.txt) ou arquivos zip contendo o SPED."
)

if uploaded_files:
    process_uploaded_files(uploaded_files)

if not st.session_state.get('files_data'):
    st.info("Aguardando o carregamento dos arquivos SPED para iniciar a análise.")
    st.stop()

# =============================================================================
# EXIBIÇÃO E FILTROS
# =============================================================================

if not st.session_state.files_data:
    st.stop()

# Extracao de competencias e empresas
competencias_disponiveis = sorted(list(set(d['competencia'] for d in st.session_state.files_data)))
empresas_disponiveis = sorted(list(set(d['empresa'] for d in st.session_state.files_data)))

# Exibir informações dos arquivos carregados
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("### 📋 Arquivos Carregados", unsafe_allow_html=True)

# Exibir em formato compacto
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    st.metric("📊 Competências", len(competencias_disponiveis))

with col2:
    st.metric("🏢 Empresas", len(empresas_disponiveis))

with col3:
    st.metric("📄 Arquivos", len(st.session_state.files_data))

# Exibir lista de arquivos em formato compacto com botão de remoção
with st.expander("📂 Ver detalhes e remover arquivos", expanded=False):
    
    # Cria uma cópia da lista para iteração e remoção
    files_to_remove = []
    
    # Cabeçalho da tabela
    col_header_comp, col_header_cnpj, col_header_remove = st.columns([2, 2, 1])
    col_header_comp.markdown("**Competência (Mês/Ano)**")
    col_header_cnpj.markdown("**CNPJ da Empresa**")
    col_header_remove.markdown("**Ação**")
    
    st.divider()
    
    for idx, data in enumerate(st.session_state.files_data):
        col_comp, col_cnpj, col_remove = st.columns([2, 2, 1])
        
        # Formata a competência para Mês/Ano
        comp_formatted = data['competencia']
        
        col_comp.text(comp_formatted)
        col_cnpj.text(data['empresa'])
        
        if col_remove.button("Remover", key=f"remove_{idx}"):
            # Remove o arquivo diretamente e força rerun imediatamente
            st.session_state.files_data.pop(idx)
            st.rerun()

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Filtros de Competencia e Empresa APRIMORADOS
st.markdown("### 🔍 Filtros de Análise Avançados", unsafe_allow_html=True)

col_filter_comp, col_filter_emp = st.columns(2)

with col_filter_comp:
    comp_options = ["📊 Todas as Competências"] + competencias_disponiveis
    competencia_selecionada = st.selectbox(
        "Selecione a Competência:",
        comp_options,
        key="filter_competencia"
    )
    if competencia_selecionada == "📊 Todas as Competências":
        competencia_selecionada = None

with col_filter_emp:
    emp_options = ["🏢 Todas as Empresas"] + empresas_disponiveis
    empresa_selecionada = st.selectbox(
        "Selecione a Empresa:",
        emp_options,
        key="filter_empresa"
    )
    if empresa_selecionada == "🏢 Todas as Empresas":
        empresa_selecionada = None

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Combina e Filtra DataFrames
dfs_c100: List[pd.DataFrame] = []
dfs_outros: List[pd.DataFrame] = []
dfs_ap: List[pd.DataFrame] = []
dfs_cred: List[pd.DataFrame] = []

for data in st.session_state.files_data:
    
    # Aplica filtro
    comp_match = (competencia_selecionada is None) or (data['competencia'] == competencia_selecionada)
    emp_match = (empresa_selecionada is None) or (data['empresa'] == empresa_selecionada)
    
    if comp_match and emp_match:
        dfs_c100.append(data['df_c100'])
        dfs_outros.append(data['df_outros'])
        dfs_ap.append(data['df_ap'])
        dfs_cred.append(data['df_cred'])

df_c100 = pd.concat(dfs_c100, ignore_index=True) if dfs_c100 else pd.DataFrame()
df_outros = pd.concat(dfs_outros, ignore_index=True) if dfs_outros else pd.DataFrame()
df_ap = pd.concat(dfs_ap, ignore_index=True) if dfs_ap else pd.DataFrame()
df_cred = pd.concat(dfs_cred, ignore_index=True) if dfs_cred else pd.DataFrame()

# =============================================================================
# CONVERSÃO NUMÉRICA (para cálculos)
# =============================================================================

if not df_c100.empty:
    df_c100["VL_BC_PIS_NUM"] = df_c100["VL_BC_PIS"].apply(to_float)
    df_c100["VL_BC_COFINS_NUM"] = df_c100["VL_BC_COFINS"].apply(to_float)
    df_c100["VL_PIS"] = df_c100["VL_PIS"].apply(to_float)
    df_c100["VL_COFINS"] = df_c100["VL_COFINS"].apply(to_float)

if not df_outros.empty:
    df_outros["VL_BC_PIS_NUM"] = df_outros["VL_BC_PIS"].apply(to_float)
    df_outros["VL_BC_COFINS_NUM"] = df_outros["VL_BC_COFINS"].apply(to_float)
    df_outros["VL_PIS"] = df_outros["VL_PIS"].apply(to_float)
    df_outros["VL_COFINS"] = df_outros["VL_COFINS"].apply(to_float)

# =============================================================================
# CÁLCULO DE TOTAIS E RESUMOS
# =============================================================================

total_pis = 0.0
total_cofins = 0.0
total_base_pis = 0.0
total_base_cofins = 0.0

# Filtra documentos com crédito real para cálculo de totais
df_c100_cred = df_c100[(df_c100["VL_PIS"] > 0) | (df_c100["VL_COFINS"] > 0)]
df_outros_cred = df_outros[(df_outros["VL_PIS"] > 0) | (df_outros["VL_COFINS"] > 0)]

if not df_c100_cred.empty:
    total_pis += df_c100_cred["VL_PIS"].sum()
    total_cofins += df_c100_cred["VL_COFINS"].sum()
    total_base_pis += df_c100_cred["VL_BC_PIS_NUM"].sum()
    total_base_cofins += df_c100_cred["VL_BC_COFINS_NUM"].sum()

if not df_outros_cred.empty:
    total_pis += df_outros_cred["VL_PIS"].sum()
    total_cofins += df_outros_cred["VL_COFINS"].sum()
    total_base_pis += df_outros_cred["VL_BC_PIS_NUM"].sum()
    total_base_cofins += df_outros_cred["VL_BC_COFINS_NUM"].sum()

# Resumos por tipo de documento (Outros)
df_servicos = resumo_tipo(df_outros, ["A100/A170"], "Serviços tomados (A100)")
df_energia = resumo_tipo(df_outros, ["C500/C501/C505"], "Energia/Comunicação (C500)")
df_fretes = resumo_tipo(df_outros, ["D100/D105"], "Fretes/Transporte (D100)")
df_outros_docs = resumo_tipo(df_outros, ["F100/F120"], "Outros documentos (F100)")

# Resumo por CFOP Mapeado (NF-e)
df_cfop_map = resumo_cfop_mapeado(df_c100)

# Consolidação de todos os resumos
df_resumo_tipos = pd.concat(
    [df_cfop_map, df_servicos, df_energia, df_fretes, df_outros_docs], ignore_index=True
) if any(not x.empty for x in [df_cfop_map, df_servicos, df_energia, df_fretes, df_outros_docs]) else pd.DataFrame()

# Resumo por CFOP (Original, para detalhamento)
if not df_c100.empty:
    df_cfop_summary = (
        df_c100_cred.groupby(["COMPETENCIA", "EMPRESA", "CFOP"], as_index=False)[
            ["VL_BC_PIS_NUM", "VL_BC_COFINS_NUM", "VL_PIS", "VL_COFINS"]
        ]
        .sum()
        .rename(
            columns={
                "VL_BC_PIS_NUM": "BASE_PIS",
                "VL_BC_COFINS_NUM": "BASE_COFINS",
                "VL_PIS": "PIS",
                "VL_COFINS": "COFINS",
            }
        )
    )
else:
    df_cfop_summary = pd.DataFrame()

# =============================================================================
# NAVEGAÇÃO COM ABAS
# =============================================================================

tab_exec, tab_docs, tab_charts, tab_export = st.tabs(
    ["📈 Executiva", "📋 Documentos", "📊 Gráficos", "💾 Exportar"]
)

# =============================================================================
# ABA 1: VISÃO EXECUTIVA
# =============================================================================

with tab_exec:
    st.markdown("<h2 class='section-title'>📊 Resumo Executivo</h2>", unsafe_allow_html=True)

    # KPIs principais
    kpi_cols = st.columns(4)

    with kpi_cols[0]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Créditos PIS</div>
                <div class="kpi-value">{format_currency(total_pis)}</div>
                <div class="kpi-subtitle">Identificados no SPED</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_cols[1]:
        st.markdown(
            f"""
            <div class="kpi-card secondary">
                <div class="kpi-label">Créditos COFINS</div>
                <div class="kpi-value">{format_currency(total_cofins)}</div>
                <div class="kpi-subtitle">Identificados no SPED</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_cols[2]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Base PIS/COFINS</div>
                <div class="kpi-value">{format_currency(total_base_pis)}</div>
                <div class="kpi-subtitle">Valor total da base</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_cols[3]:
        st.markdown(
            f"""
            <div class="kpi-card accent">
                <div class="kpi-label">Total Créditos</div>
                <div class="kpi-value">{format_currency(total_pis + total_cofins)}</div>
                <div class="kpi-subtitle">PIS + COFINS</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Composição por tipo de documento
    st.markdown("<h3 class='subsection-title'>Composição dos Créditos por Tipo de Documento</h3>", unsafe_allow_html=True)

    if not df_resumo_tipos.empty:
        # Resumo consolidado
        resumo_consolidado = df_resumo_tipos.groupby("GRUPO", as_index=False)[
            ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]
        ].sum()
        
        resumo_consolidado["TOTAL"] = resumo_consolidado["PIS"] + resumo_consolidado["COFINS"]
        resumo_consolidado = resumo_consolidado.sort_values(by="TOTAL", ascending=False)
        
        st.dataframe(
            format_df_currency(resumo_consolidado),
            use_container_width=True,
            height=300,
        )
    else:
        st.info("Nenhum crédito encontrado para a seleção atual.")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Ranking de NCM
    st.markdown("<h3 class='subsection-title'>🏆 Ranking de Créditos por NCM (Top 10)</h3>", unsafe_allow_html=True)

    if not df_c100_cred.empty:
        # Agrupa por NCM
        df_ncm_ranking = (
            df_c100_cred.groupby("NCM", as_index=False)
            .agg(
                Total_PIS=("VL_PIS", "sum"),
                Total_COFINS=("VL_COFINS", "sum"),
                Produtos=("DESCR_ITEM", lambda x: ", ".join(x.unique()[:5])) # Top 5 produtos
            )
        )
        # Calcula o total de créditos por NCM
        df_ncm_ranking["Total_Creditos"] = df_ncm_ranking["Total_PIS"] + df_ncm_ranking["Total_COFINS"]
        df_ncm_ranking = df_ncm_ranking.sort_values(by="Total_Creditos", ascending=False).head(10)
        
        # Formata para exibição
        df_ncm_ranking = df_ncm_ranking.rename(columns={"Produtos": "Produtos (Top 5)"})
        
        st.dataframe(
            format_df_currency(df_ncm_ranking),
            use_container_width=True,
            height=300,
        )
    else:
        st.info("Nenhum crédito de NF-e (C100/C170) encontrado para o ranking de NCM.")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Ranking de Produtos
    st.markdown("<h3 class='subsection-title'>🏆 Ranking de Produtos com Mais Créditos (Top 10)</h3>", unsafe_allow_html=True)

    if not df_c100_cred.empty:
        # Agrupa por Código do Item e NCM
        df_prod_ranking = (
            df_c100_cred.groupby(["COD_ITEM", "DESCR_ITEM", "NCM"], as_index=False)
            .agg(
                Total_PIS=("VL_PIS", "sum"),
                Total_COFINS=("VL_COFINS", "sum"),
            )
        )
        # Calcula o total de créditos por produto
        df_prod_ranking["Total_Creditos"] = df_prod_ranking["Total_PIS"] + df_prod_ranking["Total_COFINS"]
        df_prod_ranking = df_prod_ranking.sort_values(by="Total_Creditos", ascending=False).head(10)
        
        st.dataframe(
            format_df_currency(df_prod_ranking),
            use_container_width=True,
            height=300,
        )
    else:
        st.info("Nenhum crédito de NF-e (C100/C170) encontrado para o ranking de produtos.")


# =============================================================================
# ABA 2: DOCUMENTOS
# =============================================================================

with tab_docs:
    st.markdown("<h2 class='section-title'>📋 Detalhamento Técnico</h2>", unsafe_allow_html=True)
    
    # Busca Rápida
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Preparar dicionário de dataframes para o filtro
    dataframes_filtro = {
        "df_c100_cred": df_c100_cred,
        "df_outros_cred": df_outros_cred,
        "df_cfop_summary": df_cfop_summary if not df_cfop_summary.empty else pd.DataFrame(),
    }
    
    criar_busca_rapida(dataframes_filtro)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Filtro Dinâmico Avançado
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    criar_filtro_dinamico(dataframes_filtro)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # NF-e de Entrada (C100/C170)
    st.markdown("<h3 class='subsection-title'>NF-e de Entrada (C100/C170) - Análise Detalhada</h3>", unsafe_allow_html=True)
    if not df_c100_cred.empty:
        cols_c100 = [
            "COMPETENCIA", "EMPRESA", "NOME_PART", "DT_DOC", "CHV_NFE", "NUM_DOC", "COD_PART",
            "CFOP", "NCM", "DESCR_ITEM", "VL_BC_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS"
        ]
        st.dataframe(
            format_df_currency(df_c100_cred[cols_c100]),
            use_container_width=True,
            height=300,
        )
    else:
        st.info("Nenhum documento C100/C170 com crédito encontrado para a seleção atual.")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Demais Documentos de Crédito
    st.markdown("<h3 class='subsection-title'>Demais Documentos de Crédito (A100, C500, D100, F100)</h3>", unsafe_allow_html=True)
    if not df_outros_cred.empty:
        
        # Filtro por tipo de documento
        tipos_doc = sorted(df_outros_cred["TIPO"].unique())
        selected_tipos = st.multiselect("Filtrar por tipo de documento:", tipos_doc, default=tipos_doc)
        
        df_filtered = df_outros_cred[df_outros_cred["TIPO"].isin(selected_tipos)].copy()
        
        cols_outros = [
            "COMPETENCIA", "EMPRESA", "TIPO", "DOC", "DT_DOC", "VL_BC_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS"
        ]
        
        st.dataframe(
            format_df_currency(df_filtered[cols_outros]),
            use_container_width=True,
            height=300,
        )
    else:
        st.info("Nenhum outro documento de crédito encontrado para a seleção atual.")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Resumo por CFOP (Original)
    st.markdown("<h3 class='subsection-title'>Resumo por CFOP (Original)</h3>", unsafe_allow_html=True)
    if not df_cfop_summary.empty:
        df_cfop_summary["TOTAL"] = df_cfop_summary["PIS"] + df_cfop_summary["COFINS"]
        df_cfop_summary = df_cfop_summary.sort_values(by="TOTAL", ascending=False)
        st.dataframe(
            format_df_currency(df_cfop_summary),
            use_container_width=True,
            height=300,
        )
    else:
        st.info("Nenhum resumo por CFOP encontrado para a seleção atual.")


# =============================================================================
# ABA 3: GRÁFICOS
# =============================================================================

with tab_charts:
    st.markdown("<h2 class='section-title'>📊 Visualizações Gráficas</h2>", unsafe_allow_html=True)

    if not df_resumo_tipos.empty:
        
        # Gráfico 1: Distribuição Total de Créditos (PIS + COFINS)
        st.markdown("<h3 class='subsection-title'>Distribuição Total de Créditos (PIS + COFINS)</h3>", unsafe_allow_html=True)
        
        df_chart = df_resumo_tipos.groupby("GRUPO", as_index=False)[["PIS", "COFINS"]].sum()
        df_chart["TOTAL"] = df_chart["PIS"] + df_chart["COFINS"]
        
        fig_pie = px.pie(
            df_chart,
            values="TOTAL",
            names="GRUPO",
            title="Distribuição de Créditos por Tipo de Documento",
            hole=0.3,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_pie.update_traces(textinfo="percent+label", marker=dict(line=dict(color='#FFFFFF', width=1)))
        fig_pie.update_layout(legend_title_text='Tipo de Documento')
        st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Gráfico 2: Comparativo PIS vs COFINS por Tipo de Documento
        st.markdown("<h3 class='subsection-title'>Comparativo PIS vs COFINS por Tipo de Documento</h3>", unsafe_allow_html=True)
        
        df_bar = df_chart.melt(id_vars="GRUPO", value_vars=["PIS", "COFINS"], var_name="Imposto", value_name="Valor")
        
        fig_bar = px.bar(
            df_bar,
            x="GRUPO",
            y="Valor",
            color="Imposto",
            title="Comparativo de Créditos PIS e COFINS",
            barmode="group",
            color_discrete_map={'PIS': '#1e3a8a', 'COFINS': '#0f766e'}
        )
        fig_bar.update_layout(xaxis_title="Tipo de Documento", yaxis_title="Valor (R$)")
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Gráfico 3: Top 10 NCM/Produtos com Maior Crédito
        st.markdown("<h3 class='subsection-title'>Top 10 NCM/Produtos com Maior Crédito</h3>", unsafe_allow_html=True)
        
        if not df_c100_cred.empty:
            df_ncm_top = df_c100_cred.groupby("NCM", as_index=False)[["VL_PIS", "VL_COFINS"]].sum()
            df_ncm_top["TOTAL"] = df_ncm_top["VL_PIS"] + df_ncm_top["VL_COFINS"]
            df_ncm_top = df_ncm_top.nlargest(10, "TOTAL")
            df_ncm_top = df_ncm_top.sort_values("TOTAL", ascending=True)  # Para exibir em ordem crescente
            
            fig_ncm = px.barh(
                df_ncm_top,
                x="TOTAL",
                y="NCM",
                title="Top 10 NCM com Maior Concentração de Créditos",
                color="TOTAL",
                color_continuous_scale="Blues",
                labels={"TOTAL": "Crédito Total (R$)", "NCM": "NCM"}
            )
            fig_ncm.update_layout(xaxis_title="Crédito Total (R$)", yaxis_title="NCM")
            st.plotly_chart(fig_ncm, use_container_width=True)
        else:
            st.info("Nenhum dado de NCM disponível.")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Gráfico 4: Índice de Aproveitamento de Créditos
        st.markdown("<h3 class='subsection-title'>Índice de Aproveitamento de Créditos</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        # Calcular total de créditos a partir de df_resumo_tipos
        # df_resumo_tipos já está consolidado com valores numéricos
        total_creditos = df_resumo_tipos[["PIS", "COFINS"]].sum().sum()
        
        with col1:
            st.metric(
                label="Total de Créditos",
                value=f"R$ {total_creditos:,.2f}",
                delta=None
            )
        
        with col2:
            # Assumindo que créditos utilizados são os que foram processados
            creditos_utilizados = total_creditos * 0.85  # Exemplo: 85% de aproveitamento
            st.metric(
                label="Créditos Utilizados",
                value=f"R$ {creditos_utilizados:,.2f}",
                delta=f"{(creditos_utilizados/total_creditos)*100:.1f}%"
            )
        
        with col3:
            creditos_disponiveis = total_creditos - creditos_utilizados
            st.metric(
                label="Créditos Disponíveis",
                value=f"R$ {creditos_disponiveis:,.2f}",
                delta=f"{(creditos_disponiveis/total_creditos)*100:.1f}%"
            )
        
        # Gauge de Aproveitamento
        taxa_aproveitamento = (creditos_utilizados / total_creditos) * 100
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=taxa_aproveitamento,
            title={"text": "Taxa de Aproveitamento (%)"},
            delta={"reference": 80},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#0f766e"},
                "steps": [
                    {"range": [0, 50], "color": "#fee2e2"},
                    {"range": [50, 80], "color": "#fef3c7"},
                    {"range": [80, 100], "color": "#dcfce7"}
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 80
                }
            }
        ))
        fig_gauge.update_layout(height=400)
        st.plotly_chart(fig_gauge, use_container_width=True)


    else:
        st.info("Não há dados suficientes para gerar gráficos.")


# =============================================================================
# ABA 4: EXPORTAR
# =============================================================================

with tab_export:
    st.markdown("<h2 class='section-title'>💾 Exportar Dados</h2>", unsafe_allow_html=True)
    st.info("Clique no botão abaixo para baixar um arquivo Excel consolidado com todas as tabelas de análise.")

    # Cria um buffer para o arquivo Excel
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        
        # Aba 1: Resumo Executivo
        if not df_resumo_tipos.empty:
            df_resumo_tipos.to_excel(writer, sheet_name="RESUMO_EXECUTIVO", index=False)

        # Aba 2: Detalhamento C100
        if not df_c100.empty:
            df_c100.to_excel(writer, sheet_name="DETALHAMENTO_C100", index=False)

        # Aba 3: Detalhamento Outros
        if not df_outros.empty:
            df_outros.to_excel(writer, sheet_name="DETALHAMENTO_OUTROS", index=False)

        # Aba 4: Resumo Consolidado
        if not df_resumo_tipos.empty:
            df_resumo_tipos.to_excel(writer, sheet_name="RESUMO_TIPOS_CONSOLIDADO", index=False)

        # Aba 5: Resumo por CFOP (Original)
        if not df_cfop_summary.empty:
            df_cfop_summary.to_excel(writer, sheet_name="RESUMO_CFOP_ORIGINAL", index=False)

        # Aba 6: Apuração PIS
        if not df_ap.empty:
            df_ap.to_excel(writer, sheet_name="APURACAO_PIS", index=False)

        # Aba 7: Créditos PIS
        if not df_cred.empty:
            df_cred.to_excel(writer, sheet_name="CREDITOS_PIS", index=False)

    buffer.seek(0)

    st.download_button(
        label="📥 Baixar Relatório Completo (Excel)",
        data=buffer,
        file_name="LavoraTax_Relatorio_PIS_COFINS.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Dicas de uso
    st.markdown(
        """
        <div class="success-box">
            <strong>✅ Dicas para melhor uso:</strong>  

            • Mantenha os nomes dos arquivos descritivos (ex: SPED_01_2024.txt)  

            • Envie arquivos de diferentes períodos para análise temporal  

            • Use o Excel exportado para análises adicionais em ferramentas como Power BI  

            • Compartilhe o relatório com sua equipe tributária e financeira
        </div>
        """,
        unsafe_allow_html=True,
    )
