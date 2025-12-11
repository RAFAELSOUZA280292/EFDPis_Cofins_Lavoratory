"""
================================================================================
MÓDULO: Acumuladores por CFOP
================================================================================

OBJETIVO:
    Criar totalizadores agrupados por CFOP para análise fiscal de PIS/COFINS

CONTEXTO:
    - CFOP = Código Fiscal de Operações e Prestações
    - Usado em Notas Fiscais brasileiras
    - Identifica o tipo de operação fiscal

CLASSIFICAÇÃO:
    - ENTRADA: CFOP iniciados em 1, 2, 3 (ex: 1102, 2102, 3102)
    - SAÍDA: CFOP iniciados em 5, 6, 7 (ex: 5102, 6102, 7102)

CAMPOS ACUMULADOS:
    - VL_BC_PIS: Base de Cálculo do PIS
    - VL_PIS: Valor do PIS
    - VL_BC_COFINS: Base de Cálculo do COFINS
    - VL_COFINS: Valor do COFINS

FORMATO DE VALORES:
    - Padrão brasileiro: R$ 1.234,56
    - Ponto para milhar, vírgula para decimal

GATILHOS PARA MANUTENÇÃO:
    1. Se adicionar novos campos: incluir na lista CAMPOS_ACUMULAVEIS
    2. Se mudar formatação: ajustar função formatar_valor_br
    3. Se mudar classificação CFOP: ajustar função classificar_cfop

APRENDIZADOS:
    - Sempre agrupar por CFOP antes de somar
    - Sempre formatar valores no padrão brasileiro
    - Sempre ordenar por valor total (maior para menor)
    - Sempre incluir coluna de quantidade de notas

HISTÓRICO:
    - 2025-01-XX: Criação inicial com acumuladores de ENTRADA e SAÍDA
    
AUTOR: Manus AI Assistant
================================================================================
"""

import pandas as pd
import streamlit as st


# ============================================================================
# CONSTANTES E CONFIGURAÇÕES
# ============================================================================

# Campos que serão somados no acumulador
CAMPOS_ACUMULAVEIS = ['VL_BC_PIS', 'VL_PIS', 'VL_BC_COFINS', 'VL_COFINS']

# Mapeamento de nomes para exibição
NOMES_COLUNAS = {
    'CFOP': 'CFOP',
    'QTD_NOTAS': 'Qtd. Notas',
    'VL_BC_PIS': 'Base PIS',
    'VL_PIS': 'Valor PIS',
    'VL_BC_COFINS': 'Base COFINS',
    'VL_COFINS': 'Valor COFINS',
    'TOTAL': 'Total (PIS + COFINS)'
}


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def formatar_valor_br(valor):
    """
    Formata valor monetário no padrão brasileiro.
    
    Args:
        valor (float): Valor numérico
        
    Returns:
        str: Valor formatado como "R$ 1.234,56"
        
    Exemplo:
        >>> formatar_valor_br(1234.56)
        'R$ 1.234,56'
    
    GATILHO: Se mudar formato, ajustar aqui
    """
    try:
        # Formata com 2 casas decimais
        valor_str = f"{valor:,.2f}"
        # Troca separadores: , -> TEMP, . -> ,, TEMP -> .
        valor_str = valor_str.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return f"R$ {valor_str}"
    except:
        return "R$ 0,00"


def classificar_cfop(cfop):
    """
    Classifica CFOP como ENTRADA ou SAÍDA.
    
    Args:
        cfop (str): Código CFOP (ex: "1102", "5102")
        
    Returns:
        str: "ENTRADA" ou "SAÍDA"
        
    Regra:
        - ENTRADA: CFOP iniciado em 1, 2 ou 3
        - SAÍDA: CFOP iniciado em 5, 6 ou 7
        
    GATILHO: Se mudar regra de classificação, ajustar aqui
    """
    cfop_str = str(cfop).strip()
    if cfop_str and cfop_str[0] in ['1', '2', '3']:
        return 'ENTRADA'
    elif cfop_str and cfop_str[0] in ['5', '6', '7']:
        return 'SAÍDA'
    else:
        return 'OUTROS'


# ============================================================================
# FUNÇÃO PRINCIPAL: CRIAR ACUMULADOR
# ============================================================================

def criar_acumulador_cfop(df, tipo_operacao='ENTRADA'):
    """
    Cria acumulador de valores por CFOP.
    
    OBJETIVO:
        Agrupar notas fiscais por CFOP e somar os valores de PIS e COFINS
    
    PROCESSO:
        1. Filtra DataFrame pelo tipo de operação
        2. Agrupa por CFOP
        3. Soma os valores (BC PIS, PIS, BC COFINS, COFINS)
        4. Conta quantidade de notas
        5. Calcula total (PIS + COFINS)
        6. Ordena por total (maior para menor)
        7. Formata valores no padrão brasileiro
    
    Args:
        df (pd.DataFrame): DataFrame com dados das notas fiscais
        tipo_operacao (str): "ENTRADA" ou "SAÍDA"
        
    Returns:
        pd.DataFrame: Acumulador formatado com colunas:
            - CFOP
            - Qtd. Notas
            - Base PIS
            - Valor PIS
            - Base COFINS
            - Valor COFINS
            - Total (PIS + COFINS)
    
    CAMPOS NECESSÁRIOS NO DF:
        - CFOP: Código fiscal
        - VL_BC_PIS: Base de cálculo PIS
        - VL_PIS: Valor PIS
        - VL_BC_COFINS: Base de cálculo COFINS
        - VL_COFINS: Valor COFINS
    
    GATILHOS:
        - Para adicionar novos campos: incluir em CAMPOS_ACUMULAVEIS
        - Para mudar ordenação: ajustar sort_values
        - Para mudar formato: ajustar formatar_valor_br
    
    EXEMPLO DE USO:
        >>> df_entrada = df[df['TIPO_OPERACAO'] == 'ENTRADA']
        >>> acumulador = criar_acumulador_cfop(df_entrada, 'ENTRADA')
    """
    
    # ========================================================================
    # PASSO 1: VALIDAÇÃO
    # ========================================================================
    
    if df.empty:
        # Retorna DataFrame vazio com estrutura correta
        return pd.DataFrame(columns=list(NOMES_COLUNAS.values()))
    
    # Verifica se tem todos os campos necessários
    campos_necessarios = ['CFOP'] + CAMPOS_ACUMULAVEIS
    campos_faltantes = [c for c in campos_necessarios if c not in df.columns]
    
    if campos_faltantes:
        st.warning(f"⚠️ Campos faltantes para acumulador: {', '.join(campos_faltantes)}")
        return pd.DataFrame(columns=list(NOMES_COLUNAS.values()))
    
    # ========================================================================
    # PASSO 2: AGRUPAMENTO E SOMA
    # ========================================================================
    
    # Agrupa por CFOP e soma os valores
    # Nota: Não incluímos CFOP no agg porque ele é o índice do groupby
    acumulador = df.groupby('CFOP').agg({
        'NUM_DOC': 'count',  # Conta quantidade de notas
        'VL_BC_PIS': 'sum',
        'VL_PIS': 'sum',
        'VL_BC_COFINS': 'sum',
        'VL_COFINS': 'sum'
    }).reset_index()
    
    # Renomeia coluna de contagem
    acumulador = acumulador.rename(columns={'NUM_DOC': 'QTD_NOTAS'})
    
    # ========================================================================
    # PASSO 3: CÁLCULOS ADICIONAIS
    # ========================================================================
    
    # Calcula total (PIS + COFINS)
    acumulador['TOTAL'] = acumulador['VL_PIS'] + acumulador['VL_COFINS']
    
    # Ordena por total (maior para menor)
    acumulador = acumulador.sort_values('TOTAL', ascending=False)
    
    # ========================================================================
    # PASSO 4: FORMATAÇÃO PARA EXIBIÇÃO
    # ========================================================================
    
    # Cria cópia para exibição
    df_display = acumulador.copy()
    
    # Formata valores monetários
    colunas_monetarias = ['VL_BC_PIS', 'VL_PIS', 'VL_BC_COFINS', 'VL_COFINS', 'TOTAL']
    for col in colunas_monetarias:
        df_display[col] = df_display[col].apply(formatar_valor_br)
    
    # Formata quantidade de notas
    df_display['QTD_NOTAS'] = df_display['QTD_NOTAS'].apply(lambda x: f"{x:,}".replace(',', '.'))
    
    # Renomeia colunas para nomes amigáveis
    df_display = df_display.rename(columns=NOMES_COLUNAS)
    
    # ========================================================================
    # PASSO 5: RETORNO
    # ========================================================================
    
    return df_display


# ============================================================================
# FUNÇÃO AUXILIAR: EXIBIR ACUMULADOR NO STREAMLIT
# ============================================================================

def exibir_acumulador_cfop(df, tipo_operacao='ENTRADA'):
    """
    Exibe acumulador por CFOP no Streamlit.
    
    OBJETIVO:
        Mostrar tabela de totais por CFOP com formatação adequada
    
    Args:
        df (pd.DataFrame): DataFrame com dados das notas fiscais
        tipo_operacao (str): "ENTRADA" ou "SAÍDA"
    
    EXIBIÇÃO:
        - Título com emoji
        - Descrição
        - Tabela interativa
        - Botão de download CSV
    
    GATILHOS:
        - Para mudar layout: ajustar st.markdown e st.dataframe
        - Para adicionar gráficos: incluir após a tabela
    """
    
    # Emoji conforme tipo
    emoji = "📥" if tipo_operacao == "ENTRADA" else "📤"
    
    # Título
    st.markdown(f"### {emoji} Acumulador por CFOP - {tipo_operacao}")
    st.markdown(f"**Totalização de valores agrupados por CFOP**")
    
    # Cria acumulador
    acumulador = criar_acumulador_cfop(df, tipo_operacao)
    
    if acumulador.empty:
        st.info(f"📊 Nenhum dado para acumulador de {tipo_operacao}")
        return
    
    # Exibe tabela
    st.dataframe(
        acumulador,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Botão de download
    csv = acumulador.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label=f"📥 Baixar Acumulador {tipo_operacao} (CSV)",
        data=csv,
        file_name=f"acumulador_cfop_{tipo_operacao.lower()}.csv",
        mime="text/csv"
    )


# ============================================================================
# DOCUMENTAÇÃO DE USO
# ============================================================================

"""
EXEMPLO DE USO NO APP.PY:

```python
from acumuladores_cfop import exibir_acumulador_cfop

# Separa entrada e saída
df_entrada = df[df['TIPO_OPERACAO'] == 'ENTRADA']
df_saida = df[df['TIPO_OPERACAO'] == 'SAÍDA']

# Exibe acumuladores
st.markdown("---")
st.markdown("## 📊 Acumuladores por CFOP")

col1, col2 = st.columns(2)

with col1:
    exibir_acumulador_cfop(df_entrada, 'ENTRADA')

with col2:
    exibir_acumulador_cfop(df_saida, 'SAÍDA')
```

MANUTENÇÃO FUTURA:
    1. Para adicionar novos campos acumulados:
       - Adicionar em CAMPOS_ACUMULAVEIS
       - Adicionar em NOMES_COLUNAS
       - Ajustar agregação em criar_acumulador_cfop
    
    2. Para mudar formato de exibição:
       - Ajustar formatar_valor_br
       - Ajustar exibir_acumulador_cfop
    
    3. Para adicionar gráficos:
       - Incluir em exibir_acumulador_cfop após a tabela
       - Usar dados não formatados (acumulador antes da formatação)
"""
