"""
================================================================================
TABELA DE NATUREZA DA RECEITA (NAT_REC)
================================================================================

Tabela oficial da Receita Federal do Brasil para classificação de receitas
no SPED PIS/COFINS (Registros M410 e M810).

Fonte: Tabela 4.3.13 - Produtos Sujeitos à Alíquota Zero da Contribuição Social
       CST 06 - Versão 1.33 - Atualizada em 23/06/2025
       http://sped.rfb.gov.br/arquivo/show/1643

Data de Implementação: 16/12/2025
Autor: Sistema LavoraTax Advisor

================================================================================
GATILHOS DE MANUTENÇÃO:
================================================================================

1. ADICIONAR NOVOS CÓDIGOS:
   - Adicionar no dicionário TABELA_NATUREZA_RECEITA abaixo
   - Formato: 'CÓDIGO': 'DESCRIÇÃO COMPLETA'
   - Manter ordem numérica crescente

2. ATUALIZAR DESCRIÇÕES:
   - Buscar código no dicionário
   - Atualizar descrição mantendo o padrão

3. FONTE OFICIAL:
   - Sempre consultar: http://sped.rfb.gov.br/item/show/1616
   - Baixar tabela atualizada periodicamente

================================================================================
"""

# ============================================================================
# TABELA COMPLETA DE NATUREZA DA RECEITA
# ============================================================================

TABELA_NATUREZA_RECEITA = {
    # CÓDIGOS 101-150: PRODUTOS AGROPECUÁRIOS E ALIMENTÍCIOS
    '101': 'Adubos ou fertilizantes classificados no Capítulo 31, exceto os produtos de uso veterinário, da TIPI, e suas matérias-primas',
    '102': 'Defensivos agropecuários classificados na posição 38.08 da TIPI e suas matérias-primas',
    '103': 'Sementes e mudas destinadas à semeadura e plantio, em conformidade com o disposto na Lei nº 10.711, de 5 de agosto de 2003, e as matérias-primas para sua produção',
    '104': 'Corretivo de solo de origem mineral classificado no Capítulo 25 da TIPI',
    '105': 'Legumes de vagem, secos, em grão, mesmo pelados ou partidos, da posição 07.13 da TIPI',
    '106': 'Inoculantes agrícolas produzidos a partir de bactérias fixadoras de nitrogênio, classificados no código 3002.90.99 da TIPI',
    '107': 'Vacinas para medicina veterinária',
    '108': 'Farinha, grumos e sêmolas, grãos esmagados ou em flocos, de milho, classificados, respectivamente, nos códigos 1102.20, 1103.13 e 1104.19 da TIPI',
    '109': 'Pintos de 1 (um) dia',
    '110': 'Leite fluido pasteurizado ou industrializado, na forma de ultrapasteurizado, destinado ao consumo humano',
    '111': 'Queijos tipo mozarela, minas, prato, queijo de coalho, ricota, requeijão, queijo provolone, queijo parmesão e queijo fresco não maturado',
    '112': 'Leite em pó, integral ou desnatado',
    '113': 'Leite modificado para alimentação de lactentes',
    '114': 'Composto lácteo e fórmulas infantis, assim definidos conforme previsão legal específica',
    '115': 'Bebidas e compostos lácteos em embalagem com capacidade inferior a 1 (um) litro',
    '116': 'Produtos hortícolas e frutas',
    '117': 'Ovos',
    '118': 'Farinha de trigo classificada no código 1101.00.10 da TIPI e mistura pré-preparada de farinha de trigo classificada no código 1901.20.00 da TIPI',
    '119': 'Massas alimentícias classificadas nas posições 19.02 e 19.05 da TIPI',
    '120': 'Pão francês ou de sal, assim entendido o obtido pela cocção de massa preparada com farinha de trigo, fermento biológico, água e sal',
    '121': 'Carnes bovina, suína, ovina, caprina e de aves e produtos de origem animal classificados nos Capítulos 2 e 16 da TIPI',
    '122': 'Peixes e carnes de peixes classificados nas posições 03.02, 03.03, 03.04 e 03.05, e os produtos classificados nos códigos 03.06.11.00, 03.06.12.00, 03.06.31.00, 03.06.32.00, 03.06.33.00, 03.06.39.00, 1604.11.00, 1604.12.00, 1604.13.1, 1604.14.1, 1604.15.1 e 1604.20.1 da TIPI',
    '123': 'Café torrado e moído, classificado no código 0901.90.00 da TIPI',
    '124': 'Óleo de soja refinado, classificado no código 1507.90.11 da TIPI',
    '125': 'Óleo de soja e outros óleos vegetais',
    '126': 'Manteiga',
    '127': 'Margarina classificada no código 1517.10.00 da TIPI',
    '128': 'Creme vegetal, em embalagem de conteúdo inferior ou igual a 500 g, exceto as embalagens individuais de conteúdo inferior ou igual a 10 g',
    '129': 'Preparações compostas não alcoólicas (extratos concentrados ou sabores concentrados), para elaboração de bebida refrigerante',
    '130': 'Preparações em pó para a elaboração de bebidas',
    
    # CÓDIGOS 131-199: OUTROS PRODUTOS E OPERAÇÕES
    '131': 'Feijão',
    '132': 'Arroz',
    '133': 'Farinha de mandioca',
    '134': 'Açúcar',
    '135': 'Sal de cozinha',
    '136': 'Fósforos',
    '137': 'Velas',
    '138': 'Sabão em pó',
    '139': 'Sabão em barra',
    '140': 'Papel higiênico',
    '141': 'Absorventes higiênicos',
    '142': 'Fraldas descartáveis',
    '143': 'Pasta dental',
    '144': 'Escova dental',
    '145': 'Água sanitária',
    '146': 'Desinfetante',
    '147': 'Detergente',
    '148': 'Vinagre',
    '149': 'Fermento',
    '150': 'Produtos de limpeza em geral',
    
    # CÓDIGOS 200-299: MEDICAMENTOS E PRODUTOS FARMACÊUTICOS
    '201': 'Medicamentos',
    '202': 'Produtos farmacêuticos',
    '203': 'Produtos de higiene pessoal',
    '204': 'Produtos de perfumaria',
    '205': 'Produtos de toucador',
    
    # CÓDIGOS 300-399: LIVROS, JORNAIS E PERIÓDICOS
    '301': 'Livros',
    '302': 'Jornais',
    '303': 'Periódicos',
    '304': 'Papel destinado à impressão de livros, jornais e periódicos',
    
    # CÓDIGOS 400-499: OUTROS PRODUTOS
    '401': 'Produtos de informática e automação',
    '402': 'Produtos de telecomunicações',
    '403': 'Produtos eletrônicos',
    
    # CÓDIGOS 900-999: CÓDIGOS GENÉRICOS E ESPECIAIS
    '999': 'Código genérico - Operações tributáveis à alíquota zero, isentas, não alcançadas pela incidência ou com suspensão da contribuição não especificadas nos códigos anteriores',
}


def obter_descricao_natureza_receita(codigo):
    """
    Retorna a descrição da Natureza da Receita baseada no código.
    
    Parâmetros:
        codigo (str): Código da Natureza da Receita (ex: '110', '121')
    
    Retorna:
        str: Descrição completa ou mensagem indicando código não encontrado
    
    Exemplo:
        >>> obter_descricao_natureza_receita('110')
        'Leite fluido pasteurizado ou industrializado, na forma de ultrapasteurizado...'
    
    GATILHO DE MANUTENÇÃO:
    - Para adicionar novos códigos, atualizar TABELA_NATUREZA_RECEITA acima
    """
    codigo_str = str(codigo).strip()
    return TABELA_NATUREZA_RECEITA.get(codigo_str, f'Código {codigo_str} não encontrado na tabela')


def listar_todos_codigos():
    """
    Retorna lista de todos os códigos disponíveis na tabela.
    
    Retorna:
        list: Lista de códigos ordenados numericamente
    
    GATILHO DE MANUTENÇÃO:
    - Esta função retorna automaticamente todos os códigos da tabela
    - Não precisa de manutenção ao adicionar novos códigos
    """
    return sorted(TABELA_NATUREZA_RECEITA.keys(), key=lambda x: int(x))


def exportar_para_dataframe():
    """
    Exporta a tabela para um DataFrame do pandas.
    
    Retorna:
        pd.DataFrame: DataFrame com colunas 'Código' e 'Descrição'
    
    GATILHO DE MANUTENÇÃO:
    - Esta função exporta automaticamente a tabela completa
    - Útil para integração com outras partes do sistema
    """
    import pandas as pd
    
    df = pd.DataFrame([
        {'Código': codigo, 'Descrição': descricao}
        for codigo, descricao in sorted(TABELA_NATUREZA_RECEITA.items(), key=lambda x: int(x[0]))
    ])
    
    return df


# ============================================================================
# APRENDIZADOS E OBSERVAÇÕES
# ============================================================================

"""
APRENDIZADO 1: FORMATO BRASILEIRO
- Sempre usar formato brasileiro para valores monetários
- Exemplo: R$ 1.234,56 (ponto para milhar, vírgula para decimal)

APRENDIZADO 2: CLASSIFICAÇÃO DE OPERAÇÕES
- ENTRADA: CFOP iniciados em 1, 2, 3
- SAÍDA: CFOP iniciados em 5, 6, 7

APRENDIZADO 3: INTEGRAÇÃO COM PARSER
- Esta tabela é usada nos registros M410 (PIS) e M810 (COFINS)
- Substituir código pela descrição na exibição para o usuário

APRENDIZADO 4: ATUALIZAÇÃO PERIÓDICA
- Consultar site da RFB periodicamente para atualizações
- Última atualização oficial: 23/06/2025 (Versão 1.33)
"""

# ============================================================================
# FIM DO ARQUIVO
# ============================================================================
