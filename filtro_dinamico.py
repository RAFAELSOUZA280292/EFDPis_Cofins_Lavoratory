import streamlit as st
import pandas as pd
from typing import Dict, List, Any

# Mapeamento de tabelas e seus campos
TABELAS_DISPONIVEIS = {
    "C100/C170 - NF-e de Entrada": {
        "dataframe_key": "df_c100_cred",
        "campos": {
            "COMPETENCIA": "text",
            "EMPRESA": "text",
            "NOME_PART": "text",
            "NUM_DOC": "numeric",
            "CFOP": "text",
            "NCM": "text",
            "VL_BC_PIS": "numeric",
            "VL_PIS": "numeric",
            "VL_BC_COFINS": "numeric",
            "VL_COFINS": "numeric",
        }
    },
    "A100/A170 - Serviços Tomados": {
        "dataframe_key": "df_outros_cred",
        "campos": {
            "COMPETENCIA": "text",
            "EMPRESA": "text",
            "TIPO": "text",
            "VL_BC_PIS": "numeric",
            "VL_PIS": "numeric",
            "VL_BC_COFINS": "numeric",
            "VL_COFINS": "numeric",
        }
    },
    "D100/D105 - Fretes/Transporte": {
        "dataframe_key": "df_outros_cred",
        "campos": {
            "COMPETENCIA": "text",
            "EMPRESA": "text",
            "TIPO": "text",
            "VL_BC_PIS": "numeric",
            "VL_PIS": "numeric",
            "VL_BC_COFINS": "numeric",
            "VL_COFINS": "numeric",
        }
    },
    "F100/F120 - Outros Documentos": {
        "dataframe_key": "df_outros_cred",
        "campos": {
            "COMPETENCIA": "text",
            "EMPRESA": "text",
            "TIPO": "text",
            "VL_BC_PIS": "numeric",
            "VL_PIS": "numeric",
            "VL_BC_COFINS": "numeric",
            "VL_COFINS": "numeric",
        }
    },
    "Resumo por CFOP": {
        "dataframe_key": "df_cfop_summary",
        "campos": {
            "COMPETENCIA": "text",
            "EMPRESA": "text",
            "CFOP": "text",
            "BASE_PIS": "numeric",
            "PIS": "numeric",
            "BASE_COFINS": "numeric",
            "COFINS": "numeric",
        }
    }
}

# Operadores disponíveis por tipo de campo
OPERADORES = {
    "text": {
        "igual": "==",
        "diferente": "!=",
        "contém": "contains",
        "não contém": "not_contains",
        "vazio": "is_null",
        "não vazio": "is_not_null",
    },
    "numeric": {
        "igual": "==",
        "diferente": "!=",
        "maior que": ">",
        "menor que": "<",
        "maior ou igual": ">=",
        "menor ou igual": "<=",
        "entre": "between",
        "zero": "zero",
        "não zero": "not_zero",
    }
}

def aplicar_filtro(df: pd.DataFrame, campo: str, operador: str, valor: Any, tipo_campo: str) -> pd.DataFrame:
    """Aplica filtro ao dataframe baseado no operador e valor."""
    
    if tipo_campo == "numeric":
        # Converter coluna para float
        df[campo] = pd.to_numeric(df[campo].astype(str).str.replace(',', '.'), errors='coerce')
    
    if operador == "==":
        return df[df[campo] == valor]
    elif operador == "!=":
        return df[df[campo] != valor]
    elif operador == ">":
        return df[df[campo] > valor]
    elif operador == "<":
        return df[df[campo] < valor]
    elif operador == ">=":
        return df[df[campo] >= valor]
    elif operador == "<=":
        return df[df[campo] <= valor]
    elif operador == "between":
        val_min, val_max = valor
        return df[(df[campo] >= val_min) & (df[campo] <= val_max)]
    elif operador == "contains":
        return df[df[campo].astype(str).str.contains(valor, case=False, na=False)]
    elif operador == "not_contains":
        return df[~df[campo].astype(str).str.contains(valor, case=False, na=False)]
    elif operador == "is_null":
        return df[df[campo].isna() | (df[campo] == "")]
    elif operador == "is_not_null":
        return df[~(df[campo].isna() | (df[campo] == ""))]
    elif operador == "zero":
        return df[df[campo] == 0]
    elif operador == "not_zero":
        return df[df[campo] != 0]
    
    return df



def criar_busca_rapida(dataframes: Dict[str, pd.DataFrame]) -> None:
    """Cria interface de busca rápida por Chave, NCM ou Fornecedor."""
    
    st.markdown("<h3 class='subsection-title'>⚡ Busca Rápida</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # Busca por Chave de Acesso
    with col1:
        st.markdown("**🔑 Chave de Acesso**")
        chave = st.text_input("Digite a chave:", key="busca_chave", placeholder="Ex: 12092025")
        
        if chave and not dataframes["df_c100_cred"].empty:
            resultado = dataframes["df_c100_cred"][dataframes["df_c100_cred"]["CHV_NFE"].astype(str).str.contains(chave, case=False, na=False)]
            if not resultado.empty:
                st.success(f"✓ {len(resultado)} nota(s) encontrada(s)")
                with st.expander("Ver detalhes"):
                    st.dataframe(resultado[["CHV_NFE", "NOME_PART", "NUM_DOC", "VL_PIS", "VL_COFINS"]], use_container_width=True)
            else:
                st.warning("Nenhuma nota encontrada com essa chave")
    
    # Busca por NCM
    with col2:
        st.markdown("**📦 NCM**")
        if not dataframes["df_c100_cred"].emp    # A busca por NCM foi removida temporariamente para corrigir o KeyError.
    # A coluna NCM não está sendo populada corretamente pelo parser atual.
    with col2:
        st.markdown("**🔢 Busca por NCM (Desativada)**")
        st.info("A busca por NCM está temporariamente desativada.")    
    # Busca por Fornecedor
    with col3:
        st.markdown("**🏢 Fornecedor**")
        if not dataframes["df_c100_cred"].empty:
            fornecedores_disponiveis = sorted(dataframes["df_c100_cred"]["NOME_PART"].unique())
            fornecedor = st.selectbox("Selecione o fornecedor:", fornecedores_disponiveis, key="busca_fornecedor")
            
            if fornecedor:
                resultado = dataframes["df_c100_cred"][dataframes["df_c100_cred"]["NOME_PART"] == fornecedor]
                st.success(f"✓ {len(resultado)} nota(s) encontrada(s)")
                with st.expander("Ver detalhes"):
                    st.dataframe(resultado[["NOME_PART", "CHV_NFE", "NUM_DOC", "VL_PIS", "VL_COFINS"]], use_container_width=True)


def criar_filtro_dinamico(dataframes: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Cria interface de filtro dinâmico e retorna dataframe filtrado."""
    
    st.markdown("<h3 class='subsection-title'>🔍 Filtro Avançado de Dados</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        tabela_selecionada = st.selectbox(
            "📊 Selecione a Tabela:",
            list(TABELAS_DISPONIVEIS.keys()),
            key="filtro_tabela"
        )
    
    # Obter configuração da tabela
    config_tabela = TABELAS_DISPONIVEIS[tabela_selecionada]
    df_key = config_tabela["dataframe_key"]
    campos_disponiveis = config_tabela["campos"]
    
    # Verificar se o dataframe existe
    if df_key not in dataframes or dataframes[df_key].empty:
        st.warning(f"Nenhum dado disponível para {tabela_selecionada}")
        return pd.DataFrame()
    
    df_tabela = dataframes[df_key].copy()
    
    # Filtrar por tipo de tabela se necessário
    if tabela_selecionada == "A100/A170 - Serviços Tomados":
        df_tabela = df_tabela[df_tabela["TIPO"].str.contains("A100", na=False)]
    elif tabela_selecionada == "D100/D105 - Fretes/Transporte":
        df_tabela = df_tabela[df_tabela["TIPO"].str.contains("D100", na=False)]
    elif tabela_selecionada == "F100/F120 - Outros Documentos":
        df_tabela = df_tabela[df_tabela["TIPO"].str.contains("F100", na=False)]
    
    with col2:
        campo_selecionado = st.selectbox(
            "📋 Selecione o Campo:",
            list(campos_disponiveis.keys()),
            key="filtro_campo"
        )
    
    tipo_campo = campos_disponiveis[campo_selecionado]
    operadores_campo = OPERADORES[tipo_campo]
    
    with col3:
        operador_selecionado = st.selectbox(
            "⚙️ Operador:",
            list(operadores_campo.keys()),
            key="filtro_operador"
        )
    
    # Entrada de valor baseada no operador
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    col_val1, col_val2 = st.columns([2, 2])
    
    with col_val1:
        if operador_selecionado in ["vazio", "não vazio", "zero", "não zero"]:
            valor = None
            st.info(f"✓ Filtro '{operador_selecionado}' selecionado (sem valor necessário)")
        elif operador_selecionado == "entre":
            val_min = st.number_input("Valor Mínimo:", value=0.0, key="filtro_min")
            val_max = st.number_input("Valor Máximo:", value=1000.0, key="filtro_max")
            valor = (val_min, val_max)
        elif tipo_campo == "numeric":
            valor = st.number_input(f"Valor para {campo_selecionado}:", key="filtro_valor_num")
        else:
            valor = st.text_input(f"Valor para {campo_selecionado}:", key="filtro_valor_text")
    
    with col_val2:
        aplicar = st.button("🔎 Aplicar Filtro", use_container_width=True)
    
    # Aplicar filtro
    if aplicar:
        df_filtrado = aplicar_filtro(df_tabela, campo_selecionado, operadores_campo[operador_selecionado], valor, tipo_campo)
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown(f"<h4>Resultados: {len(df_filtrado)} registros encontrados</h4>", unsafe_allow_html=True)
        
        # Exibir tabela filtrada
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            height=400,
        )
        
        # Opção de download
        csv = df_filtrado.to_csv(index=False)
        st.download_button(
            label="📥 Baixar Resultados (CSV)",
            data=csv,
            file_name=f"filtro_{tabela_selecionada.replace('/', '_')}.csv",
            mime="text/csv"
        )
        
        return df_filtrado
    
    return pd.DataFrame()

