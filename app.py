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


def resumo_tipo(df_outros: pd.DataFrame, tipos, label: str, competencia: str, empresa: str) -> pd.DataFrame:
    """
    Gera um resumo agregado por tipo de documento:
      - BASE_PIS, BASE_COFINS, PIS, COFINS
    """
    if df_outros.empty:
        return pd.DataFrame()

    df = df_outros[df_outros["TIPO"].isin(tipos)].copy()
    if df.empty:
        return pd.DataFrame()

    base_pis = df["VL_BC_PIS"].apply(to_float).sum()
    base_cof = df["VL_BC_COFINS"].apply(to_float).sum()
    vl_pis = df["VL_PIS"].apply(to_float).sum()
    vl_cof = df["VL_COFINS"].apply(to_float).sum()

    return pd.DataFrame(
        [
            {
                "COMPETENCIA": competencia,
                "EMPRESA": empresa,
                "GRUPO": label,
                "BASE_PIS": base_pis,
                "BASE_COFINS": base_cof,
                "PIS": vl_pis,
                "COFINS": vl_cof,
            }
        ]
    )


# ===== Header =====
st.markdown(
    '<div class="ltx-card">'
    '<div class="main-title">LavoraTAX Advisor • Auditoria EFD PIS/COFINS</div>'
    '<div class="sub-title">Upload do arquivo SPED (PIS/COFINS) e geração automática '
    'de relatórios de créditos por CFOP, documento, tipo de operação e fornecedor.</div>'
    "</div>",
    unsafe_allow_html=True,
)

st.write("")


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
        • Leiaute 2024/2025 (C100/C170, A100, C500, D100, F100)<br>
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
    df_c100, df_outros, competencia, empresa = parse_efd_piscofins(lines)
except Exception as e:
    st.error(f"Erro ao processar o arquivo: {e}")
    st.stop()

# Garantia de colunas de competência/empresa (já vêm do parser, mas por segurança)
for df in (df_c100, df_outros):
    if not df.empty:
        if "COMPETENCIA" not in df.columns:
            df.insert(0, "COMPETENCIA", competencia)
        if "EMPRESA" not in df.columns:
            df.insert(1, "EMPRESA", empresa)

# ===== Métricas resumo =====
total_itens_c100 = len(df_c100)
total_outros = len(df_outros)

total_pis_c100 = df_c100["VL_PIS"].apply(to_float).sum() if not df_c100.empty else 0.0
total_cofins_c100 = df_c100["VL_COFINS"].apply(to_float).sum() if not df_c100.empty else 0.0

total_pis_outros = df_outros["VL_PIS"].apply(to_float).sum() if not df_outros.empty else 0.0
total_cofins_outros = df_outros["VL_COFINS"].apply(to_float).sum() if not df_outros.empty else 0.0

# contador de NFs com crédito (NF-e – C100/C170)
if not df_c100.empty:
    df_nfs = df_c100[["COD_MOD", "SERIE", "NUM_DOC"]].drop_duplicates()
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
        df_tmp.groupby("CFOP", as_index=False)[
            ["TOTAL_DOCUMENTO", "BASE_PIS_NUM", "BASE_COFINS_NUM", "PIS_NUM", "COFINS_NUM"]
        ]
        .sum()
        .sort_values("CFOP")
    )

    df_cfop_summary = pd.DataFrame(
        {
            "COMPETENCIA": competencia,
            "EMPRESA": empresa,
            "CFOP": grp["CFOP"],
            "TOTAL_DOCUMENTO": grp["TOTAL_DOCUMENTO"],
            "BASE_PIS": grp["BASE_PIS_NUM"],
            "BASE_COFINS": grp["BASE_COFINS_NUM"],
            "PIS": grp["PIS_NUM"],
            "COFINS": grp["COFINS_NUM"],
        }
    )

if not df_cfop_summary.empty:
    st.dataframe(df_cfop_summary, use_container_width=True)
else:
    st.caption("Sem dados de CFOP para resumir.")

st.write("")

# ===== Resumos por tipo de documento =====
st.markdown("### 📚 Resumo de Créditos por Tipo de Documento")

df_servicos = resumo_tipo(df_outros, ["A100/A170"], "Serviços tomados (A100/A170)", competencia, empresa)
df_energia = resumo_tipo(df_outros, ["C500/C505"], "Energia elétrica (C500/C505)", competencia, empresa)
df_fretes = resumo_tipo(
    df_outros, ["D100/D101", "D100/D105"], "Fretes / transporte (D100/D101/D105)", competencia, empresa
)
df_out_fat = resumo_tipo(df_outros, ["F100/F120"], "Outras faturas (F100/F120)", competencia, empresa)

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("##### Serviços tomados (A100/A170)")
    if df_servicos is not None and not df_servicos.empty:
        st.table(df_servicos)
    else:
        st.caption("Nenhum crédito de serviços tomados identificado.")

    st.markdown("##### Fretes / transporte (D100/D101/D105)")
    if df_fretes is not None and not df_fretes.empty:
        st.table(df_fretes)
    else:
        st.caption("Nenhum crédito de fretes identificado.")

with col_b:
    st.markdown("##### Energia elétrica (C500/C505)")
    if df_energia is not None and not df_energia.empty:
        st.table(df_energia)
    else:
        st.caption("Nenhum crédito de energia elétrica identificado.")

    st.markdown("##### Outras faturas (F100/F120)")
    if df_out_fat is not None and not df_out_fat.empty:
        st.table(df_out_fat)
    else:
        st.caption("Nenhum crédito de outras faturas identificado.")

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
