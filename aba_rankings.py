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
    ranking = df_entrada.groupby(['COD_PART', 'NOME_PART', 'UF_PART']).agg({
        'VL_BC_PIS': 'sum',
        'VL_PIS': 'sum',
        'VL_BC_COFINS': 'sum',
        'VL_COFINS': 'sum',
        'VL_TOTAL': 'sum'
    }).reset_index()
    
    # Ordena por valor total decrescente
    ranking = ranking.sort_values('VL_TOTAL', ascending=False).head(TOP_N)
    
    # Renomeia colunas
    ranking.columns = ['Código', 'Fornecedor', 'UF', 'BC PIS', 'PIS', 'BC COFINS', 'COFINS', 'Total de Produtos']
    
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
    ranking = df_saida.groupby(['COD_PART', 'NOME_PART', 'UF_PART']).agg({
        'VL_BC_PIS': 'sum',
        'VL_PIS': 'sum',
        'VL_BC_COFINS': 'sum',
        'VL_COFINS': 'sum',
        'VL_TOTAL': 'sum'
    }).reset_index()
    
    # Ordena por valor total decrescente
    ranking = ranking.sort_values('VL_TOTAL', ascending=False).head(TOP_N)
    
    # Renomeia colunas
    ranking.columns = ['Código', 'Cliente', 'UF', 'BC PIS', 'PIS', 'BC COFINS', 'COFINS', 'Total de Produtos']
    
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


def criar_ranking_ncm_por_uf(df, tipo='Compras'):
    """
    Cria ranking de NCM por UF.
    
    Parâmetros:
        df (pd.DataFrame): DataFrame com notas fiscais
        tipo (str): 'Compras' ou 'Vendas'
    
    Retorna:
        pd.DataFrame: Ranking de NCM por UF
    """
    if df.empty or 'NCM' not in df.columns or 'UF_PART' not in df.columns:
        return pd.DataFrame()
    
    # Agrupa por NCM e UF
    ranking = df.groupby(['NCM', 'UF_PART']).agg({
        'VL_TOTAL': 'sum'
    }).reset_index()
    
    # Ordena por valor total decrescente
    ranking = ranking.sort_values('VL_TOTAL', ascending=False).head(TOP_N)
    
    # Renomeia colunas
    ranking.columns = ['NCM', 'UF', 'Total de Produtos']
    
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


def criar_grafico_uf(df_uf, titulo, cor='#1f77b4'):
    """
    Cria gráfico de barras horizontal por UF com gradiente de cores.
    
    Parâmetros:
        df_uf (pd.DataFrame): DataFrame com distribuição por UF
        titulo (str): Título do gráfico
        cor (str): Cor base para o gradiente
    
    Retorna:
        plotly.graph_objects.Figure: Gráfico
    """
    if df_uf.empty:
        return None
    
    # Pega top 10 UF
    df_top = df_uf.head(10).copy()
    
    # Inverte ordem para exibir maior no topo
    df_top = df_top.iloc[::-1]
    
    # Cria labels com percentual
    df_top['Label'] = df_top.apply(
        lambda row: f"{row['UF']} ({row['Percentual']:.1f}%)",
        axis=1
    )
    
    # Cria gráfico de barras
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_top['Total'],
        y=df_top['Label'],
        orientation='h',
        marker=dict(
            color=df_top['Total'],
            colorscale='Blues',
            showscale=False
        ),
        text=df_top['Total'].apply(lambda x: formatar_moeda_br(x)),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Valor: R$ %{x:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=titulo,
        xaxis_title='Valor (R$)',
        yaxis_title='',
        height=400,
        template='plotly_white',
        showlegend=False
    )
    
    fig.update_xaxes(tickformat=',.2f', tickprefix='R$ ')
    
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
                'Total de Produtos',
                f'Top {TOP_N} Fornecedores por Valor Total',
                cor='#1f77b4'
            )
            st.plotly_chart(fig_fornecedores, use_container_width=True)
            
            # Tabela
            st.markdown('#### 📋 Detalhamento')
            tabela_fornecedores = ranking_fornecedores.copy()
            
            # Formata valores
            tabela_fornecedores['BC PIS'] = tabela_fornecedores['BC PIS'].apply(formatar_moeda_br)
            tabela_fornecedores['PIS'] = tabela_fornecedores['PIS'].apply(formatar_moeda_br)
            tabela_fornecedores['BC COFINS'] = tabela_fornecedores['BC COFINS'].apply(formatar_moeda_br)
            tabela_fornecedores['COFINS'] = tabela_fornecedores['COFINS'].apply(formatar_moeda_br)
            tabela_fornecedores['Total de Produtos'] = tabela_fornecedores['Total de Produtos'].apply(formatar_moeda_br)
            
            # Adiciona linha de TOTAL
            total_row = pd.DataFrame([{
                'Código': '',
                'Fornecedor': 'TOTAL',
                'UF': '',
                'BC PIS': formatar_moeda_br(ranking_fornecedores['BC PIS'].sum()),
                'PIS': formatar_moeda_br(ranking_fornecedores['PIS'].sum()),
                'BC COFINS': formatar_moeda_br(ranking_fornecedores['BC COFINS'].sum()),
                'COFINS': formatar_moeda_br(ranking_fornecedores['COFINS'].sum()),
                'Total de Produtos': formatar_moeda_br(ranking_fornecedores['Total de Produtos'].sum())
            }])
            
            tabela_fornecedores = pd.concat([tabela_fornecedores, total_row], ignore_index=True)
            st.dataframe(tabela_fornecedores, use_container_width=True, hide_index=True)
        
        # Distribuição Geográfica (Fornecedores)
        st.markdown('#### 📍 Distribuição Geográfica - Fornecedores')
        distribuicao_uf_fornecedores = criar_distribuicao_uf(df_entrada, 'Fornecedor')
        
        if not distribuicao_uf_fornecedores.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Gráfico de barras por UF
                fig_uf_fornecedores = criar_grafico_uf(
                    distribuicao_uf_fornecedores,
                    'Top 10 UF - Compras',
                    cor='#1f77b4'
                )
                if fig_uf_fornecedores:
                    st.plotly_chart(fig_uf_fornecedores, use_container_width=True)
            
            with col2:
                # Tabela Top 10 UF
                st.markdown('**Detalhamento**')
                tabela_uf_fornecedores = distribuicao_uf_fornecedores.head(10).copy()
                tabela_uf_fornecedores['Total'] = tabela_uf_fornecedores['Total'].apply(formatar_moeda_br)
                tabela_uf_fornecedores['Percentual'] = tabela_uf_fornecedores['Percentual'].apply(lambda x: f'{x:.2f}%')
                st.dataframe(tabela_uf_fornecedores, use_container_width=True, hide_index=True, height=400)
        
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
        
        # Ranking de NCM por UF (Compras)
        st.markdown('#### 📍 Top NCM por UF - Compras')
        ranking_ncm_uf_compras = criar_ranking_ncm_por_uf(df_entrada, 'Compras')
        
        if not ranking_ncm_uf_compras.empty:
            # Tabela
            tabela_ncm_uf_compras = ranking_ncm_uf_compras.copy()
            tabela_ncm_uf_compras['Total de Produtos'] = tabela_ncm_uf_compras['Total de Produtos'].apply(formatar_moeda_br)
            st.dataframe(tabela_ncm_uf_compras, use_container_width=True, hide_index=True)
        
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
                'Total de Produtos',
                f'Top {TOP_N} Clientes por Valor Total',
                cor='#d62728'
            )
            st.plotly_chart(fig_clientes, use_container_width=True)
            
            # Tabela
            st.markdown('#### 📋 Detalhamento')
            tabela_clientes = ranking_clientes.copy()
            
            # Formata valores
            tabela_clientes['BC PIS'] = tabela_clientes['BC PIS'].apply(formatar_moeda_br)
            tabela_clientes['PIS'] = tabela_clientes['PIS'].apply(formatar_moeda_br)
            tabela_clientes['BC COFINS'] = tabela_clientes['BC COFINS'].apply(formatar_moeda_br)
            tabela_clientes['COFINS'] = tabela_clientes['COFINS'].apply(formatar_moeda_br)
            tabela_clientes['Total de Produtos'] = tabela_clientes['Total de Produtos'].apply(formatar_moeda_br)
            
            # Adiciona linha de TOTAL
            total_row = pd.DataFrame([{
                'Código': '',
                'Cliente': 'TOTAL',
                'UF': '',
                'BC PIS': formatar_moeda_br(ranking_clientes['BC PIS'].sum()),
                'PIS': formatar_moeda_br(ranking_clientes['PIS'].sum()),
                'BC COFINS': formatar_moeda_br(ranking_clientes['BC COFINS'].sum()),
                'COFINS': formatar_moeda_br(ranking_clientes['COFINS'].sum()),
                'Total de Produtos': formatar_moeda_br(ranking_clientes['Total de Produtos'].sum())
            }])
            
            tabela_clientes = pd.concat([tabela_clientes, total_row], ignore_index=True)
            st.dataframe(tabela_clientes, use_container_width=True, hide_index=True)
        
        # Distribuição Geográfica (Clientes)
        st.markdown('#### 📍 Distribuição Geográfica - Clientes')
        distribuicao_uf_clientes = criar_distribuicao_uf(df_saida, 'Cliente')
        
        if not distribuicao_uf_clientes.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Gráfico de barras por UF
                fig_uf_clientes = criar_grafico_uf(
                    distribuicao_uf_clientes,
                    'Top 10 UF - Vendas',
                    cor='#d62728'
                )
                if fig_uf_clientes:
                    st.plotly_chart(fig_uf_clientes, use_container_width=True)
            
            with col2:
                # Tabela Top 10 UF
                st.markdown('**Detalhamento**')
                tabela_uf_clientes = distribuicao_uf_clientes.head(10).copy()
                tabela_uf_clientes['Total'] = tabela_uf_clientes['Total'].apply(formatar_moeda_br)
                tabela_uf_clientes['Percentual'] = tabela_uf_clientes['Percentual'].apply(lambda x: f'{x:.2f}%')
                st.dataframe(tabela_uf_clientes, use_container_width=True, hide_index=True, height=400)
        
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
        
        # Ranking de NCM por UF (Vendas)
        st.markdown('#### 📍 Top NCM por UF - Vendas')
        ranking_ncm_uf_vendas = criar_ranking_ncm_por_uf(df_saida, 'Vendas')
        
        if not ranking_ncm_uf_vendas.empty:
            # Tabela
            tabela_ncm_uf_vendas = ranking_ncm_uf_vendas.copy()
            tabela_ncm_uf_vendas['Total de Produtos'] = tabela_ncm_uf_vendas['Total de Produtos'].apply(formatar_moeda_br)
            st.dataframe(tabela_ncm_uf_vendas, use_container_width=True, hide_index=True)
        
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
