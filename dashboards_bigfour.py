"""
Dashboards Profissionais - Estilo Big Four
Módulo para criar visualizações executivas de alto nível
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st


# Paleta de cores profissional (estilo Big Four)
COLORS = {
    'primary': '#003366',      # Azul escuro corporativo
    'secondary': '#0066CC',    # Azul médio
    'accent': '#FF6B35',       # Laranja destaque
    'success': '#2ECC71',      # Verde sucesso
    'warning': '#F39C12',      # Amarelo alerta
    'danger': '#E74C3C',       # Vermelho perigo
    'neutral': '#95A5A6',      # Cinza neutro
    'background': '#F8F9FA'    # Fundo claro
}

# Paleta para gráficos de pizza (10 cores distintas)
PIZZA_COLORS = [
    '#003366', '#0066CC', '#3399FF', '#66B2FF',
    '#FF6B35', '#FFA07A', '#2ECC71', '#58D68D',
    '#F39C12', '#F8C471'
]


def formatar_valor_br(valor):
    """Formata valor no padrão brasileiro: R$ 1.234,56"""
    try:
        # Formata com 2 casas decimais usando formato americano
        valor_str = f"{valor:,.2f}"
        # Troca separadores: , por TEMP, . por ,, TEMP por .
        valor_str = valor_str.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return f"R$ {valor_str}"
    except:
        return "R$ 0,00"


def criar_kpi_card(titulo, valor, subtitulo="", cor=COLORS['primary']):
    """Cria um card KPI profissional"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {cor} 0%, {cor}DD 100%);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
        text-align: center;
    ">
        <div style="font-size: 14px; font-weight: 500; opacity: 0.9; margin-bottom: 8px;">
            {titulo}
        </div>
        <div style="font-size: 32px; font-weight: 700; margin-bottom: 4px;">
            {valor}
        </div>
        <div style="font-size: 12px; opacity: 0.8;">
            {subtitulo}
        </div>
    </div>
    """, unsafe_allow_html=True)


def criar_grafico_pizza_top10_credito(df):
    """
    Cria gráfico de pizza TOP 10 NCM com maior CRÉDITO (PIS + COFINS de ENTRADA)
    
    Args:
        df: DataFrame completo com todas as notas
        
    Returns:
        Figura Plotly
    """
    # Filtra apenas ENTRADA (crédito)
    df_entrada = df[df['TIPO_OPERACAO'] == 'ENTRADA'].copy()
    
    if df_entrada.empty:
        return None
    
    # Calcula total de crédito por NCM
    df_entrada['CREDITO_TOTAL'] = df_entrada['VL_PIS'] + df_entrada['VL_COFINS']
    
    # Agrupa por NCM e soma
    top10 = df_entrada.groupby('NCM').agg({
        'CREDITO_TOTAL': 'sum',
        'DESCR_ITEM': 'first'  # Pega primeira descrição do NCM
    }).reset_index()
    
    # Ordena e pega TOP 10
    top10 = top10.sort_values('CREDITO_TOTAL', ascending=False).head(10)
    
    # Cria labels com NCM e valor
    top10['label'] = top10.apply(
        lambda x: f"NCM {x['NCM']}<br>{formatar_valor_br(x['CREDITO_TOTAL'])}", 
        axis=1
    )
    
    # Cria gráfico de pizza
    fig = go.Figure(data=[go.Pie(
        labels=top10['label'],
        values=top10['CREDITO_TOTAL'],
        hole=0.4,  # Donut chart
        marker=dict(
            colors=PIZZA_COLORS,
            line=dict(color='white', width=2)
        ),
        textinfo='percent',
        textfont=dict(size=12, color='white', family='Arial Black'),
        hovertemplate='<b>%{label}</b><br>Valor: %{value:,.2f}<br>Percentual: %{percent}<extra></extra>'
    )])
    
    # Layout profissional
    fig.update_layout(
        title=dict(
            text='<b>TOP 10 NCM - MAIOR CRÉDITO</b><br><sub>PIS + COFINS (Entrada)</sub>',
            font=dict(size=18, color=COLORS['primary'], family='Arial'),
            x=0.5,
            xanchor='center'
        ),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=10)
        ),
        height=500,
        margin=dict(l=20, r=150, t=80, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    return fig


def criar_grafico_pizza_top10_debito(df):
    """
    Cria gráfico de pizza TOP 10 NCM com maior DÉBITO (PIS + COFINS de SAÍDA)
    
    Args:
        df: DataFrame completo com todas as notas
        
    Returns:
        Figura Plotly
    """
    # Filtra apenas SAÍDA (débito)
    df_saida = df[df['TIPO_OPERACAO'] == 'SAÍDA'].copy()
    
    if df_saida.empty:
        return None
    
    # Calcula total de débito por NCM
    df_saida['DEBITO_TOTAL'] = df_saida['VL_PIS'] + df_saida['VL_COFINS']
    
    # Agrupa por NCM e soma
    top10 = df_saida.groupby('NCM').agg({
        'DEBITO_TOTAL': 'sum',
        'DESCR_ITEM': 'first'  # Pega primeira descrição do NCM
    }).reset_index()
    
    # Ordena e pega TOP 10
    top10 = top10.sort_values('DEBITO_TOTAL', ascending=False).head(10)
    
    # Cria labels com NCM e valor
    top10['label'] = top10.apply(
        lambda x: f"NCM {x['NCM']}<br>{formatar_valor_br(x['DEBITO_TOTAL'])}", 
        axis=1
    )
    
    # Cria gráfico de pizza
    fig = go.Figure(data=[go.Pie(
        labels=top10['label'],
        values=top10['DEBITO_TOTAL'],
        hole=0.4,  # Donut chart
        marker=dict(
            colors=PIZZA_COLORS,
            line=dict(color='white', width=2)
        ),
        textinfo='percent',
        textfont=dict(size=12, color='white', family='Arial Black'),
        hovertemplate='<b>%{label}</b><br>Valor: %{value:,.2f}<br>Percentual: %{percent}<extra></extra>'
    )])
    
    # Layout profissional
    fig.update_layout(
        title=dict(
            text='<b>TOP 10 NCM - MAIOR DÉBITO</b><br><sub>PIS + COFINS (Saída)</sub>',
            font=dict(size=18, color=COLORS['primary'], family='Arial'),
            x=0.5,
            xanchor='center'
        ),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=10)
        ),
        height=500,
        margin=dict(l=20, r=150, t=80, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    return fig


def criar_grafico_barras_comparativo(df):
    """Cria gráfico de barras comparativo Crédito vs Débito"""
    df_entrada = df[df['TIPO_OPERACAO'] == 'ENTRADA']
    df_saida = df[df['TIPO_OPERACAO'] == 'SAÍDA']
    
    credito_pis = df_entrada['VL_PIS'].sum()
    credito_cofins = df_entrada['VL_COFINS'].sum()
    debito_pis = df_saida['VL_PIS'].sum()
    debito_cofins = df_saida['VL_COFINS'].sum()
    
    fig = go.Figure(data=[
        go.Bar(
            name='CRÉDITO',
            x=['PIS', 'COFINS'],
            y=[credito_pis, credito_cofins],
            marker_color=COLORS['success'],
            text=[formatar_valor_br(credito_pis), formatar_valor_br(credito_cofins)],
            textposition='outside',
            textfont=dict(size=12, color=COLORS['success'], family='Arial Black')
        ),
        go.Bar(
            name='DÉBITO',
            x=['PIS', 'COFINS'],
            y=[debito_pis, debito_cofins],
            marker_color=COLORS['danger'],
            text=[formatar_valor_br(debito_pis), formatar_valor_br(debito_cofins)],
            textposition='outside',
            textfont=dict(size=12, color=COLORS['danger'], family='Arial Black')
        )
    ])
    
    fig.update_layout(
        title=dict(
            text='<b>COMPARATIVO CRÉDITO vs DÉBITO</b>',
            font=dict(size=18, color=COLORS['primary'], family='Arial'),
            x=0.5,
            xanchor='center'
        ),
        barmode='group',
        xaxis=dict(
            title='Tributo',
            titlefont=dict(size=14, color=COLORS['primary']),
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            title='Valor (R$)',
            titlefont=dict(size=14, color=COLORS['primary']),
            tickfont=dict(size=12),
            gridcolor='#E0E0E0'
        ),
        height=400,
        margin=dict(l=60, r=40, t=80, b=60),
        paper_bgcolor='white',
        plot_bgcolor='white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12)
        )
    )
    
    return fig


def exibir_dashboard_executivo(df):
    """
    Exibe dashboard executivo completo estilo Big Four
    
    Args:
        df: DataFrame com todas as notas processadas
    """
    st.markdown("---")
    st.markdown("## 📊 Dashboard Executivo")
    
    # Separa entrada e saída
    df_entrada = df[df['TIPO_OPERACAO'] == 'ENTRADA']
    df_saida = df[df['TIPO_OPERACAO'] == 'SAÍDA']
    
    # KPIs principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_credito = df_entrada['VL_PIS'].sum() + df_entrada['VL_COFINS'].sum()
        criar_kpi_card(
            "💰 CRÉDITO TOTAL",
            formatar_valor_br(total_credito),
            f"{len(df_entrada)} notas",
            COLORS['success']
        )
    
    with col2:
        total_debito = df_saida['VL_PIS'].sum() + df_saida['VL_COFINS'].sum()
        criar_kpi_card(
            "💸 DÉBITO TOTAL",
            formatar_valor_br(total_debito),
            f"{len(df_saida)} notas",
            COLORS['danger']
        )
    
    with col3:
        saldo = total_credito - total_debito
        cor_saldo = COLORS['success'] if saldo >= 0 else COLORS['danger']
        criar_kpi_card(
            "⚖️ SALDO",
            formatar_valor_br(abs(saldo)),
            "Crédito - Débito",
            cor_saldo
        )
    
    with col4:
        total_ncm = df['NCM'].nunique()
        criar_kpi_card(
            "🏷️ NCMs DISTINTOS",
            str(total_ncm),
            "Produtos diferentes",
            COLORS['primary']
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráficos de pizza TOP 10
    col1, col2 = st.columns(2)
    
    with col1:
        fig_credito = criar_grafico_pizza_top10_credito(df)
        if fig_credito:
            st.plotly_chart(fig_credito, use_container_width=True)
        else:
            st.info("📊 Sem dados de ENTRADA para exibir")
    
    with col2:
        fig_debito = criar_grafico_pizza_top10_debito(df)
        if fig_debito:
            st.plotly_chart(fig_debito, use_container_width=True)
        else:
            st.info("📊 Sem dados de SAÍDA para exibir")
    
    # Gráfico comparativo
    st.markdown("<br>", unsafe_allow_html=True)
    fig_comparativo = criar_grafico_barras_comparativo(df)
    st.plotly_chart(fig_comparativo, use_container_width=True)
