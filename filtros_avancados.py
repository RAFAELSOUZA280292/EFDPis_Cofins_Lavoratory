"""
Filtros Avançados - Módulo para filtrar dados com operadores
Permite filtrar por múltiplos campos com operadores: =, ≠, <, >
"""

import pandas as pd
import streamlit as st


def aplicar_filtro_numerico(df, coluna, operador, valor):
    """
    Aplica filtro numérico em uma coluna
    
    Args:
        df: DataFrame
        coluna: Nome da coluna
        operador: '=', '≠', '<', '>'
        valor: Valor para comparação
        
    Returns:
        DataFrame filtrado
    """
    try:
        valor_float = float(valor)
        
        if operador == '=':
            return df[df[coluna] == valor_float]
        elif operador == '≠':
            return df[df[coluna] != valor_float]
        elif operador == '<':
            return df[df[coluna] < valor_float]
        elif operador == '>':
            return df[df[coluna] > valor_float]
        else:
            return df
    except:
        return df


def aplicar_filtro_texto(df, coluna, operador, valor):
    """
    Aplica filtro de texto em uma coluna
    
    Args:
        df: DataFrame
        coluna: Nome da coluna
        operador: '=' ou '≠'
        valor: Valor para comparação
        
    Returns:
        DataFrame filtrado
    """
    try:
        if operador == '=':
            return df[df[coluna].astype(str) == str(valor)]
        elif operador == '≠':
            return df[df[coluna].astype(str) != str(valor)]
        else:
            return df
    except:
        return df


def criar_painel_filtros(df):
    """
    Cria painel de filtros avançados na sidebar
    
    Args:
        df: DataFrame original
        
    Returns:
        DataFrame filtrado
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🔍 Filtros Avançados")
    
    df_filtrado = df.copy()
    filtros_aplicados = []
    
    # Expander para cada tipo de filtro
    with st.sidebar.expander("📄 Número do Documento", expanded=False):
        habilitar_num_doc = st.checkbox("Ativar filtro", key="enable_num_doc")
        if habilitar_num_doc:
            col1, col2 = st.columns([1, 2])
            with col1:
                operador_num_doc = st.selectbox(
                    "Op.",
                    ['=', '≠', '<', '>'],
                    key="op_num_doc"
                )
            with col2:
                valor_num_doc = st.text_input(
                    "Valor",
                    key="val_num_doc"
                )
            
            if valor_num_doc:
                df_filtrado = aplicar_filtro_texto(
                    df_filtrado, 
                    'NUM_DOC', 
                    operador_num_doc, 
                    valor_num_doc
                )
                filtros_aplicados.append(f"Número Doc {operador_num_doc} {valor_num_doc}")
    
    # Filtro Chave de Acesso
    with st.sidebar.expander("🔑 Chave de Acesso", expanded=False):
        habilitar_chave = st.checkbox("Ativar filtro", key="enable_chave")
        if habilitar_chave:
            col1, col2 = st.columns([1, 2])
            with col1:
                operador_chave = st.selectbox(
                    "Op.",
                    ['=', '≠'],
                    key="op_chave"
                )
            with col2:
                valor_chave = st.text_input(
                    "Valor",
                    key="val_chave",
                    max_chars=44
                )
            
            if valor_chave:
                df_filtrado = aplicar_filtro_texto(
                    df_filtrado, 
                    'CHV_NFE', 
                    operador_chave, 
                    valor_chave
                )
                filtros_aplicados.append(f"Chave {operador_chave} {valor_chave[:10]}...")
    
    # Filtro NCM
    with st.sidebar.expander("🏷️ NCM", expanded=False):
        habilitar_ncm = st.checkbox("Ativar filtro", key="enable_ncm")
        if habilitar_ncm:
            col1, col2 = st.columns([1, 2])
            with col1:
                operador_ncm = st.selectbox(
                    "Op.",
                    ['=', '≠'],
                    key="op_ncm"
                )
            with col2:
                # Lista de NCMs disponíveis
                ncms_disponiveis = sorted(df['NCM'].unique())
                valor_ncm = st.selectbox(
                    "Selecione",
                    ncms_disponiveis,
                    key="val_ncm"
                )
            
            if valor_ncm:
                df_filtrado = aplicar_filtro_texto(
                    df_filtrado, 
                    'NCM', 
                    operador_ncm, 
                    valor_ncm
                )
                filtros_aplicados.append(f"NCM {operador_ncm} {valor_ncm}")
    
    # Filtro Valor PIS
    with st.sidebar.expander("💰 Valor PIS", expanded=False):
        habilitar_pis = st.checkbox("Ativar filtro", key="enable_pis")
        if habilitar_pis:
            col1, col2 = st.columns([1, 2])
            with col1:
                operador_pis = st.selectbox(
                    "Op.",
                    ['=', '≠', '<', '>'],
                    key="op_pis"
                )
            with col2:
                valor_pis = st.number_input(
                    "Valor (R$)",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    key="val_pis"
                )
            
            if valor_pis > 0:
                df_filtrado = aplicar_filtro_numerico(
                    df_filtrado, 
                    'VL_PIS', 
                    operador_pis, 
                    valor_pis
                )
                filtros_aplicados.append(f"PIS {operador_pis} R$ {valor_pis:,.2f}")
    
    # Filtro Valor COFINS
    with st.sidebar.expander("💸 Valor COFINS", expanded=False):
        habilitar_cofins = st.checkbox("Ativar filtro", key="enable_cofins")
        if habilitar_cofins:
            col1, col2 = st.columns([1, 2])
            with col1:
                operador_cofins = st.selectbox(
                    "Op.",
                    ['=', '≠', '<', '>'],
                    key="op_cofins"
                )
            with col2:
                valor_cofins = st.number_input(
                    "Valor (R$)",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    key="val_cofins"
                )
            
            if valor_cofins > 0:
                df_filtrado = aplicar_filtro_numerico(
                    df_filtrado, 
                    'VL_COFINS', 
                    operador_cofins, 
                    valor_cofins
                )
                filtros_aplicados.append(f"COFINS {operador_cofins} R$ {valor_cofins:,.2f}")
    
    # Mostra filtros aplicados
    if filtros_aplicados:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ✅ Filtros Ativos:")
        for filtro in filtros_aplicados:
            st.sidebar.markdown(f"- {filtro}")
        
        st.sidebar.markdown(f"**Total de registros:** {len(df_filtrado)}")
        
        # Botão para limpar filtros
        if st.sidebar.button("🗑️ Limpar Todos os Filtros", key="clear_filters"):
            st.rerun()
    
    return df_filtrado


def exibir_resumo_filtros(df_original, df_filtrado):
    """
    Exibe resumo do impacto dos filtros
    
    Args:
        df_original: DataFrame original
        df_filtrado: DataFrame após filtros
    """
    if len(df_filtrado) < len(df_original):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📊 Total Original",
                f"{len(df_original):,}",
                delta=None
            )
        
        with col2:
            st.metric(
                "🔍 Após Filtros",
                f"{len(df_filtrado):,}",
                delta=f"-{len(df_original) - len(df_filtrado):,}",
                delta_color="inverse"
            )
        
        with col3:
            percentual = (len(df_filtrado) / len(df_original)) * 100
            st.metric(
                "📈 Percentual",
                f"{percentual:.1f}%",
                delta=None
            )
        
        st.markdown("---")
