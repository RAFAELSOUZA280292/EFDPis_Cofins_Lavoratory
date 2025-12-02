# app.py

import io
import pandas as pd
import streamlit as st

from parser_pis_cofins import load_efd_from_upload, parse_efd_piscofins


# ===== Configuração de página =====
st.set_page_config(
    page_title="LavoraTAX Advisor - EFD PIS/COFINS",
    page_icon="📊",
    layout="wide",
)


# ===== Estilo LavoraTAX (preto + azul marinho escuro) =====
LAVORATAX_DARK = "#050608"      # quase preto
LAVORATAX_NAVY = "#0b1220"      # azul marinho bem escuro
LAVORATAX_TEAL = "#0eb8b3"      # cor de destaque
LAVORATAX_TEXT = "#f5f5f5"

CUSTOM_CSS = f"""
<style>
.stApp {{
    background: radial-gradient(circle at top left, {LAVORATAX_NAVY} 0, {LAVORATAX_DARK} 45%, black 100%);
    color: {LAVORATAX_TEXT};
    font-family: "Segoe UI", system-ui, sans-serif;
}}

.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}}

.main-title {{
    font-size: 2.0rem;
    font-weight: 700;
    color: {LAVORATAX_TEAL};
}}

.sub-title {{
    font-size: 0.95rem;
    color: #d0d4e4;
    margin-bottom: 1.5rem;
}}

.ltx-card {{
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    background: rgba(11, 18, 32, 0.92);
    border: 1px solid rgba(255,255,255,0.04);
    box-shadow: 0 18px 45px rgba(0,0,0,0.65);
}}

.ltx-metric {{
    font-size: 0.80rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #9ca3af;
}}

.ltx-metric-value {{
    font-size: 1.4rem;
    font-weight: 600;
    color: {LAVORATAX_TEAL};
}}

.ltx-footer {{
    font-size: 0.75rem;
    color: #9ca3af;
    margin-top: 2rem;
    text-align: center;
}}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ===== Helpers numéricos / formatação BR =====
def to_float(s) -> float:
    s = str(s).strip()
    if not s:
        return 0.0
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def format_brl(v: float) -> str:
    """
    Converte 77508.52 -> '77.508,52'
    """
    try:
        v = float(v)
    except Exception:
        return str(v)
    s = f"{v:,.2f}"           # 77,508.52 (pt-en)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def format_df_brl(df: pd.DataFrame, numeric_cols) -> pd.DataFrame:
    """
    Retorna uma cópia do df com as colunas numéricas formatadas em texto BR.
    """
    df_disp = df.copy()
    for col in numeric_cols:
        if col in df_disp.columns:
            df_disp[col] = df_disp[col].apply(format_brl)
    return df_disp


def resumo_tipo(df_outros: pd.DataFrame, tipos, label: str) -> pd.DataFrame:
    """
    Gera um resumo agregado por tipo de documento e por COMPETENCIA/EMPRESA:
      - BASE_PIS, BASE_COFINS, PIS, COFINS
    """
    if df_outros.empty:
        return pd.DataFrame()

    df = df_outros[df_outros["TIPO"].isin(tipos)].copy()
    if df.empty:
        return pd.DataFrame()

    df["BASE_PIS_NUM"] = df["VL_BC_PIS"].apply(to_float)
    df["BASE_COFINS_NUM"] = df["VL_BC_COFINS"].apply(to_float)
    df["PIS_NUM"] = df["VL_PIS"].apply(to_float)
    df["COFINS_NUM"] = df["VL_COFINS"].apply(to_float)

    grp = (
        df.groupby(["COMPETENCIA", "EMPRESA"], as_index=False)[
            ["BASE_PIS_NUM", "BASE_COFINS_NUM", "PIS_NUM", "COFINS_NUM"]
        ]
        .sum()
    )

    grp.insert(2, "GRUPO", label)

    grp = grp.rename(
        columns={
            "BASE_PIS_NUM": "BASE_PIS",
            "BASE_COFINS_NUM": "BASE_COFINS",
            "PIS_NUM": "PIS",
            "COFINS_NUM": "COFINS",
        }
    )

    return grp


# ===== Header =====
st.markdown(
    '<div class="ltx-card">'
    '<div class="main-title">LavoraTAX Advisor • Auditoria EFD PIS/COFINS</div>'
    '<div class="sub-title">Upload de 1 ou mais arquivos SPED (PIS/COFINS) e geração automática '
    'de relatórios de créditos por CFOP, NCM, fornecedor, documento e tipo de operação.</div>'
    "</div>",
    unsafe_allow_html=True,
)

st.write("")


# ===== Upload (AGORA ACEITA VÁRIOS ARQUIVOS) =====
col_upload, col_info = st.columns([2, 1.2])

with col_upload:
    uploaded_files = st.file_uploader(
        "Carregue 1 ou mais arquivos EFD PIS/COFINS (.txt ou .zip)",
        type=["txt", "zip"],
        help="Você pode selecionar vários arquivos para analisar 12 meses, por exemplo.",
        accept_multiple_files=True,
    )

with col_info:
    st.markdown(
        """
        <div class="ltx-card">
        <div class="ltx-metric">Dica</div>
        <div style="font-size:0.90rem; margin-top:0.3rem;">
        • Pode carregar até 12 arquivos (12 meses)<br>
        • Leiaute 2024/2025 (C100/C170, A100, C500, D100, F100)<br>
        • Apenas documentos com <b>crédito efetivo</b> entram nos relatórios.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

if not uploaded_files:
    st.info("⬆️ Carregue pelo menos um arquivo para iniciar a análise.")
    st.stop()

# ===== Processamento de múltiplos arquivos =====
df_c100_list = []
df_outros_list = []

for uploaded_file in uploaded_files:
    try:
        lines = load_efd_from_upload(uploaded_file)
        df_c100_i, df_outros_i, competencia_i, empresa_i = parse_efd_piscofins(lines)
        if not df_c100_i.empty:
            df_c100_list.append(df_c100_i)
        if not df_outros_i.empty:
            df_outros_list.append(df_outros_i)
    except Exception as e:
        st.error(f"Erro ao processar o arquivo {uploaded_file.name}: {e}")

if df_c100_list:
    df_c100 = pd.concat(df_c100_list, ignore_index=True)
else:
    df_c100 = pd.DataFrame()

if df_outros_list:
    df_outros = pd.concat(df_outros_list, ignore_index=True)
else:
    df_outros = pd.DataFrame()

if df_c100.empty and df_outros.empty:
    st.error("Nenhum crédito de PIS/COFINS encontrado nos arquivos enviados.")
    st.stop()

# ===== Métricas resumo =====
total_itens_c100 = len(df_c100)
total_outros = len(df_outros)

total_pis_c100 = df_c100["VL_PIS"].apply(to_float).sum() if not df_c100.empty else 0.0
total_cofins_c100 = df_c100["VL_COFINS"].apply(to_float).sum() if not df_c100.empty else 0.0

total_pis_outros = df_outros["VL_PIS"].apply(to_float).sum() if not df_outros.empty else 0.0
total_cofins_outros = df_outros["VL_COFINS"].apply(to_float).sum() if not df_outros.empty else 0.0

# contador de NFs com crédito (NF-e – C100/C170)
if not df_c100.empty:
    df_nfs = df_c100[["COMPETENCIA", "EMPRESA", "COD_MOD", "SERIE", "NUM_DOC"]].drop_duplicates()
    total_nfs_com_credito = len(df_nfs)
else:
    total_nfs_com_credito = 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="ltx-card">
          <div class="ltx-metric">NF-e com crédito (C100/C170)</div>
          <div class="ltx-metric-value">{total_nfs_com_credito:,}</div>
          <div style="font-size:0.80rem; margin-top:0.3rem;">
            Itens com crédito: {total_itens_c100:,}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="ltx-card">
          <div class="ltx-metric">Créditos NF-e (PIS / COFINS)</div>
          <div style="font-size:1.0rem; margin-top:0.3rem;">
            PIS: R$ {format_brl(total_pis_c100)}<br>
            COFINS: R$ {format_brl(total_cofins_c100)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class="ltx-card">
          <div class="ltx-metric">Outros documentos com crédito</div>
          <div class="ltx-metric-value">{total_outros:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
        <div class="ltx-card">
          <div class="ltx-metric">Créditos Outros (PIS / COFINS)</div>
          <div style="font-size:1.0rem; margin-top:0.3rem;">
            PIS: R$ {format_brl(total_pis_outros)}<br>
            COFINS: R$ {format_brl(total_cofins_outros)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# ===== Resumo por CFOP (NF-e) =====
st.markdown("### 🧾 Resumo de Créditos por CFOP (NF-e de entrada)")

if df_c100.empty:
    st.caption("Nenhum item de NF-e com crédito encontrado (C100/C170).")
    df_cfop_summary = pd.DataFrame()
else:
    df_tmp = df_c100.copy()
    df_tmp["TOTAL_DOCUMENTO"] = df_tmp["VL_ITEM"].apply(to_float)
    df_tmp["BASE_PIS_NUM"] = df_tmp["VL_BC_PIS"].apply(to_float)
    df_tmp["BASE_COFINS_NUM"] = df_tmp["VL_BC_COFINS"].apply(to_float)
    df_tmp["PIS_NUM"] = df_tmp["VL_PIS"].apply(to_float)
    df_tmp["COFINS_NUM"] = df_tmp["VL_COFINS"].apply(to_float)

    grp = (
        df_tmp.groupby(["COMPETENCIA", "EMPRESA", "CFOP"], as_index=False)[
            ["TOTAL_DOCUMENTO", "BASE_PIS_NUM", "BASE_COFINS_NUM", "PIS_NUM", "COFINS_NUM"]
        ]
        .sum()
        .sort_values(["COMPETENCIA", "EMPRESA", "CFOP"])
    )

    df_cfop_summary = grp.rename(
        columns={
            "BASE_PIS_NUM": "BASE_PIS",
            "BASE_COFINS_NUM": "BASE_COFINS",
            "PIS_NUM": "PIS",
            "COFINS_NUM": "COFINS",
        }
    )

if not df_cfop_summary.empty:
    df_cfop_display = format_df_brl(
        df_cfop_summary,
        ["TOTAL_DOCUMENTO", "BASE_PIS", "BASE_COFINS", "PIS", "COFINS"],
    )
    st.dataframe(df_cfop_display, use_container_width=True)
else:
    st.caption("Sem dados de CFOP para resumir.")

st.write("")

# ===== Resumos por tipo de documento =====
st.markdown("### 📚 Resumo de Créditos por Tipo de Documento")

df_servicos = resumo_tipo(df_outros, ["A100/A170"], "Serviços tomados (A100/A170)")
df_energia = resumo_tipo(df_outros, ["C500/C505"], "Energia elétrica (C500/C505)")
df_fretes = resumo_tipo(df_outros, ["D100/D101", "D100/D105"], "Fretes / transporte (D100/D101/D105)")
df_out_fat = resumo_tipo(df_outros, ["F100/F120"], "Outras faturas (F100/F120)")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("##### Serviços tomados (A100/A170)")
    if df_servicos is not None and not df_servicos.empty:
        st.table(format_df_brl(df_servicos, ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]))
    else:
        st.caption("Nenhum crédito de serviços tomados identificado.")

    st.markdown("##### Fretes / transporte (D100/D101/D105)")
    if df_fretes is not None and not df_fretes.empty:
        st.table(format_df_brl(df_fretes, ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]))
    else:
        st.caption("Nenhum crédito de fretes identificado.")

with col_b:
    st.markdown("##### Energia elétrica (C500/C505)")
    if df_energia is not None and not df_energia.empty:
        st.table(format_df_brl(df_energia, ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]))
    else:
        st.caption("Nenhum crédito de energia elétrica identificado.")

    st.markdown("##### Outras faturas (F100/F120)")
    if df_out_fat is not None and not df_out_fat.empty:
        st.table(format_df_brl(df_out_fat, ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]))
    else:
        st.caption("Nenhum crédito de outras faturas identificado.")

st.write("")

# ===== Ranking TOP 10 NCM (NF-e) =====
st.markdown("### 🥇 TOP 10 NCM com mais créditos (NF-e de entrada)")

if df_c100.empty:
    st.caption("Nenhum item de NF-e com crédito para ranking de NCM.")
    df_rank_ncm = pd.DataFrame()
else:
    df_ncm = df_c100.copy()
    df_ncm["BASE_PIS_NUM"] = df_ncm["VL_BC_PIS"].apply(to_float)
    df_ncm["BASE_COFINS_NUM"] = df_ncm["VL_BC_COFINS"].apply(to_float)
    df_ncm["PIS_NUM"] = df_ncm["VL_PIS"].apply(to_float)
    df_ncm["COFINS_NUM"] = df_ncm["VL_COFINS"].apply(to_float)
    df_ncm["CREDITO_TOTAL"] = df_ncm["PIS_NUM"] + df_ncm["COFINS_NUM"]

    grp_ncm = (
        df_ncm.groupby("NCM", as_index=False)[
            ["BASE_PIS_NUM", "BASE_COFINS_NUM", "PIS_NUM", "COFINS_NUM", "CREDITO_TOTAL"]
        ]
        .sum()
        .sort_values("CREDITO_TOTAL", ascending=False)
        .head(10)
    )

    df_rank_ncm = grp_ncm.rename(
        columns={
            "BASE_PIS_NUM": "BASE_PIS",
            "BASE_COFINS_NUM": "BASE_COFINS",
            "PIS_NUM": "PIS",
            "COFINS_NUM": "COFINS",
        }
    )

if not df_rank_ncm.empty:
    df_rank_ncm_disp = format_df_brl(
        df_rank_ncm,
        ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS", "CREDITO_TOTAL"],
    )
    st.dataframe(df_rank_ncm_disp, use_container_width=True)
else:
    st.caption("Sem dados para ranking de NCM.")

st.write("")

# ===== Ranking TOP 10 Fornecedores (todos os documentos) =====
st.markdown("### 🥇 TOP 10 Fornecedores que mais geram créditos (NF-e + Outros docs)")

# unificar créditos por fornecedor (C100 + OUTROS)
frames_forn = []

if not df_c100.empty and "FORNECEDOR" in df_c100.columns:
    df_f1 = df_c100[["FORNECEDOR", "VL_PIS", "VL_COFINS"]].copy()
    df_f1["VL_PIS"] = df_f1["VL_PIS"].apply(to_float)
    df_f1["VL_COFINS"] = df_f1["VL_COFINS"].apply(to_float)
    frames_forn.append(df_f1)

if not df_outros.empty and "FORNECEDOR" in df_outros.columns:
    df_f2 = df_outros[["FORNECEDOR", "VL_PIS", "VL_COFINS"]].copy()
    df_f2["VL_PIS"] = df_f2["VL_PIS"].apply(to_float)
    df_f2["VL_COFINS"] = df_f2["VL_COFINS"].apply(to_float)
    frames_forn.append(df_f2)

if frames_forn:
    df_forn_all = pd.concat(frames_forn, ignore_index=True)
    df_forn_all["CREDITO_TOTAL"] = df_forn_all["VL_PIS"] + df_forn_all["VL_COFINS"]

    grp_forn = (
        df_forn_all.groupby("FORNECEDOR", as_index=False)[["VL_PIS", "VL_COFINS", "CREDITO_TOTAL"]]
        .sum()
        .sort_values("CREDITO_TOTAL", ascending=False)
        .head(10)
    )

    df_rank_forn = grp_forn.rename(
        columns={
            "VL_PIS": "PIS",
            "VL_COFINS": "COFINS",
        }
    )
else:
    df_rank_forn = pd.DataFrame()

if not df_rank_forn.empty:
    df_rank_forn_disp = format_df_brl(
        df_rank_forn,
        ["PIS", "COFINS", "CREDITO_TOTAL"],
    )
    st.dataframe(df_rank_forn_disp, use_container_width=True)
else:
    st.caption("Sem dados para ranking de fornecedores.")

st.write("")

# ===== Tabelas detalhadas =====
st.markdown("### 📄 NF-e de Entrada com Crédito (C100 / C170)")
st.caption("Itens de notas fiscais de entrada que geraram base e/ou crédito de PIS/COFINS.")

with st.expander("Visualizar tabela completa de NF-e (C100/C170)", expanded=False):
    st.dataframe(
        df_c100,
        use_container_width=True,
        height=400,
    )

st.markdown("### 📄 Outros Documentos com Crédito (A100, C500, D100, F100)")
st.caption("Serviços, energia elétrica, CT-e e demais documentos geradores de créditos.")

with st.expander("Visualizar tabela completa de outros documentos", expanded=False):
    st.dataframe(
        df_outros,
        use_container_width=True,
        height=400,
    )

# ===== Download do Excel =====
st.markdown("### ⬇️ Download do Relatório em Excel")

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_c100.to_excel(writer, sheet_name="C100_C170", index=False)
    df_outros.to_excel(writer, sheet_name="OUTROS_DOCUMENTOS", index=False)
    if not df_cfop_summary.empty:
        df_cfop_summary.to_excel(writer, sheet_name="RESUMO_CFOP", index=False)
    if df_servicos is not None and not df_servicos.empty:
        df_servicos.to_excel(writer, sheet_name="RESUMO_SERVICOS", index=False)
    if df_energia is not None and not df_energia.empty:
        df_energia.to_excel(writer, sheet_name="RESUMO_ENERGIA", index=False)
    if df_fretes is not None and not df_fretes.empty:
        df_fretes.to_excel(writer, sheet_name="RESUMO_FRETES", index=False)
    if df_out_fat is not None and not df_out_fat.empty:
        df_out_fat.to_excel(writer, sheet_name="RESUMO_OUTRAS_FATURAS", index=False)
    if not df_rank_ncm.empty:
        df_rank_ncm.to_excel(writer, sheet_name="RANKING_NCM", index=False)
    if not df_rank_forn.empty:
        df_rank_forn.to_excel(writer, sheet_name="RANKING_FORNECEDORES", index=False)

buffer.seek(0)

st.download_button(
    label="Baixar Excel de Créditos PIS/COFINS",
    data=buffer,
    file_name="Relatorio_Creditos_PIS_COFINS.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown(
    '<div class="ltx-footer">LavoraTAX Advisor • Análise automatizada de EFD PIS/COFINS</div>',
    unsafe_allow_html=True,
)
