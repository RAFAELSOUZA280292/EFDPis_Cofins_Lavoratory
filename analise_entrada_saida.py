"""
Módulo de Análise de Notas Fiscais de Entrada e Saída
======================================================

Funções para classificar e analisar notas fiscais baseadas no CFOP.
"""

import pandas as pd
from typing import Tuple, Dict


def classificar_tipo_operacao(cfop: str) -> str:
    """
    Classifica o tipo de operação baseado no CFOP.
    
    Args:
        cfop: Código Fiscal de Operações e Prestações
        
    Returns:
        'ENTRADA', 'SAÍDA' ou 'NÃO CLASSIFICADO'
    """
    if not cfop or len(str(cfop)) == 0:
        return 'NÃO CLASSIFICADO'
    
    cfop_str = str(cfop).strip()
    if len(cfop_str) == 0:
        return 'NÃO CLASSIFICADO'
    
    primeiro_digito = cfop_str[0]
    
    if primeiro_digito in ['1', '2', '3']:
        return 'ENTRADA'
    elif primeiro_digito in ['5', '6', '7']:
        return 'SAÍDA'
    else:
        return 'OUTROS'


def adicionar_classificacao_entrada_saida(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona colunas de classificação de entrada/saída ao DataFrame.
    
    Args:
        df: DataFrame com coluna CFOP
        
    Returns:
        DataFrame com colunas adicionais TIPO_OPERACAO e DIRECAO
    """
    if df.empty:
        df['TIPO_OPERACAO'] = ''
        df['DIRECAO'] = ''
        return df
    
    if 'CFOP' not in df.columns:
        df['TIPO_OPERACAO'] = 'NÃO CLASSIFICADO'
        df['DIRECAO'] = 'NÃO CLASSIFICADO'
        return df
    
    df['TIPO_OPERACAO'] = df['CFOP'].apply(classificar_tipo_operacao)
    df['DIRECAO'] = df['TIPO_OPERACAO']  # Alias para compatibilidade
    
    return df


def separar_entrada_saida(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separa o DataFrame em dois: entrada e saída.
    
    Args:
        df: DataFrame com coluna TIPO_OPERACAO
        
    Returns:
        Tupla (df_entrada, df_saida)
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    if 'TIPO_OPERACAO' not in df.columns:
        df = adicionar_classificacao_entrada_saida(df)
    
    df_entrada = df[df['TIPO_OPERACAO'] == 'ENTRADA'].copy()
    df_saida = df[df['TIPO_OPERACAO'] == 'SAÍDA'].copy()
    
    return df_entrada, df_saida


def calcular_totais_por_tipo(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Calcula totais de PIS/COFINS por tipo de operação.
    
    Args:
        df: DataFrame com colunas TIPO_OPERACAO, VL_PIS, VL_COFINS
        
    Returns:
        Dicionário com totais por tipo
    """
    if df.empty:
        return {
            'ENTRADA': {'pis': 0.0, 'cofins': 0.0, 'total': 0.0, 'qtd': 0},
            'SAÍDA': {'pis': 0.0, 'cofins': 0.0, 'total': 0.0, 'qtd': 0}
        }
    
    if 'TIPO_OPERACAO' not in df.columns:
        df = adicionar_classificacao_entrada_saida(df)
    
    totais = {}
    
    for tipo in ['ENTRADA', 'SAÍDA']:
        df_tipo = df[df['TIPO_OPERACAO'] == tipo]
        
        pis = 0.0
        cofins = 0.0
        
        if not df_tipo.empty:
            if 'VL_PIS' in df_tipo.columns:
                pis = df_tipo['VL_PIS'].sum()
            if 'VL_COFINS' in df_tipo.columns:
                cofins = df_tipo['VL_COFINS'].sum()
        
        totais[tipo] = {
            'pis': pis,
            'cofins': cofins,
            'total': pis + cofins,
            'qtd': len(df_tipo)
        }
    
    return totais


def resumo_entrada_saida(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria um resumo consolidado de entrada e saída.
    
    Args:
        df: DataFrame com dados de NF-e
        
    Returns:
        DataFrame com resumo
    """
    if df.empty:
        return pd.DataFrame(columns=['TIPO', 'QUANTIDADE', 'PIS', 'COFINS', 'TOTAL'])
    
    if 'TIPO_OPERACAO' not in df.columns:
        df = adicionar_classificacao_entrada_saida(df)
    
    totais = calcular_totais_por_tipo(df)
    
    resumo_data = []
    for tipo, valores in totais.items():
        resumo_data.append({
            'TIPO': tipo,
            'QUANTIDADE': valores['qtd'],
            'PIS': valores['pis'],
            'COFINS': valores['cofins'],
            'TOTAL': valores['total']
        })
    
    df_resumo = pd.DataFrame(resumo_data)
    return df_resumo


def top_produtos_por_tipo(df: pd.DataFrame, tipo: str, top_n: int = 10) -> pd.DataFrame:
    """
    Retorna os top N produtos por tipo de operação.
    
    Args:
        df: DataFrame com dados de NF-e
        tipo: 'ENTRADA' ou 'SAÍDA'
        top_n: Número de produtos a retornar
        
    Returns:
        DataFrame com top produtos
    """
    if df.empty:
        return pd.DataFrame()
    
    if 'TIPO_OPERACAO' not in df.columns:
        df = adicionar_classificacao_entrada_saida(df)
    
    df_tipo = df[df['TIPO_OPERACAO'] == tipo].copy()
    
    if df_tipo.empty:
        return pd.DataFrame()
    
    # Agrupa por produto
    if 'DESCR_ITEM' in df_tipo.columns and 'VL_PIS' in df_tipo.columns and 'VL_COFINS' in df_tipo.columns:
        df_agrupado = df_tipo.groupby('DESCR_ITEM').agg({
            'VL_PIS': 'sum',
            'VL_COFINS': 'sum'
        }).reset_index()
        
        df_agrupado['TOTAL'] = df_agrupado['VL_PIS'] + df_agrupado['VL_COFINS']
        df_agrupado = df_agrupado.sort_values('TOTAL', ascending=False).head(top_n)
        
        return df_agrupado
    
    return pd.DataFrame()


def evolucao_mensal_entrada_saida(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a evolução mensal de entrada e saída.
    
    Args:
        df: DataFrame com dados de NF-e
        
    Returns:
        DataFrame com evolução mensal
    """
    if df.empty:
        return pd.DataFrame()
    
    if 'TIPO_OPERACAO' not in df.columns:
        df = adicionar_classificacao_entrada_saida(df)
    
    if 'COMPETENCIA' not in df.columns:
        return pd.DataFrame()
    
    # Agrupa por competência e tipo
    df_evolucao = df.groupby(['COMPETENCIA', 'TIPO_OPERACAO']).agg({
        'VL_PIS': 'sum',
        'VL_COFINS': 'sum'
    }).reset_index()
    
    df_evolucao['TOTAL'] = df_evolucao['VL_PIS'] + df_evolucao['VL_COFINS']
    
    return df_evolucao
