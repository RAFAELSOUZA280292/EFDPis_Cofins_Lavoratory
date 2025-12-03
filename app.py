"""
LavoraTAX Advisor – EFD PIS/COFINS
===================================

Este aplicativo Streamlit consolida créditos de PIS/COFINS a partir de um ou mais
arquivos EFD Contribuições (.txt ou .zip) e apresenta uma visão executiva e técnica.

Principais funcionalidades:

* Processamento de múltiplos SPEDs em cache para evitar estouros de memória.
* Tema claro e legível, adequado para apresentação a executivos.
* Cartões de resumo para créditos de PIS/COFINS, valores apurados (M200) e créditos declarados (M105).
* Tabelas de detalhamento por nota fiscal (C100/C170) e por outros documentos
  (serviços tomados, energia elétrica, fretes, F100/F120).
* Resumo de créditos por tipo de documento e por CFOP.
* Gráficos em pizza para visualizar a composição dos créditos de PIS e de COFINS.
* Exportação consolidada para Excel com várias abas.

O código a seguir deve ser salvo como ``app.py`` no mesmo diretório do ``parser_pis_cofins.py``.
"""

import io
import zipfile
from typing import List, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from parser_pis_cofins import parse_efd_piscofins


# -----------------------------------------------------------------------------
# Auxiliares
# -----------------------------------------------------------------------------

def to_float(value) -> float:
    """Converte uma string no formato brasileiro (1.234,56) em float.
    Se a conversão falhar, retorna 0.0."""
    try:
        s = str(value).strip()
        if s == "" or s is None:
            return 0.0
        # Remove separador de milhares e converte vírgula em ponto
        if s.count(",") == 1 and s.count(".") >= 1:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", ".")
        return float(s)
    except Exception:
        return 0.0


def resumo_tipo(
    df_outros: pd.DataFrame, tipos: List[str], label: str
) -> pd.DataFrame:
    """Agrupa os créditos de df_outros por competência e empresa para os tipos
    especificados. Retorna um DataFrame com as colunas:
    COMPETENCIA, EMPRESA, GRUPO, BASE_PIS, BASE_COFINS, PIS e COFINS.

    Se df_outros não for um DataFrame ou não contiver a coluna 'TIPO',
    retorna DataFrame vazio com as colunas esperadas.
    """
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

    # Converte campos monetários para float para somatório correto
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


# -----------------------------------------------------------------------------
# Leitura e parsing de arquivos com cache
# -----------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def parse_file(uploaded_file) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]:
    """Processa um arquivo .txt ou .zip da EFD PIS/COFINS usando o parser.

    A função aceita arquivos enviados pelo Streamlit (st.file_uploader) e
    detecta automaticamente se o arquivo é um .zip contendo .txt. O resultado
    é memorizado (cache) para evitar processamento repetido quando o mesmo
    arquivo é reenviado.

    Retorna: (df_c100, df_outros, df_ap_pis, df_cred_pis, competencia, empresa)
    """
    name = uploaded_file.name.lower()
    # Lê o conteúdo do arquivo em bytes
    data = uploaded_file.getvalue()  # obtém bytes
    # Extrai linhas de texto
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
            # fallback: tenta ler como texto bruto
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


# -----------------------------------------------------------------------------
# Configurações de página e tema
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="LavoraTAX Advisor – EFD PIS/COFINS",
    page_icon="📊",
    layout="wide",
)

# Tema claro com CSS customizado
st.markdown(
    """
    <style>
    /* Fundo claro e texto escuro */
    .stApp {
        background-color: #f7fafc;
        color: #1f2937;
        font-family: "Segoe UI", sans-serif;
    }

    /* Container principal com padding para não ficar sob a barra */
    .block-container {
        padding-top: 3rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1400px;
    }

    /* Títulos */
    .ltx-title {
        font-size: 2rem;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 0.25rem;
    }
    .ltx-subtitle {
        font-size: 1rem;
        color: #4a5568;
        margin-bottom: 1rem;
    }

    /* Cards de resumo */
    .ltx-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        min-height: 120px;
    }
    .ltx-card-title {
        font-size: 0.75rem;
        color: #718096;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }
    .ltx-card-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2d3748;
    }
    .ltx-card-sub {
        font-size: 0.75rem;
        color: #a0aec0;
        margin-top: 0.5rem;
    }

    /* Tabelas */
    .css-1oj2s4w.e16fv1kl0 { /* Ajusta altura de dataframes */
        max-height: 500px;
        overflow: auto;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Cabeçalho
# -----------------------------------------------------------------------------

st.markdown(
    """
    <div class="ltx-title">LavoraTAX Advisor • EFD PIS/COFINS</div>
    <div class="ltx-subtitle">Análise executiva e técnica de créditos de PIS/COFINS em EFD Contribuições.</div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Upload de arquivos
# -----------------------------------------------------------------------------

col_up, col_help = st.columns([2, 1])
with col_up:
    uploaded_files = st.file_uploader(
        "Carregue 1 ou mais arquivos EFD PIS/COFINS (.txt ou .zip)",
        type=["txt", "zip"],
        accept_multiple_files=True,
        help="Arraste e solte ou clique para selecionar arquivos. Pode enviar vários arquivos de diferentes empresas ou períodos.",
    )
with col_help:
    st.markdown("""
    #### Como usar
    - Faça o upload de 1 ou mais arquivos .txt ou .zip da EFD PIS/COFINS.
    - O sistema consolida créditos de entradas (NF-e, serviços, energia, fretes, etc.).
    - Gera visão executiva (cards e gráficos) e detalhamento técnico.
    - Permite exportar os resultados para Excel.
    """)

if not uploaded_files:
    st.warning("Envie ao menos um arquivo para iniciar a análise.")
    st.stop()

# -----------------------------------------------------------------------------
# Processamento dos arquivos com cache
# -----------------------------------------------------------------------------

dfs_c100: List[pd.DataFrame] = []
dfs_outros: List[pd.DataFrame] = []
dfs_ap: List[pd.DataFrame] = []
dfs_cred: List[pd.DataFrame] = []

for f in uploaded_files:
    try:
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
            df_ap.append(df_ap_file)
        if not df_cred_file.empty:
            dfs_cred.append(df_cred_file)
    except Exception as e:
        st.error(f"Erro ao processar {f.name}: {e}")

# Combina DataFrames
df_c100 = pd.concat(dfs_c100, ignore_index=True) if dfs_c100 else pd.DataFrame()
df_outros = pd.concat(dfs_outros, ignore_index=True) if dfs_outros else pd.DataFrame()
df_ap = pd.concat(dfs_ap, ignore_index=True) if dfs_ap else pd.DataFrame()
df_cred = pd.concat(dfs_cred, ignore_index=True) if dfs_cred else pd.DataFrame()

# -----------------------------------------------------------------------------
# Conversão numérica
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# Totais
# -----------------------------------------------------------------------------

total_pis = 0.0
total_cofins = 0.0
if not df_c100.empty:
    total_pis += df_c100["VL_PIS_NUM"].sum()
    total_cofins += df_c100["VL_COFINS_NUM"].sum()
if not df_outros.empty:
    total_pis += df_outros["VL_PIS_NUM"].sum()
    total_cofins += df_outros["VL_COFINS_NUM"].sum()

total_ap_pis = 0.0
if not df_ap.empty and "VL_TOT_CONT_REAL" in df_ap.columns:
    total_ap_pis = df_ap["VL_TOT_CONT_REAL"].sum()

total_cred_pis = 0.0
if not df_cred.empty and "VL_CRED" in df_cred.columns:
    total_cred_pis = df_cred["VL_CRED"].apply(to_float).sum()

# -----------------------------------------------------------------------------
# Resumos por tipo de documento
# -----------------------------------------------------------------------------

df_servicos = resumo_tipo(
    df_outros, ["A100/A170"], "Serviços tomados (A100/A170)"
)
df_energia = resumo_tipo(
    df_outros,
    ["C500/C501/C505"],
    "Energia elétrica (C500/C501/C505 - PIS em C501, COFINS em C505)",
)
df_fretes = resumo_tipo(
    df_outros, ["D100/D101", "D100/D105"], "Fretes / transporte (D100/D101/D105)"
)
df_out_fat = resumo_tipo(
    df_outros, ["F100/F120"], "Outras faturas (F100/F120)"
)

df_resumo_tipos = pd.concat(
    [df_servicos, df_energia, df_fretes, df_out_fat], ignore_index=True
) if any(
    not x.empty for x in [df_servicos, df_energia, df_fretes, df_out_fat]
) else pd.DataFrame()

# Resumo por CFOP
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

# -----------------------------------------------------------------------------
# Interface com abas
# -----------------------------------------------------------------------------

tab_exec, tab_det, tab_graf = st.tabs(
    ["Visão Executiva (CEO)", "Detalhamento Técnico", "Gráficos & Relatórios"]
)

# -------- Visão Executiva --------
with tab_exec:
    # Cartões resumidos
    cols_cards = st.columns(4)
    with cols_cards[0]:
        st.markdown(
            f"""
            <div class="ltx-card">
                <div class="ltx-card-title">Créditos de PIS identificados</div>
                <div class="ltx-card-value">{total_pis:,.2f}</div>
                <div class="ltx-card-sub">NF‑e + serviços + energia + fretes + demais docs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols_cards[1]:
        st.markdown(
            f"""
            <div class="ltx-card">
                <div class="ltx-card-title">Créditos de COFINS identificados</div>
                <div class="ltx-card-value">{total_cofins:,.2f}</div>
                <div class="ltx-card-sub">Mesma base dos créditos de PIS (documentos irmãos)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols_cards[2]:
        st.markdown(
            f"""
            <div class="ltx-card">
                <div class="ltx-card-title">PIS apurado (Bloco M200)</div>
                <div class="ltx-card-value">{total_ap_pis:,.2f}</div>
                <div class="ltx-card-sub">Somatório de VL_TOT_CONT_REAL</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols_cards[3]:
        st.markdown(
            f"""
            <div class="ltx-card">
                <div class="ltx-card-title">Créditos de PIS declarados (Bloco M105)</div>
                <div class="ltx-card-value">{total_cred_pis:,.2f}</div>
                <div class="ltx-card-sub">Somatório de VL_CRED (M105)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Resumo executivo por empresa/competência
    st.subheader("Resumo executivo por empresa / competência")
    if df_resumo_tipos.empty:
        st.info("Não há créditos consolidados para exibir.")
    else:
        # Combina competência + empresa para seleção
        combos = (
            df_resumo_tipos[["COMPETENCIA", "EMPRESA"]]
            .drop_duplicates()
            .sort_values(["COMPETENCIA", "EMPRESA"])
        )
        # Pandas pode alterar os nomes das colunas ao gerar tuplas; usamos name=None
        combo_options = [
            f"{row[0]} - {row[1]}" for row in combos.itertuples(index=False, name=None)
        ]
        if combo_options:
            selected = st.selectbox(
                "Selecione a competência e empresa para visualizar o resumo:",
                combo_options,
            )
            # Desempacota competência e empresa
            sel_comp, sel_emp = selected.split(" - ", 1)
            df_sel = df_resumo_tipos[
                (df_resumo_tipos["COMPETENCIA"] == sel_comp)
                & (df_resumo_tipos["EMPRESA"] == sel_emp)
            ]
            grupos = df_sel["GRUPO"].unique().tolist()
            grp = st.radio(
                "Escolha o tipo de documento:",
                grupos,
                horizontal=True,
            )
            df_grp = df_sel[df_sel["GRUPO"] == grp].copy()
            df_grp["TOTAL_PIS_COFINS"] = df_grp["PIS"] + df_grp["COFINS"]
            st.dataframe(
                df_grp[[
                    "COMPETENCIA",
                    "EMPRESA",
                    "GRUPO",
                    "BASE_PIS",
                    "BASE_COFINS",
                    "PIS",
                    "COFINS",
                    "TOTAL_PIS_COFINS",
                ]],
                use_container_width=True,
                height=220,
            )

# -------- Detalhamento Técnico --------
with tab_det:
    st.subheader("NF-e de entrada (C100/C170) – Detalhamento por item")
    if df_c100.empty:
        st.info("Nenhum registro C100/C170 de entrada foi identificado.")
    else:
        st.dataframe(df_c100, use_container_width=True, height=400)

    st.subheader("Demais documentos de crédito (A100/A170, C500, D100, F100/F120)")
    if df_outros.empty:
        st.info("Nenhum documento adicional de crédito foi identificado.")
    else:
        st.dataframe(df_outros, use_container_width=True, height=400)

    st.subheader("Resumo por CFOP (NF-e de entrada)")
    if df_cfop_summary.empty:
        st.info("Não há NF-e de entrada para agrupar por CFOP.")
    else:
        st.dataframe(df_cfop_summary, use_container_width=True, height=300)

# -------- Gráficos & Relatórios --------
with tab_graf:
    st.subheader("Gráficos de composição dos créditos")
    if df_resumo_tipos.empty:
        st.info("Não há dados consolidados para gerar gráficos.")
    else:
        df_plot = (
            df_resumo_tipos.groupby("GRUPO", as_index=False)[["PIS", "COFINS"]].sum()
        )
        col_pis, col_cof = st.columns(2)
        with col_pis:
            fig_pis = px.pie(
                df_plot,
                values="PIS",
                names="GRUPO",
                hole=0.5,
                title="Distribuição dos créditos de PIS por tipo de documento",
            )
            st.plotly_chart(fig_pis, use_container_width=True)
        with col_cof:
            fig_cof = px.pie(
                df_plot,
                values="COFINS",
                names="GRUPO",
                hole=0.5,
                title="Distribuição dos créditos de COFINS por tipo de documento",
            )
            st.plotly_chart(fig_cof, use_container_width=True)

    st.markdown("---")
    st.subheader("Exportar relatório consolidado (Excel)")
    # Exporta todas as tabelas para Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_c100.to_excel(writer, sheet_name="C100_C170", index=False)
        df_outros.to_excel(writer, sheet_name="OUTROS_CREDITOS", index=False)
        df_ap.to_excel(writer, sheet_name="AP_PIS_M200", index=False)
        df_cred.to_excel(writer, sheet_name="CREDITOS_PIS_M105", index=False)
        if not df_resumo_tipos.empty:
            temp = df_resumo_tipos.copy()
            temp["TOTAL_PIS_COFINS"] = temp["PIS"] + temp["COFINS"]
            temp.to_excel(writer, sheet_name="RESUMO_TIPOS", index=False)
        if not df_cfop_summary.empty:
            df_cfop_summary.to_excel(writer, sheet_name="RESUMO_CFOP", index=False)
    buffer.seek(0)
    st.download_button(
        label="📥 Baixar Excel consolidado",
        data=buffer,
        file_name="Relatorio_EFD_PIS_COFINS_LavoraTAX.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
