"""
LavoraTAX Advisor – EFD PIS/COFINS (Versão 2.1 - Executiva)
===========================================================

Painel executivo para análise consolidada de créditos de PIS/COFINS.
Otimizado para CEO, CFO, Diretores Tributários e Financeiros.

Principais melhorias:
* Design moderno e profissional com tema executivo
* KPIs destacados e visualizações de impacto
* Navegação intuitiva e responsiva
* Gráficos interativos com Plotly
* Tabelas filtráveis e exportáveis
* Consolidação inteligente de múltiplos SPEDs
* Performance otimizada com cache
* **FIX:** Formatação de moeda brasileira nas tabelas
* **NEW:** Consolidação de créditos de NF-e (C100/C170) por CFOP mapeado
"""

import io
import zipfile
from typing import List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from parser_pis_cofins import parse_efd_piscofins


# =============================================================================
# CONFIGURAÇÃO DE PÁGINA
# =============================================================================

st.set_page_config(
    page_title="LavoraTAX Advisor – EFD PIS/COFINS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# TEMA E ESTILO CUSTOMIZADO (EXECUTIVO)
# =============================================================================

st.markdown(
    """
    <style>
    /* Variáveis de cor executiva */
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
    # Usa o locale para formatação correta (milhar com ponto, decimal com vírgula)
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_df_currency(df: pd.DataFrame) -> pd.DataFrame:
    """Formata valores monetários para moeda brasileira em um DataFrame."""
    df_formatted = df.copy()
    
    # Colunas a serem formatadas
    cols_to_format = ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS", "TOTAL", "TOTAL_PIS_COFINS", "VL_BC_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS"]
    
    for col in cols_to_format:
        if col in df_formatted.columns:
            # Converte para float e formata como moeda brasileira
            # O uso de float(x) é seguro aqui porque as colunas já foram convertidas para números (VL_..._NUM)
            # ou são resultados de soma (BASE_..., PIS, COFINS, TOTAL)
            df_formatted[col] = df_formatted[col].apply(lambda x: format_currency(float(x)) if pd.notna(x) else "R$ 0,00")
    
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
    """Agrupa créditos de NF-e (C100/C170) por CFOP mapeado."""
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

    # Cria a coluna de CFOP Mapeado
    df = df_c100.copy()
    df["CFOP_GRUPO"] = df["CFOP"].astype(str).map(CFOP_MAP).fillna("Outras NF-e de Entrada")

    # Agrupa por Competência, Empresa e CFOP Mapeado
    grouped = (
        df.groupby(["COMPETENCIA", "EMPRESA", "CFOP_GRUPO"], as_index=False)[
            ["VL_BC_PIS_NUM", "VL_BC_COFINS_NUM", "VL_PIS_NUM", "VL_COFINS_NUM"]
        ]
        .sum()
        .rename(
            columns={
                "CFOP_GRUPO": "GRUPO",
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
    """Processa arquivo EFD com cache."""
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    lines: List[str] = []

    if name.endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for fname in zf.namelist():
                    if fname.lower().endswith(".txt"):
                        raw = zf.read(fname)
                        try:
                            decoded = raw.decode("utf-8")
                        except Exception:
                            decoded = raw.decode("latin-1")
                        lines.extend(decoded.splitlines())
        except Exception:
            try:
                decoded = data.decode("utf-8")
            except Exception:
                decoded = data.decode("latin-1")
            lines.extend(decoded.splitlines())
    elif name.endswith(".txt"):
        try:
            decoded = data.decode("utf-8")
        except Exception:
            decoded = data.decode("latin-1")
        lines.extend(decoded.splitlines())
    else:
        raise ValueError("Formato inválido. Apenas .txt ou .zip são suportados.")

    return parse_efd_piscofins(lines)


# =============================================================================
# CABEÇALHO E UPLOAD
# =============================================================================

st.markdown(
    """
    <div class="header-main">
        <h1>📊 LavoraTAX Advisor</h1>
        <p>Análise Executiva de Créditos PIS/COFINS – EFD Contribuições</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 📁 Carregue seus arquivos SPED")

col_upload, col_info = st.columns([2, 1])

with col_upload:
    uploaded_files = st.file_uploader(
        "Selecione 1 a 12 arquivos EFD PIS/COFINS (.txt ou .zip)",
        type=["txt", "zip"],
        accept_multiple_files=True,
        help="Você pode enviar múltiplos arquivos de diferentes empresas ou períodos.",
    )

with col_info:
    st.info(
        """
        **Dicas:**
        - Máximo 12 arquivos por sessão
        - Formatos: .txt ou .zip
        - Processamento automático com cache
        """
    )

if not uploaded_files:
    st.warning("👉 Envie ao menos um arquivo para iniciar a análise.")
    st.stop()

if len(uploaded_files) > 12:
    st.error("❌ Máximo de 12 arquivos permitidos por sessão.")
    st.stop()

# =============================================================================
# PROCESSAMENTO DOS ARQUIVOS
# =============================================================================

dfs_c100: List[pd.DataFrame] = []
dfs_outros: List[pd.DataFrame] = []
dfs_ap: List[pd.DataFrame] = []
dfs_cred: List[pd.DataFrame] = []
files_info = []

progress_bar = st.progress(0)
status_text = st.empty()

for idx, f in enumerate(uploaded_files):
    try:
        status_text.text(f"Processando arquivo {idx + 1}/{len(uploaded_files)}: {f.name}")
        df_c100_file, df_outros_file, df_ap_file, df_cred_file, comp, emp = parse_file(f)

        if not df_c100_file.empty:
            df_c100_file["COMPETENCIA"] = comp
            df_c100_file["EMPRESA"] = emp
            dfs_c100.append(df_c100_file)

        if not df_outros_file.empty:
            df_outros_file["COMPETENCIA"] = comp
            df_outros_file["EMPRESA"] = emp
            dfs_outros.append(df_outros_file)

        if not df_ap_file.empty:
            dfs_ap.append(df_ap_file)

        if not df_cred_file.empty:
            dfs_cred.append(df_cred_file)

        files_info.append({"arquivo": f.name, "competencia": comp, "empresa": emp})

    except Exception as e:
        st.error(f"❌ Erro ao processar {f.name}: {str(e)}")

    progress_bar.progress((idx + 1) / len(uploaded_files))

status_text.empty()
progress_bar.empty()

# Combina DataFrames
df_c100 = pd.concat(dfs_c100, ignore_index=True) if dfs_c100 else pd.DataFrame()
df_outros = pd.concat(dfs_outros, ignore_index=True) if dfs_outros else pd.DataFrame()
df_ap = pd.concat(dfs_ap, ignore_index=True) if dfs_ap else pd.DataFrame()
df_cred = pd.concat(dfs_cred, ignore_index=True) if dfs_cred else pd.DataFrame()

# =============================================================================
# CONVERSÃO NUMÉRICA
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

if not df_c100.empty:
    total_pis += df_c100["VL_PIS_NUM"].sum()
    total_cofins += df_c100["VL_COFINS_NUM"].sum()
    total_base_pis += df_c100["VL_BC_PIS_NUM"].sum()
    total_base_cofins += df_c100["VL_BC_COFINS_NUM"].sum()

if not df_outros.empty:
    total_pis += df_outros["VL_PIS_NUM"].sum()
    total_cofins += df_outros["VL_COFINS_NUM"].sum()
    total_base_pis += df_outros["VL_BC_PIS_NUM"].sum()
    total_base_cofins += df_outros["VL_BC_COFINS_NUM"].sum()

total_ap_pis = 0.0
if not df_ap.empty:
    # Procura pela coluna de contribuição total
    for col in df_ap.columns:
        if "Contribuição" in col and "Período" in col:
            total_ap_pis = df_ap[col].apply(to_float).sum()
            break

total_cred_pis = 0.0
if not df_cred.empty and "VL_CRED" in df_cred.columns:
    total_cred_pis = df_cred["VL_CRED"].apply(to_float).sum()

# Resumos por tipo de documento (Outros)
df_servicos = resumo_tipo(df_outros, ["A100/A170"], "Serviços tomados")
df_energia = resumo_tipo(df_outros, ["C500/C501/C505"], "Energia elétrica")
df_fretes = resumo_tipo(df_outros, ["D100/D101", "D100/D105"], "Fretes/Transporte")
df_outros_docs = resumo_tipo(df_outros, ["F100/F120"], "Outros documentos")

# Resumo por CFOP Mapeado (NF-e)
df_cfop_map = resumo_cfop_mapeado(df_c100)

# Consolidação de todos os resumos
df_resumo_tipos = pd.concat(
    [df_cfop_map, df_servicos, df_energia, df_fretes, df_outros_docs], ignore_index=True
) if any(not x.empty for x in [df_cfop_map, df_servicos, df_energia, df_fretes, df_outros_docs]) else pd.DataFrame()

# Resumo por CFOP (Original, para detalhamento)
if not df_c100.empty:
    df_cfop_summary = (
        df_c100.groupby(["COMPETENCIA", "EMPRESA", "CFOP"], as_index=False)[
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

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Resumo por competência e empresa
    st.markdown("<h3 class='subsection-title'>Resumo por Competência e Empresa</h3>", unsafe_allow_html=True)

    if not df_resumo_tipos.empty:
        # Seletor de competência e empresa
        combos = (
            df_resumo_tipos[["COMPETENCIA", "EMPRESA"]]
            .drop_duplicates()
            .sort_values(["COMPETENCIA", "EMPRESA"])
        )
        combo_options = [
            f"{row[0]} - {row[1]}" for row in combos.itertuples(index=False, name=None)
        ]

        if combo_options:
            selected = st.selectbox(
                "Selecione a competência e empresa:",
                combo_options,
                key="exec_combo",
            )
            sel_comp, sel_emp = selected.split(" - ", 1)
            df_sel = df_resumo_tipos[
                (df_resumo_tipos["COMPETENCIA"] == sel_comp)
                & (df_resumo_tipos["EMPRESA"] == sel_emp)
            ]

            if not df_sel.empty:
                df_sel_display = df_sel.copy()
                df_sel_display["TOTAL"] = df_sel_display["PIS"] + df_sel_display["COFINS"]

                st.dataframe(
                    format_df_currency(df_sel_display),
                    use_container_width=True,
                    height=250,
                )

# =============================================================================
# ABA 2: DOCUMENTOS (DETALHAMENTO TÉCNICO)
# =============================================================================

with tab_docs:
    st.markdown("<h2 class='section-title'>📋 Detalhamento Técnico</h2>", unsafe_allow_html=True)

    # NF-e de entrada
    st.markdown("<h3 class='subsection-title'>NF-e de Entrada (C100/C170)</h3>", unsafe_allow_html=True)

    if df_c100.empty:
        st.info("ℹ️ Nenhum registro C100/C170 foi identificado.")
    else:
        st.metric("Total de linhas de NF-e", len(df_c100))
        st.dataframe(
            format_df_currency(df_c100[[
                "COMPETENCIA", "EMPRESA", "NUM_DOC", "DT_DOC", "COD_PART",
                "CFOP", "VL_BC_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS"
            ]]),
            use_container_width=True,
            height=400,
        )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Demais documentos
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

        st.dataframe(
            format_df_currency(df_outros_filtrado[[
                "COMPETENCIA", "EMPRESA", "TIPO", "DOC", "DT_DOC",
                "VL_BC_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS"
            ]]),
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
        # Gráficos principais
        col_chart1, col_chart2 = st.columns(2)

        df_plot = df_resumo_tipos.groupby("GRUPO", as_index=False)[["PIS", "COFINS"]].sum()

        with col_chart1:
            fig_pis = px.pie(
                df_plot,
                values="PIS",
                names="GRUPO",
                title="Distribuição de Créditos PIS",
                hole=0.4,
                color_discrete_sequence=["#1e3a8a", "#0f766e", "#0284c7", "#f59e0b"],
            )
            fig_pis.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pis, use_container_width=True)

        with col_chart2:
            fig_cof = px.pie(
                df_plot,
                values="COFINS",
                names="GRUPO",
                title="Distribuição de Créditos COFINS",
                hole=0.4,
                color_discrete_sequence=["#1e3a8a", "#0f766e", "#0284c7", "#f59e0b"],
            )
            fig_cof.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_cof, use_container_width=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Gráfico de barras comparativo
        st.markdown("<h3 class='subsection-title'>Comparativo PIS vs COFINS por Tipo</h3>", unsafe_allow_html=True)

        fig_bar = px.bar(
            df_plot,
            x="GRUPO",
            y=["PIS", "COFINS"],
            title="Comparativo de Créditos",
            barmode="group",
            color_discrete_map={"PIS": "#1e3a8a", "COFINS": "#0f766e"},
            labels={"value": "Valor (R$)", "GRUPO": "Tipo de Documento"},
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
                len(uploaded_files),
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
        file_name="LavoraTAX_Relatorio_PIS_COFINS.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Informações sobre os arquivos processados
    st.markdown("<h3 class='subsection-title'>Arquivos Processados</h3>", unsafe_allow_html=True)

    if files_info:
        df_files = pd.DataFrame(files_info)
        st.dataframe(df_files, use_container_width=True)
    else:
        st.info("ℹ️ Nenhum arquivo foi processado com sucesso.")

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
