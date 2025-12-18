"""
================================================================================
ABA: RANKINGS - ANÁLISE DE FORNECEDORES E CLIENTES
================================================================================

Módulo para exibir rankings de fornecedores e clientes com análises por:
- Valor total
- UF (Unidade Federativa)
- NCM (Nomenclatura Comum do Mercosul)
- Produtos

Data de Criação: 16/12/2025
Autor: Sistema LavoraTax Advisor

================================================================================
GATILHOS DE MANUTENÇÃO:
================================================================================

1. ADICIONAR NOVOS RANKINGS:
   - Criar função criar_ranking_XXXX()
   - Adicionar chamada em exibir_aba_rankings()

2. MUDAR QUANTIDADE DE ITENS NO TOP:
   - Editar variável TOP_N (padrão: 10)

3. ALTERAR CORES DOS GRÁFICOS:
   - Editar parâmetro color= nos gráficos Plotly

================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# CONSTANTES
# ============================================================================

TOP_N = 10  # Quantidade de itens nos rankings

# Mapeamento de código IBGE para UF (primeiros 2 dígitos)
CODIGO_UF = {
    '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
    '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL',
    '28': 'SE', '29': 'BA', '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP', '41': 'PR',
    '42': 'SC', '43': 'RS', '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'
}


def formatar_moeda_br(valor):
    """Formata valor para padrão brasileiro: R$ 1.234,56"""
    if pd.isna(valor) or valor == 0:
        return 'R$ 0,00'
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def extrair_uf_codigo_municipio(cod_municipio):
    """
    Extrai UF do código do município IBGE (primeiros 2 dígitos).
    
    Parâmetros:
        cod_municipio (str): Código IBGE do município (7 dígitos)
    
    Retorna:
        str: Sigla da UF ou 'Não Identificado'
    """
    if not cod_municipio or len(str(cod_municipio)) < 2:
        return 'Não Identificado'
    
    cod_uf = str(cod_municipio)[:2]
    return CODIGO_UF.get(cod_uf, 'Não Identificado')


def criar_ranking_fornecedores(df_entrada):
    """
    Cria ranking de fornecedores por valor total.
    
    Parâmetros:
        df_entrada (pd.DataFrame): DataFrame com notas de entrada
    
    Retorna:
        pd.DataFrame: Ranking de fornecedores
    """
    if df_entrada.empty:
        return pd.DataFrame()
    
    # Agrupa por fornecedor
    ranking = df_entrada.groupby(['COD_PART', 'NOME_PART']).agg({
        'VL_PIS': 'sum',
        'VL_COFINS': 'sum',
        'VL_TOTAL': 'sum'
    }).reset_index()
    
    # Ordena por valor total decrescente
    ranking = ranking.sort_values('VL_TOTAL', ascending=False).head(TOP_N)
    
    # Renomeia colunas
    ranking.columns = ['Código', 'Fornecedor', 'PIS', 'COFINS', 'Total']
    
    return ranking


def criar_ranking_clientes(df_saida):
    """
    Cria ranking de clientes por valor total.
    
    Parâmetros:
        df_saida (pd.DataFrame): DataFrame com notas de saída
    
    Retorna:
        pd.DataFrame: Ranking de clientes
    """
    if df_saida.empty:
        return pd.DataFrame()
    
    # Agrupa por cliente
    ranking = df_saida.groupby(['COD_PART', 'NOME_PART']).agg({
        'VL_PIS': 'sum',
        'VL_COFINS': 'sum',
        'VL_TOTAL': 'sum'
    }).reset_index()
    
    # Ordena por valor total decrescente
    ranking = ranking.sort_values('VL_TOTAL', ascending=False).head(TOP_N)
    
    # Renomeia colunas
    ranking.columns = ['Código', 'Cliente', 'PIS', 'COFINS', 'Total']
    
    return ranking


def criar_distribuicao_uf(df, tipo='Fornecedor'):
    """
    Cria distribuição de valores por UF.
    
    Parâmetros:
        df (pd.DataFrame): DataFrame com notas fiscais
        tipo (str): 'Fornecedor' ou 'Cliente'
    
    Retorna:
        pd.DataFrame: Distribuição por UF
    """
    if df.empty or 'UF_PART' not in df.columns:
        return pd.DataFrame()
    
    # Agrupa por UF
    distribuicao = df.groupby('UF_PART').agg({
        'VL_TOTAL': 'sum'
    }).reset_index()
    
    # Calcula percentual
    total_geral = distribuicao['VL_TOTAL'].sum()
    distribuicao['PERCENTUAL'] = (distribuicao['VL_TOTAL'] / total_geral * 100).round(2)
    
    # Ordena por valor total decrescente
    distribuicao = distribuicao.sort_values('VL_TOTAL', ascending=False)
    
    # Renomeia colunas
    distribuicao.columns = ['UF', 'Total', 'Percentual']
    
    return distribuicao


def criar_ranking_ncm(df, tipo='Compras'):
    """
    Cria ranking de NCM por valor total.
    
    Parâmetros:
        df (pd.DataFrame): DataFrame com notas fiscais
        tipo (str): 'Compras' ou 'Vendas'
    
    Retorna:
        pd.DataFrame: Ranking de NCM
    """
    if df.empty or 'NCM' not in df.columns:
        return pd.DataFrame()
    
    # Agrupa por NCM
    ranking = df.groupby('NCM').agg({
        'VL_TOTAL': 'sum'
    }).reset_index()
    
    # Ordena por valor total decrescente
    ranking = ranking.sort_values('VL_TOTAL', ascending=False).head(TOP_N)
    
    # Renomeia colunas
    ranking.columns = ['NCM', 'Total']
    
    return ranking


def criar_ranking_produtos(df, tipo='Compras'):
    """
    Cria ranking de produtos por valor total.
    
    Parâmetros:
        df (pd.DataFrame): DataFrame com notas fiscais
        tipo (str): 'Compras' ou 'Vendas'
    
    Retorna:
        pd.DataFrame: Ranking de produtos
    """
    if df.empty or 'DESCR_ITEM' not in df.columns:
        return pd.DataFrame()
    
    # Agrupa por produto
    ranking = df.groupby(['COD_ITEM', 'DESCR_ITEM']).agg({
        'VL_TOTAL': 'sum'
    }).reset_index()
    
    # Ordena por valor total decrescente
    ranking = ranking.sort_values('VL_TOTAL', ascending=False).head(TOP_N)
    
    # Renomeia colunas
    ranking.columns = ['Código', 'Produto', 'Total']
    
    return ranking


def criar_mapa_brasil(df_uf, titulo):
    """
    Cria mapa coroplético do Brasil.
    
    Parâmetros:
        df_uf (pd.DataFrame): DataFrame com distribuição por UF
        titulo (str): Título do mapa
    
    Retorna:
        plotly.graph_objects.Figure: Mapa
    """
    if df_uf.empty:
        return None
    
    # Cria mapa coroplético
    fig = px.choropleth(
        df_uf,
        locations='UF',
        locationmode='USA-states',  # Usar modo genérico
        color='Total',
        hover_name='UF',
        hover_data={
            'Total': ':,.2f',
            'Percentual': ':.2f'
        },
        color_continuous_scale='Blues',
        labels={'Total': 'Valor (R$)', 'Percentual': '% do Total'},
        title=titulo
    )
    
    # Ajusta layout para focar no Brasil
    fig.update_geos(
        scope='south america',
        center={'lat': -14, 'lon': -55},
        projection_scale=3.5,
        visible=False
    )
    
    fig.update_layout(
        height=500,
        template='plotly_white'
    )
    
    return fig


def criar_grafico_barras_horizontal(df, coluna_label, coluna_valor, titulo, cor='#1f77b4'):
    """
    Cria gráfico de barras horizontal.
    
    Parâmetros:
        df (pd.DataFrame): DataFrame com dados
        coluna_label (str): Nome da coluna de labels
        coluna_valor (str): Nome da coluna de valores
        titulo (str): Título do gráfico
        cor (str): Cor das barras
    
    Retorna:
        plotly.graph_objects.Figure: Gráfico
    """
    if df.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df[coluna_valor],
        y=df[coluna_label],
        orientation='h',
        marker=dict(color=cor),
        text=df[coluna_valor].apply(lambda x: formatar_moeda_br(x)),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Valor: R$ %{x:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=titulo,
        xaxis_title='Valor (R$)',
        yaxis_title='',
        height=400,
        template='plotly_white',
        yaxis={'categoryorder': 'total ascending'}
    )
    
    fig.update_xaxes(tickformat=',.2f', tickprefix='R$ ')
    
    return fig


def exibir_aba_rankings(df_entrada, df_saida):
    """
    Exibe a aba de Rankings com análises de fornecedores e clientes.
    
    Parâmetros:
        df_entrada (pd.DataFrame): DataFrame com notas de entrada
        df_saida (pd.DataFrame): DataFrame com notas de saída
    """
    st.header('🏆 Rankings - Fornecedores e Clientes')
    st.markdown('**Análise dos principais fornecedores, clientes, NCM e produtos**')
    
    # ========================================================================
    # SEÇÃO 1: RANKING DE FORNECEDORES
    # ========================================================================
    
    st.markdown('---')
    st.subheader('📥 Ranking de Fornecedores (Entrada)')
    
    if df_entrada.empty:
        st.info('👆 Nenhuma nota de entrada encontrada.')
    else:
        # Ranking de fornecedores
        ranking_fornecedores = criar_ranking_fornecedores(df_entrada)
        
        if not ranking_fornecedores.empty:
            # Gráfico
            fig_fornecedores = criar_grafico_barras_horizontal(
                ranking_fornecedores,
                'Fornecedor',
                'Total',
                f'Top {TOP_N} Fornecedores por Valor Total',
                cor='#1f77b4'
            )
            st.plotly_chart(fig_fornecedores, use_container_width=True)
            
            # Tabela
            st.markdown('#### 📋 Detalhamento')
            tabela_fornecedores = ranking_fornecedores.copy()
            tabela_fornecedores['PIS'] = tabela_fornecedores['PIS'].apply(formatar_moeda_br)
            tabela_fornecedores['COFINS'] = tabela_fornecedores['COFINS'].apply(formatar_moeda_br)
            tabela_fornecedores['Total'] = tabela_fornecedores['Total'].apply(formatar_moeda_br)
            st.dataframe(tabela_fornecedores, use_container_width=True, hide_index=True)
        
        # Distribuição Geográfica (Fornecedores)
        st.markdown('#### 📍 Distribuição Geográfica - Fornecedores')
        distribuicao_uf_fornecedores = criar_distribuicao_uf(df_entrada, 'Fornecedor')
        
        if not distribuicao_uf_fornecedores.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Mapa do Brasil
                fig_mapa_fornecedores = criar_mapa_brasil(
                    distribuicao_uf_fornecedores,
                    'Distribuição de Compras por UF'
                )
                if fig_mapa_fornecedores:
                    st.plotly_chart(fig_mapa_fornecedores, use_container_width=True)
            
            with col2:
                # Tabela Top 10 UF
                st.markdown('**Top 10 UF**')
                tabela_uf_fornecedores = distribuicao_uf_fornecedores.head(10).copy()
                tabela_uf_fornecedores['Total'] = tabela_uf_fornecedores['Total'].apply(formatar_moeda_br)
                tabela_uf_fornecedores['Percentual'] = tabela_uf_fornecedores['Percentual'].apply(lambda x: f'{x:.2f}%')
                st.dataframe(tabela_uf_fornecedores, use_container_width=True, hide_index=True, height=500)
        
        # Ranking de NCM (Compras)
        st.markdown('#### 📦 Top NCM - Compras')
        ranking_ncm_compras = criar_ranking_ncm(df_entrada, 'Compras')
        
        if not ranking_ncm_compras.empty:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Gráfico
                fig_ncm_compras = criar_grafico_barras_horizontal(
                    ranking_ncm_compras,
                    'NCM',
                    'Total',
                    f'Top {TOP_N} NCM - Compras',
                    cor='#2ca02c'
                )
                st.plotly_chart(fig_ncm_compras, use_container_width=True)
            
            with col2:
                # Tabela
                tabela_ncm_compras = ranking_ncm_compras.copy()
                tabela_ncm_compras['Total'] = tabela_ncm_compras['Total'].apply(formatar_moeda_br)
                st.dataframe(tabela_ncm_compras, use_container_width=True, hide_index=True, height=400)
        
        # Ranking de Produtos (Compras)
        st.markdown('#### 🛒 Top Produtos - Compras')
        ranking_produtos_compras = criar_ranking_produtos(df_entrada, 'Compras')
        
        if not ranking_produtos_compras.empty:
            # Gráfico
            fig_produtos_compras = criar_grafico_barras_horizontal(
                ranking_produtos_compras,
                'Produto',
                'Total',
                f'Top {TOP_N} Produtos - Compras',
                cor='#ff7f0e'
            )
            st.plotly_chart(fig_produtos_compras, use_container_width=True)
            
            # Tabela
            tabela_produtos_compras = ranking_produtos_compras.copy()
            tabela_produtos_compras['Total'] = tabela_produtos_compras['Total'].apply(formatar_moeda_br)
            st.dataframe(tabela_produtos_compras, use_container_width=True, hide_index=True)
    
    # ========================================================================
    # SEÇÃO 2: RANKING DE CLIENTES
    # ========================================================================
    
    st.markdown('---')
    st.subheader('📤 Ranking de Clientes (Saída)')
    
    if df_saida.empty:
        st.info('👆 Nenhuma nota de saída encontrada.')
    else:
        # Ranking de clientes
        ranking_clientes = criar_ranking_clientes(df_saida)
        
        if not ranking_clientes.empty:
            # Gráfico
            fig_clientes = criar_grafico_barras_horizontal(
                ranking_clientes,
                'Cliente',
                'Total',
                f'Top {TOP_N} Clientes por Valor Total',
                cor='#d62728'
            )
            st.plotly_chart(fig_clientes, use_container_width=True)
            
            # Tabela
            st.markdown('#### 📋 Detalhamento')
            tabela_clientes = ranking_clientes.copy()
            tabela_clientes['PIS'] = tabela_clientes['PIS'].apply(formatar_moeda_br)
            tabela_clientes['COFINS'] = tabela_clientes['COFINS'].apply(formatar_moeda_br)
            tabela_clientes['Total'] = tabela_clientes['Total'].apply(formatar_moeda_br)
            st.dataframe(tabela_clientes, use_container_width=True, hide_index=True)
        
        # Distribuição Geográfica (Clientes)
        st.markdown('#### 📍 Distribuição Geográfica - Clientes')
        distribuicao_uf_clientes = criar_distribuicao_uf(df_saida, 'Cliente')
        
        if not distribuicao_uf_clientes.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Mapa do Brasil
                fig_mapa_clientes = criar_mapa_brasil(
                    distribuicao_uf_clientes,
                    'Distribuição de Vendas por UF'
                )
                if fig_mapa_clientes:
                    st.plotly_chart(fig_mapa_clientes, use_container_width=True)
            
            with col2:
                # Tabela Top 10 UF
                st.markdown('**Top 10 UF**')
                tabela_uf_clientes = distribuicao_uf_clientes.head(10).copy()
                tabela_uf_clientes['Total'] = tabela_uf_clientes['Total'].apply(formatar_moeda_br)
                tabela_uf_clientes['Percentual'] = tabela_uf_clientes['Percentual'].apply(lambda x: f'{x:.2f}%')
                st.dataframe(tabela_uf_clientes, use_container_width=True, hide_index=True, height=500)
        
        # Ranking de NCM (Vendas)
        st.markdown('#### 📦 Top NCM - Vendas')
        ranking_ncm_vendas = criar_ranking_ncm(df_saida, 'Vendas')
        
        if not ranking_ncm_vendas.empty:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Gráfico
                fig_ncm_vendas = criar_grafico_barras_horizontal(
                    ranking_ncm_vendas,
                    'NCM',
                    'Total',
                    f'Top {TOP_N} NCM - Vendas',
                    cor='#9467bd'
                )
                st.plotly_chart(fig_ncm_vendas, use_container_width=True)
            
            with col2:
                # Tabela
                tabela_ncm_vendas = ranking_ncm_vendas.copy()
                tabela_ncm_vendas['Total'] = tabela_ncm_vendas['Total'].apply(formatar_moeda_br)
                st.dataframe(tabela_ncm_vendas, use_container_width=True, hide_index=True, height=400)
        
        # Ranking de Produtos (Vendas)
        st.markdown('#### 🛒 Top Produtos - Vendas')
        ranking_produtos_vendas = criar_ranking_produtos(df_saida, 'Vendas')
        
        if not ranking_produtos_vendas.empty:
            # Gráfico
            fig_produtos_vendas = criar_grafico_barras_horizontal(
                ranking_produtos_vendas,
                'Produto',
                'Total',
                f'Top {TOP_N} Produtos - Vendas',
                cor='#8c564b'
            )
            st.plotly_chart(fig_produtos_vendas, use_container_width=True)
            
            # Tabela
            tabela_produtos_vendas = ranking_produtos_vendas.copy()
            tabela_produtos_vendas['Total'] = tabela_produtos_vendas['Total'].apply(formatar_moeda_br)
            st.dataframe(tabela_produtos_vendas, use_container_width=True, hide_index=True)


# ============================================================================
# APRENDIZADOS E OBSERVAÇÕES
# ============================================================================

"""
APRENDIZADO 1: RANKINGS
- Top 10 por padrão (ajustável via TOP_N)
- Ordenação decrescente por valor total

APRENDIZADO 2: CORES DOS GRÁFICOS
- Fornecedores: Azul (#1f77b4)
- Clientes: Vermelho (#d62728)
- NCM Compras: Verde (#2ca02c)
- NCM Vendas: Roxo (#9467bd)
- Produtos Compras: Laranja (#ff7f0e)
- Produtos Vendas: Marrom (#8c564b)

APRENDIZADO 3: UF
- Extrair do código do município IBGE (primeiros 2 dígitos)
- Implementar quando houver campo COD_MUN disponível
"""

# ============================================================================
# FIM DO ARQUIVO
# ============================================================================
