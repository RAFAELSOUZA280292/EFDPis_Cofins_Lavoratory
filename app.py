import streamlit as st
import pandas as pd
import plotly.express as px
import io
from parser_pis_cofins import load_efd_from_upload, parse_efd_piscofins

# ============================================================
# Helpers
# ============================================================

def to_float(value):
    try:
        value = str(value).replace(".", "").replace(",", ".")
        return float(value)
    except:
        return 0.0

def format_brl(value):
    try:
        value = float(value)
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return value

def format_df_brl(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = df[col].apply(format_brl)
    return df

def resumo_tipo(df_outros, tipos, label):
    if df_outros.empty:
        return pd.DataFrame()

    df = df_outros[df_outros["TIPO"].isin(tipos)].copy()
    if df.empty:
        return pd.DataFrame()

    df["VL_BC_PIS_NUM"] = df["VL_BC_PIS"].apply(to_float)
    df["VL_PIS_NUM"] = df["VL_PIS"].apply(to_float)
    df["VL_BC_COFINS_NUM"] = df["VL_BC_COFINS"].apply(to_float)
    df["VL_COFINS_NUM"] = df["VL_COFINS"].apply(to_float)

    r = (
        df.groupby(["COMPETENCIA", "EMPRESA"])
        .agg({
            "VL_BC_PIS_NUM": "sum",
            "VL_PIS_NUM": "sum",
            "VL_BC_COFINS_NUM": "sum",
            "VL_COFINS_NUM": "sum"
        })
        .reset_index()
    )
    r["GRUPO"] = label
    return r


# ============================================================
# LAYOUT
# ============================================================

st.set_page_config(page_title="LavoraTax – EFD PIS/COFINS", layout="wide")

st.markdown("""
<style>
body { background-color: #0f172a; }
.ltx-title { font-size: 26px; font-weight: 700; color: #fff; }
.ltx-card { background-color: #1e293b; padding: 15px; border-radius: 8px; }
.ltx-card-title { font-size: 14px; color: #94a3b8; }
.ltx-card-value { font-size: 22px; font-weight: 900; color: #fff; }
</style>
""", unsafe_allow_html=True)

tabs = st.tabs(["Visão Executiva (CEO)", "Detalhamento Técnico", "Gráficos & Relatórios"])

# ============================================================
# Upload
# ============================================================

uploaded_files = st.sidebar.file_uploader("Envie arquivos SPED (.txt ou .zip):", type=["txt", "zip"], accept_multiple_files=True)

all_c100 = []
all_outros = []
all_ap = []
all_cred = []

if uploaded_files:
    for file in uploaded_files:
        try:
            lines = load_efd_from_upload(file)
            df_c100, df_outros, df_ap_pis, df_cred_pis, comp, emp = parse_efd_piscofins(lines)

            if not df_c100.empty:
                df_c100["COMPETENCIA"] = comp
                df_c100["EMPRESA"] = emp

            if not df_outros.empty:
                df_outros["COMPETENCIA"] = comp
                df_outros["EMPRESA"] = emp

            all_c100.append(df_c100)
            all_outros.append(df_outros)
            all_ap.append(df_ap_pis)
            all_cred.append(df_cred_pis)

        except Exception as e:
            st.error(f"Erro ao processar {file.name}: {str(e)}")

    df_c100 = pd.concat(all_c100, ignore_index=True) if all_c100 else pd.DataFrame()
    df_outros = pd.concat(all_outros, ignore_index=True) if all_outros else pd.DataFrame()
    df_ap = pd.concat(all_ap, ignore_index=True) if all_ap else pd.DataFrame()
    df_cred = pd.concat(all_cred, ignore_index=True) if all_cred else pd.DataFrame()
else:
    st.stop()

# ============================================================
# Tab 1 – Visão Executiva
# ============================================================

with tabs[0]:
    st.markdown("<div class='ltx-title'>Resumo Executivo</div>", unsafe_allow_html=True)

    total_pis = df_outros["VL_PIS"].apply(to_float).sum() + df_c100["VL_PIS"].apply(to_float).sum()
    total_cof = df_outros["VL_COFINS"].apply(to_float).sum() + df_c100["VL_COFINS"].apply(to_float).sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.markdown("<div class='ltx-card'><div class='ltx-card-title'>Créditos de PIS</div>"
                  f"<div class='ltx-card-value'>{format_brl(total_pis)}</div></div>", unsafe_allow_html=True)

    col2.markdown("<div class='ltx-card'><div class='ltx-card-title'>Créditos de COFINS</div>"
                  f"<div class='ltx-card-value'>{format_brl(total_cof)}</div></div>", unsafe_allow_html=True)

# ============================================================
# Tab 2 – Detalhamento Técnico
# ============================================================

with tabs[1]:
    st.header("Detalhamento Técnico dos Créditos")

    st.subheader("Entradas – C100/C170")
    st.dataframe(df_c100)

    st.subheader("Outros Créditos – A100/A170, C500, D100, F100/F120")
    st.dataframe(df_outros)

# ============================================================
# Tab 3 – Gráficos
# ============================================================

with tabs[2]:
    st.header("Gráficos de composição dos créditos")

    def pie(tipo_label, tipos):
        df = resumo_tipo(df_outros, tipos, tipo_label)
        if df.empty:
            st.info(f"Sem dados para {tipo_label}.")
            return None

        df_plot = df[["GRUPO", "VL_PIS_NUM", "VL_COFINS_NUM"]].groupby("GRUPO").sum().reset_index()

        fig_pis = px.pie(df_plot, values="VL_PIS_NUM", names="GRUPO", hole=.4,
                         title=f"Composição dos créditos de PIS – {tipo_label}")
        fig_cof = px.pie(df_plot, values="VL_COFINS_NUM", names="GRUPO", hole=.4,
                         title=f"Composição dos créditos de COFINS – {tipo_label}")

        return fig_pis, fig_cof

    grupos = {
        "Serviços tomados": ["A100/A170"],
        "Energia elétrica": ["C500/C501/C505"],
        "Fretes": ["D100/D101", "D100/D105"],
        "Outras faturas": ["F100/F120"]
    }

    for label, tipos in grupos.items():
        st.subheader(label)
        result = pie(label, tipos)
        if result:
            fig_pis, fig_cof = result
            col1, col2 = st.columns(2)
            col1.plotly_chart(fig_pis, use_container_width=True)
            col2.plotly_chart(fig_cof, use_container_width=True)

# ============================================================
# Export Excel
# ============================================================

bio = io.BytesIO()
with pd.ExcelWriter(bio, engine="openpyxl") as writer:
    df_c100.to_excel(writer, sheet_name="C100_C170", index=False)
    df_outros.to_excel(writer, sheet_name="OUTROS_CREDITOS", index=False)
    df_ap.to_excel(writer, sheet_name="AP_PIS_M200", index=False)
    df_cred.to_excel(writer, sheet_name="CREDITOS_PIS_M105", index=False)

st.download_button(
    "Baixar Excel Consolidado",
    data=bio.getvalue(),
    file_name="Relatorio_EFD_PIS_COFINS_Lavoratory.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
