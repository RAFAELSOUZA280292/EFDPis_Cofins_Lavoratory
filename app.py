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
LAVORATAX_TEAL = "#0eb8b3"      # cor de destaque (se quiser)
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


# ===== Header =====
st.markdown(
    '<div class="ltx-card">'
    '<div class="main-title">LavoraTAX Advisor • Auditoria EFD PIS/COFINS</div>'
    '<div class="sub-title">Upload do arquivo SPED (PIS/COFINS) e geração automática '
    'de relatórios de créditos por nota, documento, CFOP e fornecedor.</div>'
    "</div>",
    unsafe_allow_html=True,
)

st.write("")  # espaçamento


# ===== Upload =====
col_upload, col_info = st.columns([2, 1.2])

with col_upload:
    uploaded_file = st.file_uploader(
        "Carregue o arquivo EFD PIS/COFINS (.txt ou .zip)",
        type=["txt", "zip"],
        help="O arquivo pode ser o TXT original do PVA ou um ZIP contendo o TXT.",
    )

with col_info:
    st.markdown(
        """
        <div class="ltx-card">
        <div class="ltx-metric">Dica</div>
        <div style="font-size:0.90rem; margin-top:0.3rem;">
        • Um arquivo por vez<br>
        • Usamos o leiaute 2024/2025 (C100/C170, A100, C500, D100, F100)<br>
        • Apenas documentos com <b>crédito efetivo</b> entram nos relatórios.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

if uploaded_file is None:
    st.info("⬆️ Carregue um arquivo para iniciar a análise.")
    st.stop()

# ===== Processamento =====
try:
    lines = load_efd_from_upload(uploaded_file)
    df_c100, df_outros = parse_efd_piscofins(lines)
except Exception as e:
    st.error(f"Erro ao processar o arquivo: {e}")
    st.stop()

# ===== Métricas resumo =====
total_itens_c100 = len(df_c100)
total_outros = len(df_outros)

total_pis_c100 = df_c100["VL_PIS"].apply(lambda x: float(str(x).replace(".", "").replace(",", ".")) if str(x).strip() else 0.0).sum()
total_cofins_c100 = df_c100["VL_COFINS"].apply(lambda x: float(str(x).replace(".", "").replace(",", ".")) if str(x).strip() else 0.0).sum()

total_pis_outros = df_outros["VL_PIS"].apply(lambda x: float(str(x).replace(".", "").replace(",", ".")) if str(x).strip() else 0.0).sum()
total_cofins_outros = df_outros["VL_COFINS"].apply(lambda x: float(str(x).replace(".", "").replace(",", ".")) if str(x).strip() else 0.0).sum()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="ltx-card">
          <div class="ltx-metric">Itens com crédito (NF-e - C100/C170)</div>
          <div class="ltx-metric-value">{total_itens_c100:,}</div>
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
            PIS: R$ {total_pis_c100:,.2f}<br>
            COFINS: R$ {total_cofins_c100:,.2f}
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
            PIS: R$ {total_pis_outros:,.2f}<br>
            COFINS: R$ {total_cofins_outros:,.2f}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# ===== Tabelas =====
st.markdown("### 📄 NF-e de Entrada com Crédito (C100 / C170)")
st.caption("Itens de notas fiscais de entrada que geraram base e/ou crédito de PIS/COFINS.")

with st.expander("Visualizar tabela completa de NF-e (C100/C170)", expanded=True):
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
