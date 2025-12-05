"""
Parser SPED PIS/COFINS - Versão Corrigida
Extrai dados de Notas Fiscais dos registros 0200, C100 e C170
"""

import pandas as pd
from typing import List, Dict


def extrair_campo(linha: str, indice: int, default: str = "") -> str:
    """Extrai campo de uma linha SPED pelo índice"""
    try:
        partes = linha.split('|')
        if indice < len(partes):
            return partes[indice].strip()
        return default
    except:
        return default


def to_float(valor: str) -> float:
    """Converte string para float, tratando vírgula como separador decimal"""
    try:
        if not valor or valor.strip() == '':
            return 0.0
        # Remove pontos de milhar e substitui vírgula por ponto
        valor_limpo = valor.replace('.', '').replace(',', '.')
        return float(valor_limpo)
    except:
        return 0.0


def formatar_valor_br(valor: float) -> str:
    """Formata valor no padrão brasileiro: R$ 1.234,56"""
    try:
        # Formata com 2 casas decimais
        valor_str = f"{valor:,.2f}"
        # Substitui separadores: , por . e . por ,
        valor_str = valor_str.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"R$ {valor_str}"
    except:
        return "R$ 0,00"


def processar_sped(conteudo: str) -> pd.DataFrame:
    """
    Processa o conteúdo de um arquivo SPED e retorna DataFrame com NF-e
    
    Args:
        conteudo: String com o conteúdo completo do arquivo SPED
        
    Returns:
        DataFrame com as notas fiscais processadas
    """
    linhas = conteudo.split('\n')
    
    # Dicionário para armazenar produtos do registro 0200
    produtos = {}
    
    # Primeiro passo: Ler todos os registros 0200 (cadastro de produtos)
    for linha in linhas:
        linha = linha.strip()
        if linha.startswith('|0200|'):
            cod_item = extrair_campo(linha, 2)
            descr_item = extrair_campo(linha, 3)
            ncm = extrair_campo(linha, 8)
            
            if cod_item:
                produtos[cod_item] = {
                    'descricao': descr_item,
                    'ncm': ncm
                }
    
    # Dicionários para armazenar dados
    c100_atual = {}
    registros = []
    
    # Segundo passo: Processar C100 e C170
    for linha in linhas:
        linha = linha.strip()
        
        if not linha:
            continue
        
        # Registro C100 - Cabeçalho do Documento
        if linha.startswith('|C100|'):
            c100_atual = {
                'NUM_DOC': extrair_campo(linha, 8),   # Número do documento
                'CHV_NFE': extrair_campo(linha, 9),   # Chave NF-e
                'DT_DOC': extrair_campo(linha, 10),   # Data do documento (emissão)
                'COD_PART': extrair_campo(linha, 4),  # Código participante
            }
        
        # Registro C170 - Itens do Documento
        elif linha.startswith('|C170|') and c100_atual:
            # Extrai código do item
            cod_item = extrair_campo(linha, 3)
            
            # Busca descrição e NCM no cadastro de produtos
            produto_info = produtos.get(cod_item, {'descricao': '', 'ncm': ''})
            
            # Extrai dados do item conforme mapeamento correto
            registro = {
                # Dados do documento (C100)
                'NUM_DOC': c100_atual.get('NUM_DOC', ''),
                'CHV_NFE': c100_atual.get('CHV_NFE', ''),
                'DT_DOC': c100_atual.get('DT_DOC', ''),
                'COD_PART': c100_atual.get('COD_PART', ''),
                
                # Dados do item (C170)
                'COD_ITEM': cod_item,
                'DESCR_ITEM': produto_info['descricao'],
                'NCM': produto_info['ncm'],
                'CFOP': extrair_campo(linha, 11),         # Campo [11] = CFOP
                
                # Valores PIS
                'CST_PIS': extrair_campo(linha, 25),      # Campo [25] = CST PIS
                'VL_BC_PIS': extrair_campo(linha, 26),    # Campo [26] = Base de cálculo PIS
                'ALIQ_PIS': extrair_campo(linha, 27),     # Campo [27] = Alíquota PIS
                'VL_PIS': extrair_campo(linha, 30),       # Campo [30] = Valor PIS
                
                # Valores COFINS
                'CST_COFINS': extrair_campo(linha, 31),   # Campo [31] = CST COFINS
                'VL_BC_COFINS': extrair_campo(linha, 32), # Campo [32] = Base de cálculo COFINS
                'ALIQ_COFINS': extrair_campo(linha, 33),  # Campo [33] = Alíquota COFINS
                'VL_COFINS': extrair_campo(linha, 36),    # Campo [36] = Valor COFINS
            }
            
            registros.append(registro)
    
    # Cria DataFrame
    if not registros:
        return pd.DataFrame()
    
    df = pd.DataFrame(registros)
    
    # Converte valores numéricos
    colunas_numericas = ['VL_BC_PIS', 'ALIQ_PIS', 'VL_PIS', 'VL_BC_COFINS', 'ALIQ_COFINS', 'VL_COFINS']
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = df[col].apply(to_float)
    
    # Adiciona coluna de tipo de operação baseada no CFOP
    if 'CFOP' in df.columns:
        df['TIPO_OPERACAO'] = df['CFOP'].apply(classificar_cfop)
    else:
        df['TIPO_OPERACAO'] = 'NÃO CLASSIFICADO'
    
    # Calcula valor total
    df['VL_TOTAL'] = df['VL_PIS'] + df['VL_COFINS']
    
    return df


def classificar_cfop(cfop: str) -> str:
    """
    Classifica o CFOP em ENTRADA ou SAÍDA
    
    Args:
        cfop: Código CFOP
        
    Returns:
        'ENTRADA', 'SAÍDA' ou 'OUTROS'
    """
    if not cfop or len(str(cfop)) == 0:
        return 'OUTROS'
    
    cfop_str = str(cfop).strip()
    if len(cfop_str) == 0:
        return 'OUTROS'
    
    primeiro_digito = cfop_str[0]
    
    if primeiro_digito in ['1', '2', '3']:
        return 'ENTRADA'
    elif primeiro_digito in ['5', '6', '7']:
        return 'SAÍDA'
    else:
        return 'OUTROS'


def processar_multiplos_speds(arquivos_conteudo: List[str]) -> pd.DataFrame:
    """
    Processa múltiplos arquivos SPED e consolida em um único DataFrame
    
    Args:
        arquivos_conteudo: Lista com conteúdo dos arquivos SPED
        
    Returns:
        DataFrame consolidado
    """
    dataframes = []
    
    for conteudo in arquivos_conteudo:
        df = processar_sped(conteudo)
        if not df.empty:
            dataframes.append(df)
    
    if not dataframes:
        return pd.DataFrame()
    
    return pd.concat(dataframes, ignore_index=True)
