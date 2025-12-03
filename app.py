# app.py
"""
LavoraTAX Advisor - Dashboard de EFD PIS/COFINS

- Upload de múltiplos SPEDs (txt ou zip)
- Consolidação de créditos de PIS/COFINS
- Visão executiva para CEO (cards + gráficos de pizza)
- Detalhamento técnico
- Resumo de AP PIS (M200) e CREDITO PIS (M105)
"""

import io

import pandas as pd
import plotly.express as px
import streamlit as st

from parser_pis_cofins import load_efd_from_upload, parse_efd_piscofins


# ==============================
# CONFIGURAÇÃO DE PÁGINA / TEMA
# ==============================
st.set_page_config(
    page_title="LavoraTAX Advisor - EFD PIS/COFINS",
    page_icon="📊",
    layout="wide",
)


# ==============================
# CSS customizado
# ==============================
st.markdown(
    """
    <style>
    /* background geral */
    .stApp {
        background-color: #0f172a;
        color: #e5e7eb;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    /* títulos */
    h1, h2, h3 {
        color: #f9fafb;
    }

    /* cards de métricas */
    .ltx-card {
        background: #020617;
        border-radius: 18px;
        padding: 16px 18px;
        border: 1px solid #1f2937;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.55);
    }
    .ltx-card-title {
        font-size: 0.80rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }
    .ltx-card-value {
        font-size: 1.35rem;
        font-weight: 600;
        color: #f9fafb;
    }
    .ltx-card-sub {
        font-size: 0.78rem;
        color: #6b7280;
        margin-top: 2px;
    }

    /* tabelas */
    .dataframe tbody tr:nth-child(even) {
        background-color: #020617;
    }
    .dataframe tbody tr:nth-child(odd) {
        background-color: #020617;
    }
    .dataframe th {
        background-color: #020617 !important;
        color: #e5e7eb !important;
    }

    /* footer */
    .ltx-footer {
        margin-top: 32px;
        text-align: center;
        font-size: 0.75rem;
        color: #6b7280;
        padding-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================
# Helpers numéricos / formatação
# ==============================


def to_float(s) -> float:
    if s is None:
        return 0.0
    s = str(s).strip()
    if not s:
        return 0.0
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def format_brl(v: float) -> str:
    try:
        v = float(v)
    except Exception:
        return "R$ 0,00"
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def format_df_brl(df: pd.DataFrame, numeric_cols) -> pd.DataFrame:
    if df.empty:
        return df
    df_fmt = df.copy()
    for col in numeric_cols:
        if col in df_fmt.columns:
            df_fmt[col] = df_fmt[col].apply(format_brl)
    return df_fmt


def resumo_tipo(df_outros: pd.DataFrame, tipos, label: str) -> pd.DataFrame:
    df = df_outros[df_outros["TIPO"].isin(tipos)].copy()
    if df.empty:
        return pd.DataFrame(
            columns=[
                "COMPETENCIA",
                "EMPRESA",
                "GRUPO",
                "BASE_PIS",
                "BASE_COFINS",
                "PIS",
                "COFINS",
            ]
        )

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


# ==============================
# Cabeçalho
# ==============================
st.title("LavoraTAX Advisor – EFD PIS/COFINS")
st.caption(
    "Análise executiva e técnica de créditos de PIS/COFINS em EFD Contribuições."
)


# ==============================
# UPLOAD (MULTI-ARQUIVO)
# ==============================
col_upload, col_info = st.columns([2, 1.2])

with col_upload:
    uploaded_files = st.file_uploader(
        "Carregue 1 ou mais arquivos EFD PIS/COFINS (.txt ou .zip)",
        type=["txt", "zip"],
        accept_multiple_files=True,
    )

with col_info:
    st.markdown(
        """
        ##### Como usar
        1. Faça o upload de 1 ou mais arquivos `.txt` ou `.zip` da EFD PIS/COFINS  
        2. O sistema consolida **créditos de entradas** (NF-e, serviços, energia, fretes, etc.)  
        3. Gera:
           - Visão para CEO (cards + gráficos pizza)  
           - Detalhamento técnico  
           - Resumo **AP PIS (M200)** e **CREDITO PIS (M105)**  
           - Planilha Excel para trabalho em BI / auditoria
        """
    )

st.write("")


if not uploaded_files:
    st.info("📂 Aguardando upload de arquivos EFD PIS/COFINS...")
    st.stop()


# ==============================
# PROCESSAMENTO
# ==============================
dfs_c100 = []
dfs_outros = []
dfs_ap_pis = []
dfs_cred_pis = []

progress = st.progress(0.0)
status = st.empty()

for i, f in enumerate(uploaded_files, start=1):
    status.text(f"Processando arquivo {i}/{len(uploaded_files)}: {f.name}")
    try:
        lines = load_efd_from_upload(f)
        df_c100, df_outros, df_ap_pis, df_cred_pis, competencia, empresa = (
            parse_efd_piscofins(lines)
        )
    except Exception as e:
        st.error(f"Erro ao processar {f.name}: {e}")
        continue

    if not df_c100.empty:
        dfs_c100.append(df_c100)
    if not df_outros.empty:
        dfs_outros.append(df_outros)
    if not df_ap_pis.empty:
        dfs_ap_pis.append(df_ap_pis)
    if not df_cred_pis.empty:
        dfs_cred_pis.append(df_cred_pis)

    progress.progress(i / len(uploaded_files))

progress.progress(1.0)
status.empty()

if not dfs_c100 and not dfs_outros:
    st.error("Nenhum crédito de PIS/COFINS identificado nos arquivos enviados.")
    st.stop()

df_c100 = pd.concat(dfs_c100, ignore_index=True) if dfs_c100 else pd.DataFrame()
df_outros = pd.concat(dfs_outros, ignore_index=True) if dfs_outros else pd.DataFrame()
df_ap_pis = (
    pd.concat(dfs_ap_pis, ignore_index=True) if dfs_ap_pis else pd.DataFrame()
)
df_cred_pis = (
    pd.concat(dfs_cred_pis, ignore_index=True) if dfs_cred_pis else pd.DataFrame()
)


# ==============================
# Normalização numérica
# ==============================
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

# AP PIS / CRÉDITOS PIS (Bloco M)
M200_TOTAL_COL = "Valor Total da Contribuição a Recolher/Pagar no Período"
total_ap_pis = (
    df_ap_pis[M200_TOTAL_COL].sum() if M200_TOTAL_COL in df_ap_pis.columns else 0.0
)
total_cred_pis = df_cred_pis["VL_CRED"].sum() if "VL_CRED" in df_cred_pis.columns else 0.0


# ==============================
# Resumos por tipo
# ==============================
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
)


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


# ==============================
# LAYOUT EM ABAS (Clean / CEO friendly)
# ==============================
tab_exec, tab_det, tab_grafs = st.tabs(
    ["Visão Executiva (CEO)", "Detalhamento Técnico", "Gráficos & Relatórios"]
)

# --------- Visão Executiva (CEO) ----------
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
                <div class="ltx-card-sub">Mesma base de documentos de entrada</div>
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
                <div class="ltx-card-sub">Valor total da contribuição a recolher/pagar</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="ltx-card">
                <div class="ltx-card-title">Créditos de PIS (Bloco M105)</div>
                <div class="ltx-card-value">{format_brl(total_cred_pis)}</div>
                <div class="ltx-card-sub">Somatório de VL_CRED (M105)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Resumo por tipo de documento")
        if df_resumo_tipos.empty:
            st.info("Nenhum crédito por tipo de documento foi identificado.")
        else:
            df_res_exec = df_resumo_tipos.copy()
            df_res_exec["TOTAL_PIS_COFINS"] = (
                df_res_exec["PIS"] + df_res_exec["COFINS"]
            )
            df_res_exec = df_res_exec.sort_values(
                ["COMPETENCIA", "EMPRESA", "TOTAL_PIS_COFINS"], ascending=[True, True, False]
            )
            df_res_exec_fmt = format_df_brl(
                df_res_exec,
                ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS", "TOTAL_PIS_COFINS"],
            )
            st.dataframe(df_res_exec_fmt, use_container_width=True, height=360)

    with col_r:
        st.subheader("Resumo AP PIS x Créditos PIS")
        if df_ap_pis.empty and df_cred_pis.empty:
            st.info("Nenhuma informação de Bloco M200/M105 encontrada nos arquivos.")
        else:
            if not df_ap_pis.empty:
                if M200_TOTAL_COL in df_ap_pis.columns:
                    df_ap_res = (
                        df_ap_pis.groupby(["COMPETENCIA", "EMPRESA"], as_index=False)[
                            M200_TOTAL_COL
                        ]
                        .sum()
                        .rename(columns={M200_TOTAL_COL: "PIS_A_RECOLHER"})
                    )
                    df_ap_res_fmt = format_df_brl(df_ap_res, ["PIS_A_RECOLHER"])
                    st.markdown("**Apuração PIS (M200)**")
                    st.dataframe(df_ap_res_fmt, use_container_width=True, height=180)
            if not df_cred_pis.empty:
                df_cred_res = (
                    df_cred_pis.groupby("NAT_BC_CRED", as_index=False)["VL_CRED"]
                    .sum()
                    .sort_values("VL_CRED", ascending=False)
                )
                df_cred_res_fmt = format_df_brl(df_cred_res, ["VL_CRED"])
                st.markdown("**Créditos PIS por natureza da base (M105)**")
                st.dataframe(df_cred_res_fmt, use_container_width=True, height=180)


# --------- Detalhamento Técnico ----------
with tab_det:
    st.subheader("Detalhamento dos créditos de entrada")

    if not df_c100.empty:
        with st.expander("NF-e de entrada (C100/C170) – visão linha a linha", expanded=False):
            cols_fmt = ["VL_DOC", "VL_BC_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS"]
            df_c100_view = df_c100.copy()
            df_c100_view_fmt = format_df_brl(df_c100_view, cols_fmt)
            st.dataframe(df_c100_view_fmt, use_container_width=True, height=420)
    else:
        st.info("Nenhuma NF-e de entrada com crédito foi encontrada (C100/C170).")

    with st.expander("Serviços, energia, fretes e demais documentos", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Serviços tomados (A100/A170)**")
            if df_servicos.empty:
                st.write("—")
            else:
                st.dataframe(
                    format_df_brl(df_servicos, ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]),
                    use_container_width=True,
                    height=200,
                )

            st.markdown("**Fretes / transporte (D100/D101/D105)**")
            if df_fretes.empty:
                st.write("—")
            else:
                st.dataframe(
                    format_df_brl(df_fretes, ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]),
                    use_container_width=True,
                    height=200,
                )

        with col2:
            st.markdown("**Energia elétrica (C500/C501/C505)**")
            if df_energia.empty:
                st.write("—")
            else:
                st.dataframe(
                    format_df_brl(df_energia, ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]),
                    use_container_width=True,
                    height=200,
                )

            st.markdown("**Outras faturas / documentos (F100/F120)**")
            if df_out_fat.empty:
                st.write("—")
            else:
                st.dataframe(
                    format_df_brl(df_out_fat, ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]),
                    use_container_width=True,
                    height=200,
                )

    with st.expander("Resumo por CFOP (NF-e de entrada)", expanded=False):
        if df_cfop_summary.empty:
            st.info("Não foi possível montar o resumo por CFOP.")
        else:
            df_cfop_fmt = format_df_brl(
                df_cfop_summary, ["BASE_PIS", "BASE_COFINS", "PIS", "COFINS"]
            )
            st.dataframe(df_cfop_fmt, use_container_width=True, height=360)


# --------- Gráficos & Relatórios ----------
with tab_grafs:
    st.subheader("Gráficos de composição dos créditos")

    col_g1, col_g2 = st.columns(2)

    if not df_resumo_tipos.empty:
        df_pie_tipo = (
            df_resumo_tipos.groupby("GRUPO", as_index=False)[["PIS", "COFINS"]]
            .sum()
        )

        with col_g1:
            fig_pis = px.pie(
                df_pie_tipo,
                names="GRUPO",
                values="PIS",
                title="Composição dos créditos de PIS por tipo de documento",
                hole=0.35,
            )
            st.plotly_chart(fig_pis, use_container_width=True)

        with col_g2:
            fig_cof = px.pie(
                df_pie_tipo,
                names="GRUPO",
                values="COFINS",
                title="Composição dos créditos de COFINS por tipo de documento",
                hole=0.35,
            )
            st.plotly_chart(fig_cof, use_container_width=True)
    else:
        st.info("Sem dados consolidados por tipo de documento para gerar os gráficos.")

    st.markdown("---")
    st.subheader("Gráfico de PIS Apurado x Créditos PIS")

    if total_ap_pis == 0 and total_cred_pis == 0 and total_pis_credit == 0:
        st.info("Sem dados suficientes de apuração (M200/M105) para o gráfico comparativo.")
    else:
        df_pis_bal = pd.DataFrame(
            [
                {"Categoria": "PIS apurado (M200)", "Valor": total_ap_pis},
                {"Categoria": "Créditos PIS (M105)", "Valor": total_cred_pis},
                {
                    "Categoria": "Créditos PIS identificados nas entradas",
                    "Valor": total_pis_credit,
                },
            ]
        )
        # filtra zeros
        df_pis_bal = df_pis_bal[df_pis_bal["Valor"] > 0]
        if not df_pis_bal.empty:
            fig_bal = px.pie(
                df_pis_bal,
                names="Categoria",
                values="Valor",
                title="Relação entre PIS apurado, créditos declarados (M105) e créditos identificados",
                hole=0.3,
            )
            st.plotly_chart(fig_bal, use_container_width=True)

    st.markdown("---")
    st.subheader("Download de planilha Excel (todas as visões)")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        if not df_c100.empty:
            df_c100.to_excel(writer, sheet_name="C100_C170", index=False)
        if not df_outros.empty:
            df_outros.to_excel(writer, sheet_name="OUTROS_DOCUMENTOS", index=False)
        if not df_cfop_summary.empty:
            df_cfop_summary.to_excel(writer, sheet_name="RESUMO_CFOP", index=False)
        if not df_servicos.empty:
            df_servicos.to_excel(writer, sheet_name="RESUMO_SERVICOS", index=False)
        if not df_energia.empty:
            df_energia.to_excel(writer, sheet_name="RESUMO_ENERGIA", index=False)
        if not df_fretes.empty:
            df_fretes.to_excel(writer, sheet_name="RESUMO_FRETES", index=False)
        if not df_out_fat.empty:
            df_out_fat.to_excel(
                writer, sheet_name="RESUMO_OUTRAS_FATURAS", index=False
            )
        if not df_ap_pis.empty:
            df_ap_pis.to_excel(writer, sheet_name="AP_PIS_M200", index=False)
        if not df_cred_pis.empty:
            df_cred_pis.to_excel(writer, sheet_name="CREDITO_PIS_M105", index=False)

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
