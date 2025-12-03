# app.py
"""
LavoraTAX Advisor - Dashboard de EFD PIS/COFINS

- Upload de múltiplos SPEDs (txt ou .zip)
- Processamento com cache para melhor performance
- Visão executiva focada (um resumo por vez para o CEO)
- Detalhamento técnico e gráficos
"""

import io
from typing import List, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from parser_pis_cofins import load_efd_from_upload, parse_efd_piscofins


# ==========================================================
# Helpers
# ==========================================================

def to_float(value):
    try:
        s = str(value).strip()
        if s == "":
            return 0.0
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except Exception:
        return 0.0


def format_brl(value):
    try:
        value = float(value)
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return value


def format_df_brl(df, cols):
    df2 = df.copy()
    for c in cols:
        if c in df2.columns:
            df2[c] = df2[c].apply(format_brl)
    return df2


def resumo_tipo(df_outros: pd.DataFrame, tipos: List[str], label: str) -> pd.DataFrame:
    """
    Monta resumo por COMPETENCIA + EMPRESA para uma lista de TIPO(s) de documento.
    """
    if df_outros.empty:
        return pd.DataFrame()

    df = df_outros[df_outros["TIPO"].isin(tipos)].copy()
    if df.empty:
        return pd.DataFrame()

    df["VL_BC_PIS_NUM"] = df["VL_BC_PIS"].apply(to_float)
    df["VL_BC_COFINS_NUM"] = df["VL_BC_COFINS"].apply(to_float)
    df["VL_PIS_NUM"] = df["VL_PIS"].apply(to_float)
    df["VL_COFINS_NUM"] = df["VL_COFINS"].apply(to_float)

    grp = (
        df.groupby(["COMPETENCIA", "EMPRESA"], as_index=False)[
            ["VL_BC_PIS_NUM", "VL_BC_COFINS_NUM", "VL_PIS_NUM", "VL_COFINS_NUM"]
        ]
        .sum()
    )
    grp.insert(2, "GRUPO", label)
    grp = grp.rename(
        columns={
            "VL_BC_PIS_NUM": "BASE_PIS",
            "VL_BC_COFINS_NUM": "BASE_COFINS",
            "VL_PIS_NUM": "PIS",
            "VL_COFINS_NUM": "COFINS",
        }
    )
    return grp


# ==========================================================
# CACHE – processamento de arquivos
# ==========================================================

@st.cache_data(show_spinner=False)
def process_efd_file(name: str, data_bytes: bytes):
    """
    Processa UM arquivo (txt/zip) de EFD utilizando o parser,
    com cache por (nome + conteúdo). Isso deixa a navegação
    fluida depois do primeiro processamento.
    """
    class FakeUpload:
        def __init__(self, fname, fdata):
            self.name = fname
            self._data = fdata

        def read(self):
            return self._data

    fake = FakeUpload(name, data_bytes)
    lines = load_efd_from_upload(fake)
    return parse_efd_piscofins(lines)  # df_c100, df_outros, df_ap_pis, df_cred_pis, comp, emp


# ==========================================================
# CONFIG STREAMLIT
# ==========================================================

st.set_page_config(
    page_title="LavoraTAX Advisor - EFD PIS/COFINS",
    page_icon="📊",
    layout="wide",
)

# CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0f172a;
        color: #e5e7eb;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .ltx-title {
        font-size: 26px;
        font-weight: 700;
        color: #f9fafb;
        margin-bottom: 0.25rem;
    }
    .ltx-subtitle {
        font-size: 14px;
        color: #9ca3af;
        margin-bottom: 1.5rem;
    }
    .ltx-card {
        background: #020617;
        border-radius: 10px;
        padding: 14px 16px;
        border: 1px solid #1f2937;
        box-shadow: 0 10px 12px rgba(15,23,42,0.55);
        min-height: 98px;
    }
    .ltx-card-title {
        font-size: 12px;
        color: #9ca3af;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .ltx-card-value {
        font-size: 22px;
        font-weight: 800;
        color: #f9fafb;
    }
    .ltx-card-sub {
        font-size: 11px;
        color: #6b7280;
        margin-top: 4px;
    }
    .ltx-section-title {
        font-size: 18px;
        font-weight: 600;
        color: #e5e7eb;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    .ltx-footer {
        font-size: 11px;
        color: #6b7280;
        margin-top: 1.2rem;
        text-align: right;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 1300px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 32px;
        background-color: #020617;
        border-radius: 999px;
        padding: 4px 16px;
        color: #9ca3af;
        font-size: 13px;
        border: 1px solid transparent;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(90deg, #1d4ed8, #f97316);
        color: white;
        border-color: #1d4ed8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
    <div class="ltx-title">LavoraTAX Advisor • EFD PIS/COFINS</div>
    <div class="ltx-subtitle">
        Consolidação inteligente de créditos de PIS/COFINS por tipo de documento, com visão executiva e trilha técnica.
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# UPLOAD
# ==========================================================

col_upload, col_info = st.columns([2, 1.2])

with col_upload:
    uploaded_files = st.file_uploader(
        "Carregue 1 ou mais arquivos EFD PIS/COFINS (.txt ou .zip)",
        type=["txt", "zip"],
        accept_multiple_files=True,
    )

with col_info:
    st.markdown("#### Como usar")
    st.markdown(
        "- Pode carregar EFDs de **várias empresas** e **vários meses** de uma vez.\n"
        "- A análise é cacheada por arquivo, então a navegação depois do upload fica leve.\n"
        "- Os resumos executivos são exibidos **um por vez**, focando na leitura do CEO."
    )

if not uploaded_files:
    st.info("Carregue ao menos um arquivo de EFD PIS/COFINS para iniciar a análise.")
    st.stop()

# ==========================================================
# PROCESSAMENTO (com cache)
# ==========================================================

dfs_c100 = []
dfs_outros = []
dfs_ap_pis = []
dfs_cred_pis = []

progress = st.progress(0.0)
status = st.empty()

for i, f in enumerate(uploaded_files, start=1):
    status.text(f"Processando arquivo {i}/{len(uploaded_files)}: {f.name}")
    try:
        data_bytes = f.read()  # conteúdo bruto
        (
            df_c100_file,
            df_outros_file,
            df_ap_pis_file,
            df_cred_pis_file,
            comp,
            emp,
        ) = process_efd_file(f.name, data_bytes)

        if not df_c100_file.empty:
            df_c100_file["COMPETENCIA"] = comp
            df_c100_file["EMPRESA"] = emp
            dfs_c100.append(df_c100_file)

        if not df_outros_file.empty:
            df_outros_file["COMPETENCIA"] = comp
            df_outros_file["EMPRESA"] = emp
            dfs_outros.append(df_outros_file)

        if not df_ap_pis_file.empty:
            dfs_ap_pis.append(df_ap_pis_file)

        if not df_cred_pis_file.empty:
            dfs_cred_pis.append(df_cred_pis_file)

    except Exception as e:
        st.error(f"Erro ao processar {f.name}: {e}")

    progress.progress(i / len(uploaded_files))

status.empty()
progress.empty()

df_c100 = pd.concat(dfs_c100, ignore_index=True) if dfs_c100 else pd.DataFrame()
df_outros = pd.concat(dfs_outros, ignore_index=True) if dfs_outros else pd.DataFrame()
df_ap_pis = pd.concat(dfs_ap_pis, ignore_index=True) if dfs_ap_pis else pd.DataFrame()
df_cred_pis = (
    pd.concat(dfs_cred_pis, ignore_index=True) if dfs_cred_pis else pd.DataFrame()
)

# ==========================================================
# NORMALIZAÇÃO NUMÉRICA
# ==========================================================

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

total_pis_credit = 0.0
total_cofins_credit = 0.0
if not df_c100.empty:
    total_pis_credit += df_c100["VL_PIS_NUM"].sum()
    total_cofins_credit += df_c100["VL_COFINS_NUM"].sum()
if not df_outros.empty:
    total_pis_credit += df_outros["VL_PIS_NUM"].sum()
    total_cofins_credit += df_outros["VL_COFINS_NUM"].sum()

total_ap_pis = 0.0
if not df_ap_pis.empty and "VL_TOT_CONT_REAL" in df_ap_pis.columns:
    total_ap_pis = df_ap_pis["VL_TOT_CONT_REAL"].sum()

total_cred_pis_bloco_m = 0.0
if not df_cred_pis.empty and "VL_CRED" in df_cred_pis.columns:
    total_cred_pis_bloco_m = df_cred_pis["VL_CRED"].apply(to_float).sum()

# Resumos por tipo
df_servicos = resumo_tipo(df_outros, ["A100/A170"], "Serviços tomados (A100/A170)")
df_energia = resumo_tipo(
    df_outros,
    ["C500/C501/C505"],
    "Energia elétrica (C500/C501/C505 - PIS em C501, COFINS em C505)",
)
df_fretes = resumo_tipo(
    df_outros,
    ["D100/D101", "D100/D105"],
    "Fretes / transporte (D100/D101/D105)",
)
df_out_fat = resumo_tipo(df_outros, ["F100/F120"], "Outras faturas (F100/F120)")

df_resumo_tipos = pd.concat(
    [df_servicos, df_energia, df_fretes, df_out_fat], ignore_index=True
) if any(
    not x.empty for x in [df_servicos, df_energia, df_fretes, df_out_fat]
) else pd.DataFrame()

# Resumo CFOP (NF-e de entrada)
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
    df_cfop_summary = pd.DataFrame(
        columns=["COMPETENCIA", "EMPRESA", "CFOP", "BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]
    )

# ==========================================================
# ABAS
# ==========================================================

tab_exec, tab_det, tab_grafs = st.tabs(
    ["Visão Executiva (CEO)", "Detalhamento Técnico", "Gráficos & Relatórios"]
)

# ----------------------------------------------------------
# Visão Executiva
# ----------------------------------------------------------
with tab_exec:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="ltx-card">
                <div class="ltx-card-title">Créditos de PIS identificados</div>
                <div class="ltx-card-value">{format_brl(total_pis_credit)}</div>
                <div class="ltx-card-sub">NF-e + serviços + energia + fretes + demais docs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="ltx-card">
                <div class="ltx-card-title">Créditos de COFINS identificados</div>
                <div class="ltx-card-value">{format_brl(total_cofins_credit)}</div>
                <div class="ltx-card-sub">Mesma base dos créditos de PIS (documentos irmãos)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="ltx-card">
                <div class="ltx-card-title">PIS apurado (Bloco M200)</div>
                <div class="ltx-card-value">{format_brl(total_ap_pis)}</div>
                <div class="ltx-card-sub">Somatório de VL_TOT_CONT_REAL</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="ltx-card">
                <div class="ltx-card-title">Créditos de PIS declarados (Bloco M105)</div>
                <div class="ltx-card-value">{format_brl(total_cred_pis_bloco_m)}</div>
                <div class="ltx-card-sub">Somatório de VL_CRED (M105)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 🔎 Nova navegação "um resumo por vez"
    st.markdown('<div class="ltx-section-title">Resumo executivo por empresa / competência</div>', unsafe_allow_html=True)

    if df_resumo_tipos.empty:
        st.info("Nenhum crédito consolidado por tipo de documento foi identificado.")
    else:
        # Combos de COMPETENCIA + EMPRESA
        combos = (
            df_resumo_tipos[["COMPETENCIA", "EMPRESA"]]
            .drop_duplicates()
            .sort_values(["COMPETENCIA", "EMPRESA"])
        )

        combo_labels = [
            f"{row.COMP
ETENCIA} - {row.EMPRESA}" for row in combos.itertuples(index=False)
        ]
        selected_label = st.selectbox(
            "Selecione a competência e empresa para visualizar o resumo:",
            combo_labels,
        )

        sel_comp, sel_emp = selected_label.split(" - ", 1)
        df_sel = df_resumo_tipos[
            (df_resumo_tipos["COMPETENCIA"] == sel_comp)
            & (df_resumo_tipos["EMPRESA"] == sel_emp)
        ].copy()

        grupos_disp = list(df_sel["GRUPO"].unique())
        grupo_escolhido = st.radio(
            "Escolha o tipo de documento para ver o resumo (um por vez):",
            grupos_disp,
            horizontal=True,
        )

        df_grupo = df_sel[df_sel["GRUPO"] == grupo_escolhido].copy()

        if df_grupo.empty:
            st.info("Sem dados para esse tipo de documento.")
        else:
            df_grupo["TOTAL_PIS_COFINS"] = df_grupo["PIS"] + df_grupo["COFINS"]
            df_grupo_fmt = format_df_brl(
                df_grupo,
                ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS", "TOTAL_PIS_COFINS"],
            )
            st.dataframe(df_grupo_fmt, use_container_width=True, height=200)

# ----------------------------------------------------------
# Detalhamento Técnico
# ----------------------------------------------------------
with tab_det:
    st.subheader("NF-e de entrada (C100/C170) – Detalhamento por item")
    if df_c100.empty:
        st.info("Nenhum registro C100/C170 de entrada foi identificado.")
    else:
        st.dataframe(df_c100, use_container_width=True, height=360)

    st.subheader("Demais documentos de crédito (A100/A170, C500, D100, F100/F120)")
    if df_outros.empty:
        st.info("Nenhum documento adicional de crédito foi identificado.")
    else:
        st.dataframe(df_outros, use_container_width=True, height=360)

    st.subheader("Resumo por CFOP (NF-e de entrada)")
    if df_cfop_summary.empty:
        st.info("Sem NF-e de entrada para resumo por CFOP.")
    else:
        df_cfop_fmt = format_df_brl(
            df_cfop_summary, ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]
        )
        st.dataframe(df_cfop_fmt, use_container_width=True, height=360)

# ----------------------------------------------------------
# Gráficos & Relatórios
# ----------------------------------------------------------
with tab_grafs:
    st.subheader("Gráficos de composição dos créditos")

    if df_resumo_tipos.empty:
        st.info("Sem créditos consolidados por tipo de documento para gerar gráficos.")
    else:
        df_plot = df_resumo_tipos.groupby("GRUPO", as_index=False)[
            ["PIS", "COFINS"]
        ].sum()

        col_pis, col_cof = st.columns(2)
        with col_pis:
            fig_pis = px.pie(
                df_plot,
                values="PIS",
                names="GRUPO",
                hole=0.5,
                title="Composição dos créditos de PIS por tipo de documento",
            )
            st.plotly_chart(fig_pis, use_container_width=True)

        with col_cof:
            fig_cof = px.pie(
                df_plot,
                values="COFINS",
                names="GRUPO",
                hole=0.5,
                title="Composição dos créditos de COFINS por tipo de documento",
            )
            st.plotly_chart(fig_cof, use_container_width=True)

    st.markdown("---")
    st.subheader("Exportar relatório consolidado (Excel)")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_c100.to_excel(writer, sheet_name="C100_C170", index=False)
        df_outros.to_excel(writer, sheet_name="OUTROS_CREDITOS", index=False)
        df_ap_pis.to_excel(writer, sheet_name="AP_PIS_M200", index=False)
        df_cred_pis.to_excel(writer, sheet_name="CREDITOS_PIS_M105", index=False)
        if not df_resumo_tipos.empty:
            df_res_exec = df_resumo_tipos.copy()
            df_res_exec["TOTAL_PIS_COFINS"] = (
                df_res_exec["PIS"] + df_res_exec["COFINS"]
            )
            df_res_exec.to_excel(writer, sheet_name="RESUMO_TIPOS", index=False)
        if not df_cfop_summary.empty:
            df_cfop_summary.to_excel(writer, sheet_name="RESUMO_CFOP", index=False)

    buffer.seek(0)

    st.download_button(
        label="📥 Baixar Excel de Créditos PIS/COFINS + Bloco M",
        data=buffer,
        file_name="Relatorio_EFD_PIS_COFINS_LavoraTAX.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.markdown(
    '<div class="ltx-footer">LavoraTAX Advisor • Análise automatizada de EFD PIS/COFINS</div>',
    unsafe_allow_html=True,
)
