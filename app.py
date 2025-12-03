"""
LavoraTax Advisor – EFD PIS/COFINS (Versão 3.2.2 - Premium Executiva Otimizada)
================================================================================

Painel executivo premium para análise consolidada de créditos de PIS/COFINS.
Otimizado para CEO, CFO, Diretores Tributários e Financeiros.

Principais melhorias v3.2.2:
* **FIX:** Corrigido o erro de NameError ('_decode_bytes' is not defined) na função parse_file.
* **FIX:** Estabilidade e correção de loops no parser.
* **FIX:** Extração correta de dados de A100, C500, D100 e F100 no parser.
* **FIX:** Exibição da Chave de Acesso (CHV_NFE) na tabela C100/C170.
* **BRANDING:** Renomeado para LavoraTax Advisor (braço da Lavoratory Group).
"""

import io
import zipfile
from typing import List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Importa o parser corrigido e a função de carregamento
from parser_pis_cofins import parse_efd_piscofins, load_efd_from_upload


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
    cols_to_format = ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS", "TOTAL", "TOTAL_PIS_COFINS", "VL_BC_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS", "Total_PIS", "Total_COFINS", "Total_Creditos", "Valor"]
    
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
    df["VL_PIS_NUM"] = df["VL_PIS"].apply(to_float)
    df["VL_COFINS_NUM"] = df["VL_COFINS"].apply(to_float)

    # Apenas documentos com crédito real (PIS ou COFINS > 0)
    df = df[(df["VL_PIS_NUM"] > 0) | (df["VL_COFINS_NUM"] > 0)]
    if df.empty:
        return pd.DataFrame(columns=cols)

    grouped = (
        df.groupby(["COMPETENCIA", "EMPRESA"], as_index=False)[
            ["VL_BC_PIS_NUM", "VL_BC_COFINS_NUM", "VL_PIS_NUM", "VL_COFINS_NUM"]
        ]
        .sum()
        .rename(
            columns={
                "VL_BC_PIS_NUM": "BASE_PIS",
                "VL_BC_COFINS_NUM": "BASE_COFINS",
                "VL_PIS_NUM": "PIS",
                "VL_COFINS_NUM": "COFINS",
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
    "1909": "Entrada em Comodato",
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
    
    # Filtra apenas documentos com crédito real
    df = df[(df["VL_PIS_NUM"] > 0) | (df["VL_COFINS_NUM"] > 0)]
    if df.empty:
        return pd.DataFrame(columns=cols)

    # Mapeia CFOP
    df["GRUPO"] = df["CFOP"].astype(str).map(CFOP_MAP).fillna("Outras NF-e (C100)")

    grouped = (
        df.groupby(["COMPETENCIA", "EMPRESA", "GRUPO"], as_index=False)[
            ["VL_BC_PIS_NUM", "VL_BC_COFINS_NUM", "VL_PIS_NUM", "VL_COFINS_NUM"]
        ]
        .sum()
        .rename(
            columns={
                "VL_BC_PIS_NUM": "BASE_PIS",
                "VL_BC_COFINS_NUM": "BASE_COFINS",
                "VL_PIS_NUM": "PIS",
                "VL_COFINS_NUM": "COFINS",
            }
        )
    )
    return grouped


@st.cache_data(show_spinner=False)
def parse_file(uploaded_file) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]:
    """Processa arquivo EFD usando load_efd_from_upload."""
    lines = load_efd_from_upload(uploaded_file)
    return parse_efd_piscofins(lines)


# =============================================================================
# INICIALIZAÇÃO E CARREGAMENTO
# =============================================================================

# Inicializa o estado da sessão
if "files_data" not in st.session_state:
    st.session_state.files_data = []

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
    "📤 Carregar Arquivos SPED PIS/COFINS (.txt ou .zip)",
    type=["txt", "zip"],
    accept_multiple_files=True,
    key="file_uploader",
)

# Processamento de arquivos
if uploaded_files:
    # Verifica se há novos arquivos para processar
    new_files = [f for f in uploaded_files if f.name not in [d['name'] for d in st.session_state.files_data]]
    
    if new_files:
        
        # Processar arquivos
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, f in enumerate(new_files):
            try:
                status_text.text(f"⏳ Processando: {f.name}")
                
                df_c100_file, df_outros_file, df_ap_file, df_cred_file, comp, emp = parse_file(f)

                st.session_state.files_data.append({
                    "name": f.name,
                    "df_c100": df_c100_file,
                    "df_outros": df_outros_file,
                    "df_ap": df_ap_file,
                    "df_cred": df_cred_file,
                    "competencia": comp,
                    "empresa": emp
                })

            except Exception as e:
                st.error(f"❌ Erro ao processar {f.name}: {str(e)}")

            progress_bar.progress((idx + 1) / len(new_files))

        status_text.empty()
        progress_bar.empty()
        st.rerun() # Força o rerun para atualizar a lista de arquivos e filtros

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
    
    for idx, data in enumerate(st.session_state.files_data):
        col_name, col_comp, col_emp, col_remove = st.columns([3, 1, 2, 0.5])
        
        col_name.text(data['name'])
        col_comp.text(data['competencia'])
        col_emp.text(data['empresa'])
        
        if col_remove.button("❌", key=f"remove_{idx}"):
            files_to_remove.append(idx)

    # Remove os arquivos marcados
    if files_to_remove:
        # Remove em ordem decrescente para não bagunçar os índices
        for idx in sorted(files_to_remove, reverse=True):
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
    df_c100["VL_PIS_NUM"] = df_c100["VL_PIS"].apply(to_float)
    df_c100["VL_COFINS_NUM"] = df_c100["VL_COFINS"].apply(to_float)

if not df_outros.empty:
    df_outros["VL_BC_PIS_NUM"] = df_outros["VL_BC_PIS"].apply(to_float)
    df_outros["VL_BC_COFINS_NUM"] = df_outros["VL_BC_COFINS"].apply(to_float)
    df_outros["VL_PIS_NUM"] = df_outros["VL_PIS"].apply(to_float)
    df_outros["VL_COFINS_NUM"] = df_outros["VL_COFINS"].apply(to_float)

# =============================================================================
# CÁLCULO DE TOTAIS E RESUMOS
# =============================================================================

total_pis = 0.0
total_cofins = 0.0
total_base_pis = 0.0
total_base_cofins = 0.0

# Filtra documentos com crédito real para cálculo de totais
df_c100_cred = df_c100[(df_c100["VL_PIS_NUM"] > 0) | (df_c100["VL_COFINS_NUM"] > 0)]
df_outros_cred = df_outros[(df_outros["VL_PIS_NUM"] > 0) | (df_outros["VL_COFINS_NUM"] > 0)]

if not df_c100_cred.empty:
    total_pis += df_c100_cred["VL_PIS_NUM"].sum()
    total_cofins += df_c100_cred["VL_COFINS_NUM"].sum()
    total_base_pis += df_c100_cred["VL_BC_PIS_NUM"].sum()
    total_base_cofins += df_c100_cred["VL_BC_COFINS_NUM"].sum()

if not df_outros_cred.empty:
    total_pis += df_outros_cred["VL_PIS_NUM"].sum()
    total_cofins += df_outros_cred["VL_COFINS_NUM"].sum()
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
            ["VL_BC_PIS_NUM", "VL_BC_COFINS_NUM", "VL_PIS_NUM", "VL_COFINS_NUM"]
        ]
        .sum()
        .rename(
            columns={
                "VL_BC_PIS_NUM": "BASE_PIS",
                "VL_BC_COFINS_NUM": "BASE_COFINS",
                "VL_PIS_NUM": "PIS",
                "VL_COFINS_NUM": "COFINS",
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
        resumo_consolidado = resumo_consolidado.sort_values("TOTAL", ascending=False)

        # Exibir em colunas
        col1, col2 = st.columns([2, 1])

        with col1:
            st.dataframe(
                format_df_currency(resumo_consolidado),
                use_container_width=True,
                height=300,
            )

        with col2:
            # Gráfico de pizza resumido
            fig_pie = px.pie(
                resumo_consolidado,
                values="TOTAL",
                names="GRUPO",
                title="Distribuição dos Créditos",
                hole=0.4,
                color_discrete_sequence=["#1e3a8a", "#0f766e", "#0284c7", "#f59e0b"],
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

    else:
        st.info("ℹ️ Nenhum documento de crédito foi identificado nos arquivos enviados.")

# =============================================================================
# ABA 2: DOCUMENTOS (DETALHAMENTO TÉCNICO)
# =============================================================================

with tab_docs:
    st.markdown("<h2 class='section-title'>📋 Detalhamento Técnico</h2>", unsafe_allow_html=True)

    # NF-e de entrada ENRIQUECIDA
    st.markdown("<h3 class='subsection-title'>NF-e de Entrada (C100/C170) - Análise Detalhada</h3>", unsafe_allow_html=True)

    if df_c100.empty:
        st.info("ℹ️ Nenhum registro C100/C170 foi identificado.")
    else:
        st.metric("Total de linhas de NF-e", len(df_c100))
        
        # Colunas a exibir na tabela principal (COM CHAVE DE ACESSO)
        cols_to_display = [
            "CHV_NFE", "DT_DOC", "NUM_DOC", "NOME_PART", "NCM", "DESCR_ITEM",
            "VL_BC_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS"
        ]
        
        # Filtra apenas colunas que existem
        cols_to_display = [col for col in cols_to_display if col in df_c100.columns]
        
        df_c100_display = df_c100[cols_to_display].copy()
        
        # Renomeia para melhor legibilidade
        df_c100_display = df_c100_display.rename(columns={
            "CHV_NFE": "Chave de Acesso",
            "DT_DOC": "Data Emissão",
            "NUM_DOC": "NF",
            "NOME_PART": "Fornecedor",
            "NCM": "NCM",
            "DESCR_ITEM": "Descrição",
            "VL_BC_PIS": "BC PIS",
            "VL_PIS": "Valor PIS",
            "VL_BC_COFINS": "BC COFINS",
            "VL_COFINS": "Valor COFINS"
        })
        
        st.dataframe(
            format_df_currency(df_c100_display),
            use_container_width=True,
            height=400,
        )

        # RANKING DE CRÉDITOS POR NCM (NOVO DESIGN)
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("<h3 class='subsection-title'>🏆 Ranking de Créditos por NCM</h3>", unsafe_allow_html=True)
        
        if "NCM" in df_c100_cred.columns:
            # 1. Agrupa por NCM e coleta os dados
            df_ranking_ncm = df_c100_cred.groupby("NCM", as_index=False).agg({
                "VL_PIS_NUM": "sum",
                "VL_COFINS_NUM": "sum",
                "DESCR_ITEM": lambda x: " | ".join(x.unique()[:5])  # Top 5 produtos
            }).rename(columns={
                "VL_PIS_NUM": "Total_PIS",
                "VL_COFINS_NUM": "Total_COFINS",
                "DESCR_ITEM": "Top_Produtos"
            })
            
            df_ranking_ncm["Total_Creditos"] = df_ranking_ncm["Total_PIS"] + df_ranking_ncm["Total_COFINS"]
            df_ranking_ncm = df_ranking_ncm.sort_values("Total_Creditos", ascending=False).head(10)
            
            # 2. Exibir em tabela com tooltip
            df_ranking_display = df_ranking_ncm.copy()
            df_ranking_display = df_ranking_display.rename(columns={
                "NCM": "NCM",
                "Total_PIS": "PIS",
                "Total_COFINS": "COFINS",
                "Total_Creditos": "Total",
                "Top_Produtos": "Produtos (Top 5)"
            })
            
            st.dataframe(
                format_df_currency(df_ranking_display),
                use_container_width=True,
                height=350,
            )

        # RANKING TOP 10 DE PRODUTOS COM MAIS CRÉDITOS
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("<h3 class='subsection-title'>⭐ Top 10 Produtos com Maior Crédito PIS/COFINS</h3>", unsafe_allow_html=True)
        
        if "COD_ITEM" in df_c100_cred.columns:
            df_ranking_produtos = df_c100_cred.groupby(["COD_ITEM", "DESCR_ITEM", "NCM"], as_index=False).agg({
                "VL_PIS_NUM": "sum",
                "VL_COFINS_NUM": "sum"
            }).rename(columns={
                "VL_PIS_NUM": "Total_PIS",
                "VL_COFINS_NUM": "Total_COFINS"
            })
            
            df_ranking_produtos["Total_Creditos"] = df_ranking_produtos["Total_PIS"] + df_ranking_produtos["Total_COFINS"]
            df_ranking_produtos = df_ranking_produtos.sort_values("Total_Creditos", ascending=False).head(10)
            
            df_ranking_produtos_display = df_ranking_produtos.copy()
            df_ranking_produtos_display = df_ranking_produtos_display.rename(columns={
                "COD_ITEM": "Código",
                "DESCR_ITEM": "Descrição",
                "NCM": "NCM",
                "Total_PIS": "PIS",
                "Total_COFINS": "COFINS",
                "Total_Creditos": "Total"
            })
            
            st.dataframe(
                format_df_currency(df_ranking_produtos_display),
                use_container_width=True,
                height=350,
            )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Demais documentos (COM TRATAMENTO DE BASES ZERADAS)
    st.markdown("<h3 class='subsection-title'>Demais Documentos de Crédito</h3>", unsafe_allow_html=True)

    if df_outros.empty:
        st.info("ℹ️ Nenhum documento adicional foi identificado.")
    else:
        st.metric("Total de documentos", len(df_outros))

        # Filtro por tipo
        tipos_disponiveis = df_outros["TIPO"].unique().tolist()
        tipo_selecionado = st.multiselect(
            "Filtrar por tipo de documento:",
            tipos_disponiveis,
            default=tipos_disponiveis,
        )

        df_outros_filtrado = df_outros[df_outros["TIPO"].isin(tipo_selecionado)]

        # Colunas a exibir (apenas as que existem e são relevantes)
        cols_base = ["COMPETENCIA", "EMPRESA", "TIPO", "DOC", "DT_DOC"]
        numeric_cols = ["VL_BC_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS"]
        
        cols_to_display = cols_base.copy()
        for col in numeric_cols:
            if col in df_outros_filtrado.columns:
                cols_to_display.append(col)
        
        df_outros_display = df_outros_filtrado[cols_to_display].copy()
        
        # Renomeia para melhor legibilidade
        df_outros_display = df_outros_display.rename(columns={
            "TIPO": "Tipo Doc.",
            "DOC": "Número Doc.",
            "DT_DOC": "Data Doc.",
            "VL_BC_PIS": "BC PIS",
            "VL_PIS": "Valor PIS",
            "VL_BC_COFINS": "BC COFINS",
            "VL_COFINS": "Valor COFINS"
        })
        
        st.dataframe(
            format_df_currency(df_outros_display),
            use_container_width=True,
            height=400,
        )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Resumo por CFOP
    st.markdown("<h3 class='subsection-title'>Resumo por CFOP (NF-e de Entrada)</h3>", unsafe_allow_html=True)

    if df_cfop_summary.empty:
        st.info("ℹ️ Não há dados de CFOP disponíveis.")
    else:
        st.dataframe(
            format_df_currency(df_cfop_summary),
            use_container_width=True,
            height=350,
        )

# =============================================================================
# ABA 3: GRÁFICOS E VISUALIZAÇÕES
# =============================================================================

with tab_charts:
    st.markdown("<h2 class='section-title'>📊 Análise Gráfica</h2>", unsafe_allow_html=True)

    if df_resumo_tipos.empty:
        st.info("ℹ️ Nenhum dado disponível para gerar gráficos.")
    else:
        # Gráfico unificado PIS/COFINS
        st.markdown("<h3 class='subsection-title'>Distribuição Consolidada de Créditos PIS/COFINS</h3>", unsafe_allow_html=True)
        
        df_plot = df_resumo_tipos.groupby("GRUPO", as_index=False)[["PIS", "COFINS"]].sum()
        df_plot["TOTAL"] = df_plot["PIS"] + df_plot["COFINS"]
        
        fig_pie_unified = px.pie(
            df_plot,
            values="TOTAL",
            names="GRUPO",
            title="Distribuição Total de Créditos (PIS + COFINS)",
            hole=0.4,
            color_discrete_sequence=["#1e3a8a", "#0f766e", "#0284c7", "#f59e0b", "#ec4899"],
        )
        fig_pie_unified.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie_unified, use_container_width=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Gráfico de barras comparativo
        st.markdown("<h3 class='subsection-title'>Comparativo PIS vs COFINS por Tipo</h3>", unsafe_allow_html=True)

        df_plot_melt = df_plot.melt(id_vars="GRUPO", value_vars=["PIS", "COFINS"], var_name="Tributo", value_name="Valor")

        fig_bar = px.bar(
            df_plot_melt,
            x="GRUPO",
            y="Valor",
            color="Tributo",
            title="Comparativo de Créditos",
            barmode="group",
            color_discrete_map={"PIS": "#1e3a8a", "COFINS": "#0f766e"},
        )
        fig_bar.update_layout(
            hovermode="x unified",
            height=400,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Série temporal (se houver múltiplas competências)
        st.markdown("<h3 class='subsection-title'>Evolução Temporal dos Créditos</h3>", unsafe_allow_html=True)

        df_temporal = df_resumo_tipos.groupby("COMPETENCIA", as_index=False)[["PIS", "COFINS"]].sum()
        df_temporal["TOTAL"] = df_temporal["PIS"] + df_temporal["COFINS"]
        df_temporal = df_temporal.sort_values("COMPETENCIA")

        if len(df_temporal) > 1:
            fig_temporal = px.line(
                df_temporal,
                x="COMPETENCIA",
                y=["PIS", "COFINS"],
                markers=True,
                title="Evolução dos Créditos por Competência",
                color_discrete_map={"PIS": "#1e3a8a", "COFINS": "#0f766e"},
                labels={"value": "Valor (R$)", "COMPETENCIA": "Competência"},
            )
            fig_temporal.update_layout(height=400, hovermode="x unified")
            st.plotly_chart(fig_temporal, use_container_width=True)
        else:
            st.info("ℹ️ Apenas uma competência disponível. Envie múltiplos períodos para ver a evolução.")

# =============================================================================
# ABA 4: EXPORTAÇÃO
# =============================================================================

with tab_export:
    st.markdown("<h2 class='section-title'>💾 Exportar Relatório</h2>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="info-box">
            <strong>📥 Exportar para Excel</strong>  

            Clique no botão abaixo para baixar um relatório consolidado com todas as abas.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Preparar Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Aba 1: Resumo Executivo
        resumo_exec = pd.DataFrame({
            "Métrica": [
                "Créditos PIS",
                "Créditos COFINS",
                "Total Créditos",
                "Base PIS",
                "Base COFINS",
                "Arquivos processados",
            ],
            "Valor": [
                total_pis,
                total_cofins,
                total_pis + total_cofins,
                total_base_pis,
                total_base_cofins,
                len(st.session_state.files_data),
            ],
        })
        resumo_exec.to_excel(writer, sheet_name="RESUMO_EXECUTIVO", index=False)

        # Aba 2: NF-e de entrada
        if not df_c100.empty:
            df_c100.to_excel(writer, sheet_name="C100_C170", index=False)

        # Aba 3: Demais documentos
        if not df_outros.empty:
            df_outros.to_excel(writer, sheet_name="OUTROS_CREDITOS", index=False)

        # Aba 4: Resumo por tipo (incluindo CFOP mapeado)
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
