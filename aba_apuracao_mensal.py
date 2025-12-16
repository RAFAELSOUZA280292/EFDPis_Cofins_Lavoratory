"""
================================================================================
ABA: PIS/COFINS APURADO - ANÁLISE MENSAL
================================================================================

Módulo para exibir evolução mensal dos valores de PIS e COFINS a recolher.

Baseado nos registros:
- M210: Receitas PIS
- M610: Receitas COFINS

Data de Criação: 16/12/2025
Autor: Sistema LavoraTax Advisor

================================================================================
GATILHOS DE MANUTENÇÃO:
================================================================================

1. ADICIONAR NOVOS CAMPOS:
   - Editar função criar_tabela_mensal()
   - Adicionar campo no DataFrame

2. MUDAR GRÁFICO:
   - Editar função criar_grafico_evolucao()
   - Ajustar cores, títulos, etc.

3. ALTERAR ORDEM DOS MESES:
   - Editar ORDEM_MESES abaixo
   - Manter ordem alfabética (Jan, Fev, Mar...)

================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ============================================================================
# CONSTANTES
# ============================================================================

# Ordem alfabética dos meses (Jan, Fev, Mar...)
ORDEM_MESES = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

# Mapeamento de número para nome do mês
MESES_DICT = {
    '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março',
    '04': 'Abril', '05': 'Maio', '06': 'Junho',
    '07': 'Julho', '08': 'Agosto', '09': 'Setembro',
    '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
}


def formatar_moeda_br(valor):
    """
    Formata valor para padrão brasileiro: R$ 1.234,56
    
    GATILHO DE MANUTENÇÃO:
    - Sempre usar este formato em todo o sistema
    - Ponto para milhar, vírgula para decimal
    """
    if pd.isna(valor) or valor == 0:
        return 'R$ 0,00'
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def extrair_mes_competencia(competencia):
    """
    Extrai o mês da competência no formato MMAAAA.
    
    Parâmetros:
        competencia (str): Competência no formato '012025' (Janeiro/2025)
    
    Retorna:
        str: Nome do mês ('Janeiro', 'Fevereiro', etc.)
    
    GATILHO DE MANUTENÇÃO:
    - Se formato da competência mudar, ajustar aqui
    """
    if not competencia or len(str(competencia)) < 2:
        return 'Indefinido'
    
    mes_num = str(competencia)[:2]
    return MESES_DICT.get(mes_num, 'Indefinido')


def criar_tabela_mensal(dados_m):
    """
    Cria tabela mensal de PIS/COFINS apurado.
    
    Parâmetros:
        dados_m (dict): Dicionário com DataFrames dos registros M
    
    Retorna:
        pd.DataFrame: Tabela com colunas:
            - Competência
            - PIS Apurado
            - COFINS Apurado
            - Total
    
    GATILHO DE MANUTENÇÃO:
    - Para adicionar campos, incluir na agregação abaixo
    - Para mudar cálculo, ajustar a lógica de soma
    """
    # Extrair DataFrames
    df_rec_pis = dados_m.get('df_rec_pis', pd.DataFrame())
    df_rec_cof = dados_m.get('df_rec_cof', pd.DataFrame())
    
    # Verificar se DataFrames estão vazios
    if df_rec_pis.empty and df_rec_cof.empty:
        return pd.DataFrame(columns=['Competência', 'PIS Apurado', 'COFINS Apurado', 'Total'])
    
    # Processar PIS (M210)
    if not df_rec_pis.empty and 'COMPETENCIA' in df_rec_pis.columns:
        df_rec_pis['MES'] = df_rec_pis['COMPETENCIA'].apply(extrair_mes_competencia)
        # Somar VL_CONT_PER (Valor da Contribuição no Período)
        pis_mensal = df_rec_pis.groupby('MES')['VL_CONT_PER'].sum().reset_index()
        pis_mensal.columns = ['Competência', 'PIS Apurado']
    else:
        pis_mensal = pd.DataFrame(columns=['Competência', 'PIS Apurado'])
    
    # Processar COFINS (M610)
    if not df_rec_cof.empty and 'COMPETENCIA' in df_rec_cof.columns:
        df_rec_cof['MES'] = df_rec_cof['COMPETENCIA'].apply(extrair_mes_competencia)
        # Somar VL_CONT_PER (Valor da Contribuição no Período)
        cofins_mensal = df_rec_cof.groupby('MES')['VL_CONT_PER'].sum().reset_index()
        cofins_mensal.columns = ['Competência', 'COFINS Apurado']
    else:
        cofins_mensal = pd.DataFrame(columns=['Competência', 'COFINS Apurado'])
    
    # Merge PIS e COFINS
    if not pis_mensal.empty and not cofins_mensal.empty:
        tabela = pd.merge(pis_mensal, cofins_mensal, on='Competência', how='outer')
    elif not pis_mensal.empty:
        tabela = pis_mensal.copy()
        tabela['COFINS Apurado'] = 0
    elif not cofins_mensal.empty:
        tabela = cofins_mensal.copy()
        tabela['PIS Apurado'] = 0
    else:
        return pd.DataFrame(columns=['Competência', 'PIS Apurado', 'COFINS Apurado', 'Total'])
    
    # Preencher NaN com 0
    tabela['PIS Apurado'] = tabela['PIS Apurado'].fillna(0)
    tabela['COFINS Apurado'] = tabela['COFINS Apurado'].fillna(0)
    
    # Calcular Total
    tabela['Total'] = tabela['PIS Apurado'] + tabela['COFINS Apurado']
    
    # Ordenar por ordem alfabética dos meses
    tabela['ORDEM'] = tabela['Competência'].apply(lambda x: ORDEM_MESES.index(x) if x in ORDEM_MESES else 99)
    tabela = tabela.sort_values('ORDEM').drop('ORDEM', axis=1)
    
    return tabela


def criar_grafico_evolucao(tabela):
    """
    Cria gráfico de linha mostrando evolução mensal de PIS, COFINS e Total.
    
    Parâmetros:
        tabela (pd.DataFrame): Tabela mensal criada por criar_tabela_mensal()
    
    Retorna:
        plotly.graph_objects.Figure: Gráfico de evolução
    
    GATILHO DE MANUTENÇÃO:
    - Para mudar cores, ajustar parâmetro 'line=dict(color=...)'
    - Para adicionar linhas, adicionar fig.add_trace()
    """
    fig = go.Figure()
    
    # Linha PIS (Azul)
    fig.add_trace(go.Scatter(
        x=tabela['Competência'],
        y=tabela['PIS Apurado'],
        mode='lines+markers',
        name='PIS',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>PIS: R$ %{y:,.2f}<extra></extra>'
    ))
    
    # Linha COFINS (Vermelho)
    fig.add_trace(go.Scatter(
        x=tabela['Competência'],
        y=tabela['COFINS Apurado'],
        mode='lines+markers',
        name='COFINS',
        line=dict(color='#d62728', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>COFINS: R$ %{y:,.2f}<extra></extra>'
    ))
    
    # Linha Total (Verde)
    fig.add_trace(go.Scatter(
        x=tabela['Competência'],
        y=tabela['Total'],
        mode='lines+markers',
        name='Total',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Total: R$ %{y:,.2f}<extra></extra>'
    ))
    
    # Layout
    fig.update_layout(
        title='Evolução Mensal de PIS/COFINS Apurado',
        xaxis_title='Competência',
        yaxis_title='Valor (R$)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    # Formatação do eixo Y (valores em R$)
    fig.update_yaxes(tickformat=',.2f', tickprefix='R$ ')
    
    return fig


def exibir_aba_apuracao_mensal(dados_m):
    """
    Exibe a aba de PIS/COFINS Apurado com tabela e gráfico.
    
    Parâmetros:
        dados_m (dict): Dicionário com DataFrames dos registros M
    
    GATILHO DE MANUTENÇÃO:
    - Esta é a função principal chamada pelo app.py
    - Para adicionar seções, adicionar st.subheader() e conteúdo
    """
    st.header('💰 PIS/COFINS Apurado')
    st.markdown('**Análise Mensal dos Valores a Recolher (M210 e M610)**')
    
    # Criar tabela mensal
    tabela = criar_tabela_mensal(dados_m)
    
    if tabela.empty:
        st.warning('⚠️ Nenhum dado de apuração mensal encontrado nos registros M210 e M610.')
        return
    
    # Exibir resumo
    total_pis = tabela['PIS Apurado'].sum()
    total_cofins = tabela['COFINS Apurado'].sum()
    total_geral = tabela['Total'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('💵 Total PIS', formatar_moeda_br(total_pis))
    with col2:
        st.metric('💵 Total COFINS', formatar_moeda_br(total_cofins))
    with col3:
        st.metric('💵 Total Geral', formatar_moeda_br(total_geral))
    
    st.markdown('---')
    
    # Gráfico de Evolução
    st.subheader('📈 Evolução Mensal')
    fig = criar_grafico_evolucao(tabela)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('---')
    
    # Tabela Detalhada
    st.subheader('📋 Detalhamento Mensal')
    
    # Formatar tabela para exibição
    tabela_exibicao = tabela.copy()
    tabela_exibicao['PIS Apurado'] = tabela_exibicao['PIS Apurado'].apply(formatar_moeda_br)
    tabela_exibicao['COFINS Apurado'] = tabela_exibicao['COFINS Apurado'].apply(formatar_moeda_br)
    tabela_exibicao['Total'] = tabela_exibicao['Total'].apply(formatar_moeda_br)
    
    st.dataframe(tabela_exibicao, use_container_width=True, hide_index=True)
    
    # Download CSV
    st.markdown('---')
    st.subheader('📥 Download')
    
    csv = tabela.to_csv(index=False, encoding='utf-8-sig', sep=';', decimal=',')
    st.download_button(
        label='📥 Baixar Tabela Mensal (CSV)',
        data=csv,
        file_name='pis_cofins_apurado_mensal.csv',
        mime='text/csv'
    )


# ============================================================================
# APRENDIZADOS E OBSERVAÇÕES
# ============================================================================

"""
APRENDIZADO 1: FORMATO BRASILEIRO
- Sempre usar formato brasileiro para valores monetários
- Exemplo: R$ 1.234,56 (ponto para milhar, vírgula para decimal)

APRENDIZADO 2: ORDEM ALFABÉTICA DOS MESES
- Janeiro, Fevereiro, Março, Abril, Maio, Junho
- Julho, Agosto, Setembro, Outubro, Novembro, Dezembro

APRENDIZADO 3: REGISTROS UTILIZADOS
- M210: Receitas PIS (campo VL_CONT_PER)
- M610: Receitas COFINS (campo VL_CONT_PER)

APRENDIZADO 4: COMPETÊNCIA
- Formato: MMAAAA (ex: 012025 = Janeiro/2025)
- Extrair primeiros 2 dígitos para obter o mês
"""

# ============================================================================
# FIM DO ARQUIVO
# ============================================================================
