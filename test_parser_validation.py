"""
Testes Automatizados de Validação - Parser SPED PIS/COFINS
Versão: 1.0 (Stable)
Data: 05/12/2025

IMPORTANTE: Execute estes testes ANTES de fazer qualquer alteração no parser!
"""

import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sped_parser import processar_sped, classificar_cfop


def print_header(title):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_test(test_name, passed):
    """Imprime resultado do teste"""
    status = "✅ PASSOU" if passed else "❌ FALHOU"
    print(f"  [{status}] {test_name}")
    return passed


def test_classificacao_cfop():
    """Testa classificação de CFOP"""
    print_header("TESTE 1: Classificação de CFOP")
    
    tests_passed = []
    
    # Testa ENTRADA
    tests_passed.append(print_test(
        "CFOP 1102 → ENTRADA",
        classificar_cfop("1102") == "ENTRADA"
    ))
    tests_passed.append(print_test(
        "CFOP 1556 → ENTRADA",
        classificar_cfop("1556") == "ENTRADA"
    ))
    tests_passed.append(print_test(
        "CFOP 2102 → ENTRADA",
        classificar_cfop("2102") == "ENTRADA"
    ))
    tests_passed.append(print_test(
        "CFOP 3102 → ENTRADA",
        classificar_cfop("3102") == "ENTRADA"
    ))
    
    # Testa SAÍDA
    tests_passed.append(print_test(
        "CFOP 5102 → SAÍDA",
        classificar_cfop("5102") == "SAÍDA"
    ))
    tests_passed.append(print_test(
        "CFOP 6102 → SAÍDA",
        classificar_cfop("6102") == "SAÍDA"
    ))
    tests_passed.append(print_test(
        "CFOP 7102 → SAÍDA",
        classificar_cfop("7102") == "SAÍDA"
    ))
    
    # Testa casos especiais
    tests_passed.append(print_test(
        "CFOP vazio → OUTROS",
        classificar_cfop("") == "OUTROS"
    ))
    
    return all(tests_passed)


def test_parser_estrutura():
    """Testa estrutura básica do parser"""
    print_header("TESTE 2: Estrutura do Parser")
    
    # Cria SPED de teste simples
    sped_teste = """
|0200|91|PRODUTO TESTE A|7899679701751||PC|00|19059090||19||22|
|0200|92|PRODUTO TESTE B|7899679701752||PC|00|21069000||19||22|
|C100|0|1|F47|01|00|001|11723||04092025|04092025|13069|1|0|0|13069|9|0|||0|0|0|0|0|215,64|993,24|0|0|
|C170|1|91||10|CX|6360|0|0|090|1556||0|0|0|0|0|0|0|49||0|0|0|50|6360|1,65|||104,94|50|6360|7,6|||483,36|3.2.1.06.0008|
|C170|2|92||10|CX|3570|0|0|020|2102||2082,38|12|249,89|0|0|0|0|49||0|0|0|73|||||0|73|||||0|1.1.5.01.0001|
|C100|0|1|C51|55|00|001|50706||17092025|18092025|69,91|2|0|0|69,91|0|0|0|0|0|0|0|0|0|1,15|5,32|0|0|
|C170|1|91||5|CX|255,53|0|0|090|5102||0|0|0|0|0|0|0|49||0|0|0|01|255,53|1,65|||4,22|01|255,53|7,6|||19,42|4.1.2.01.0003|
"""
    
    df = processar_sped(sped_teste)
    
    tests_passed = []
    
    # Testa se processou registros
    tests_passed.append(print_test(
        f"Processou registros (esperado: 3, obtido: {len(df)})",
        len(df) == 3
    ))
    
    # Testa se tem as colunas esperadas
    colunas_esperadas = ['NUM_DOC', 'CHV_NFE', 'DT_DOC', 'COD_ITEM', 'DESCR_ITEM', 
                        'NCM', 'CFOP', 'CST_PIS', 'VL_BC_PIS', 'VL_PIS', 
                        'CST_COFINS', 'VL_BC_COFINS', 'VL_COFINS', 'TIPO_OPERACAO', 'VL_TOTAL']
    
    for coluna in colunas_esperadas:
        tests_passed.append(print_test(
            f"Coluna '{coluna}' existe",
            coluna in df.columns
        ))
    
    return all(tests_passed)


def test_busca_0200():
    """Testa busca de NCM e Descrição no registro 0200"""
    print_header("TESTE 3: Busca no Registro 0200")
    
    sped_teste = """
|0200|177|HB VPJ COSTELA ANGUS 66X160G - CX 10,16KG|7899679701751||PC|00|02023000||19||22|
|0200|26|MOLHO ZAFRAN THAI SWEET CHILI DP CX C/ 5,25KG|7899679701752||PC|00|21039099||19||22|
|C100|0|1|F47|01|00|001|654609||06092025|06092025|3570|1|0|0|3570|0|0|0|0|2082,38|249,89|0|0|0|0|0|0|0|
|C170|1|177||10|CX|3570|0|0|020|2102||2082,38|12|249,89|0|0|0|0|49||0|0|0|73|||||0|73|||||0|1.1.5.01.0001|
|C100|0|1|C51|55|00|001|15300||24092025|24092025|255,53|2|0|0|255,53|0|0|0|0|0|0|0|0|0|3,56|16,42|0|0|
|C170|1|26||5|CX|255,53|0|0|090|5102||0|0|0|0|0|0|0|49||0|0|0|01|255,53|1,65|||4,22|01|255,53|7,6|||19,42|4.1.2.01.0003|
"""
    
    df = processar_sped(sped_teste)
    
    tests_passed = []
    
    # Testa primeiro registro (código 177)
    reg1 = df[df['COD_ITEM'] == '177'].iloc[0]
    tests_passed.append(print_test(
        f"NCM do item 177 (esperado: 02023000, obtido: {reg1['NCM']})",
        reg1['NCM'] == '02023000'
    ))
    tests_passed.append(print_test(
        "Descrição do item 177 contém 'HB VPJ COSTELA'",
        'HB VPJ COSTELA' in reg1['DESCR_ITEM']
    ))
    
    # Testa segundo registro (código 26)
    reg2 = df[df['COD_ITEM'] == '26'].iloc[0]
    tests_passed.append(print_test(
        f"NCM do item 26 (esperado: 21039099, obtido: {reg2['NCM']})",
        reg2['NCM'] == '21039099'
    ))
    tests_passed.append(print_test(
        "Descrição do item 26 contém 'MOLHO ZAFRAN'",
        'MOLHO ZAFRAN' in reg2['DESCR_ITEM']
    ))
    
    return all(tests_passed)


def test_cfop_correto():
    """Testa se CFOP está sendo extraído do campo correto [11]"""
    print_header("TESTE 4: CFOP no Campo Correto")
    
    sped_teste = """
|0200|91|PRODUTO TESTE|7899679701751||PC|00|19059090||19||22|
|C100|0|1|F47|01|00|001|11723||04092025|04092025|13069|1|0|0|13069|9|0|||0|0|0|0|0|215,64|993,24|0|0|
|C170|1|91||10|CX|6360|0|0|090|1556||0|0|0|0|0|0|0|49||0|0|0|50|6360|1,65|||104,94|50|6360|7,6|||483,36|3.2.1.06.0008|
|C170|2|91||10|CX|3570|0|0|020|2102||2082,38|12|249,89|0|0|0|0|49||0|0|0|73|||||0|73|||||0|1.1.5.01.0001|
|C100|0|1|C51|55|00|001|50706||17092025|18092025|69,91|2|0|0|69,91|0|0|0|0|0|0|0|0|0|1,15|5,32|0|0|
|C170|1|91||5|CX|255,53|0|0|090|5102||0|0|0|0|0|0|0|49||0|0|0|01|255,53|1,65|||4,22|01|255,53|7,6|||19,42|4.1.2.01.0003|
"""
    
    df = processar_sped(sped_teste)
    
    tests_passed = []
    
    # Verifica CFOPs extraídos
    cfops = df['CFOP'].unique()
    
    tests_passed.append(print_test(
        "CFOP 1556 encontrado (ENTRADA)",
        '1556' in cfops
    ))
    tests_passed.append(print_test(
        "CFOP 2102 encontrado (ENTRADA)",
        '2102' in cfops
    ))
    tests_passed.append(print_test(
        "CFOP 5102 encontrado (SAÍDA)",
        '5102' in cfops
    ))
    
    # Verifica se NÃO pegou o campo [10] (CST_ICMS)
    tests_passed.append(print_test(
        "Não pegou CST_ICMS como CFOP (090, 020)",
        '090' not in cfops and '020' not in cfops
    ))
    
    return all(tests_passed)


def test_cst_pis_cofins():
    """Testa extração de CST PIS e COFINS"""
    print_header("TESTE 5: CST PIS e COFINS")
    
    sped_teste = """
|0200|91|PRODUTO TESTE|7899679701751||PC|00|19059090||19||22|
|C100|0|1|F47|01|00|001|11723||04092025|04092025|13069|1|0|0|13069|9|0|||0|0|0|0|0|215,64|993,24|0|0|
|C170|1|91||10|CX|6360|0|0|090|1556||0|0|0|0|0|0|0|49||0|0|0|50|6360|1,65|||104,94|50|6360|7,6|||483,36|3.2.1.06.0008|
|C170|2|91||10|CX|3570|0|0|020|2102||2082,38|12|249,89|0|0|0|0|49||0|0|0|73|||||0|73|||||0|1.1.5.01.0001|
|C100|0|1|C51|55|00|001|50706||17092025|18092025|69,91|2|0|0|69,91|0|0|0|0|0|0|0|0|0|1,15|5,32|0|0|
|C170|1|91||5|CX|255,53|0|0|090|5102||0|0|0|0|0|0|0|49||0|0|0|01|255,53|1,65|||4,22|01|255,53|7,6|||19,42|4.1.2.01.0003|
"""
    
    df = processar_sped(sped_teste)
    
    tests_passed = []
    
    # Testa CST 50
    reg_cst50 = df[df['CST_PIS'] == '50'].iloc[0]
    tests_passed.append(print_test(
        "CST PIS 50 encontrado",
        reg_cst50['CST_PIS'] == '50'
    ))
    tests_passed.append(print_test(
        "CST COFINS 50 encontrado",
        reg_cst50['CST_COFINS'] == '50'
    ))
    
    # Testa CST 73
    reg_cst73 = df[df['CST_PIS'] == '73'].iloc[0]
    tests_passed.append(print_test(
        "CST PIS 73 encontrado",
        reg_cst73['CST_PIS'] == '73'
    ))
    tests_passed.append(print_test(
        "CST COFINS 73 encontrado",
        reg_cst73['CST_COFINS'] == '73'
    ))
    
    # Testa CST 01
    reg_cst01 = df[df['CST_PIS'] == '01'].iloc[0]
    tests_passed.append(print_test(
        "CST PIS 01 encontrado",
        reg_cst01['CST_PIS'] == '01'
    ))
    tests_passed.append(print_test(
        "CST COFINS 01 encontrado",
        reg_cst01['CST_COFINS'] == '01'
    ))
    
    return all(tests_passed)


def test_valores_pis_cofins():
    """Testa extração de valores PIS e COFINS"""
    print_header("TESTE 6: Valores PIS e COFINS")
    
    sped_teste = """
|0200|91|PRODUTO TESTE|7899679701751||PC|00|19059090||19||22|
|C100|0|1|F47|01|00|001|11723||04092025|04092025|13069|1|0|0|13069|9|0|||0|0|0|0|0|215,64|993,24|0|0|
|C170|1|91||10|CX|6360|0|0|090|1556||0|0|0|0|0|0|0|49||0|0|0|50|6360|1,65|||104,94|50|6360|7,6|||483,36|3.2.1.06.0008|
|C100|0|1|C51|55|00|001|50706||17092025|18092025|69,91|2|0|0|69,91|0|0|0|0|0|0|0|0|0|1,15|5,32|0|0|
|C170|1|91||5|CX|255,53|0|0|090|5102||0|0|0|0|0|0|0|49||0|0|0|01|255,53|1,65|||4,22|01|255,53|7,6|||19,42|4.1.2.01.0003|
"""
    
    df = processar_sped(sped_teste)
    
    tests_passed = []
    
    # Testa valores do primeiro registro (CST 50)
    reg1 = df.iloc[0]
    tests_passed.append(print_test(
        f"Base PIS = 6360,00 (obtido: {reg1['VL_BC_PIS']})",
        abs(reg1['VL_BC_PIS'] - 6360.0) < 0.01
    ))
    tests_passed.append(print_test(
        f"Valor PIS = 104,94 (obtido: {reg1['VL_PIS']})",
        abs(reg1['VL_PIS'] - 104.94) < 0.01
    ))
    tests_passed.append(print_test(
        f"Base COFINS = 6360,00 (obtido: {reg1['VL_BC_COFINS']})",
        abs(reg1['VL_BC_COFINS'] - 6360.0) < 0.01
    ))
    tests_passed.append(print_test(
        f"Valor COFINS = 483,36 (obtido: {reg1['VL_COFINS']})",
        abs(reg1['VL_COFINS'] - 483.36) < 0.01
    ))
    
    # Testa valores do segundo registro (CST 01)
    reg2 = df.iloc[1]
    tests_passed.append(print_test(
        f"Base PIS = 255,53 (obtido: {reg2['VL_BC_PIS']})",
        abs(reg2['VL_BC_PIS'] - 255.53) < 0.01
    ))
    tests_passed.append(print_test(
        f"Valor PIS = 4,22 (obtido: {reg2['VL_PIS']})",
        abs(reg2['VL_PIS'] - 4.22) < 0.01
    ))
    tests_passed.append(print_test(
        f"Valor COFINS = 19,42 (obtido: {reg2['VL_COFINS']})",
        abs(reg2['VL_COFINS'] - 19.42) < 0.01
    ))
    
    return all(tests_passed)


def test_separacao_entrada_saida():
    """Testa separação de ENTRADA e SAÍDA"""
    print_header("TESTE 7: Separação ENTRADA/SAÍDA")
    
    sped_teste = """
|0200|91|PRODUTO TESTE|7899679701751||PC|00|19059090||19||22|
|C100|0|1|F47|01|00|001|11723||04092025|04092025|13069|1|0|0|13069|9|0|||0|0|0|0|0|215,64|993,24|0|0|
|C170|1|91||10|CX|6360|0|0|090|1556||0|0|0|0|0|0|0|49||0|0|0|50|6360|1,65|||104,94|50|6360|7,6|||483,36|3.2.1.06.0008|
|C170|2|91||10|CX|3570|0|0|020|2102||2082,38|12|249,89|0|0|0|0|49||0|0|0|73|||||0|73|||||0|1.1.5.01.0001|
|C100|0|1|C51|55|00|001|50706||17092025|18092025|69,91|2|0|0|69,91|0|0|0|0|0|0|0|0|0|1,15|5,32|0|0|
|C170|1|91||5|CX|255,53|0|0|090|5102||0|0|0|0|0|0|0|49||0|0|0|01|255,53|1,65|||4,22|01|255,53|7,6|||19,42|4.1.2.01.0003|
|C170|2|91||5|CX|100,00|0|0|090|6102||0|0|0|0|0|0|0|49||0|0|0|01|100,00|1,65|||1,65|01|100,00|7,6|||7,60|4.1.2.01.0003|
"""
    
    df = processar_sped(sped_teste)
    
    tests_passed = []
    
    # Separa entrada e saída
    df_entrada = df[df['TIPO_OPERACAO'] == 'ENTRADA']
    df_saida = df[df['TIPO_OPERACAO'] == 'SAÍDA']
    
    tests_passed.append(print_test(
        f"Quantidade ENTRADA = 2 (obtido: {len(df_entrada)})",
        len(df_entrada) == 2
    ))
    tests_passed.append(print_test(
        f"Quantidade SAÍDA = 2 (obtido: {len(df_saida)})",
        len(df_saida) == 2
    ))
    
    # Verifica CFOPs de entrada
    cfops_entrada = set(df_entrada['CFOP'].unique())
    tests_passed.append(print_test(
        "CFOPs de ENTRADA são 1556 e 2102",
        cfops_entrada == {'1556', '2102'}
    ))
    
    # Verifica CFOPs de saída
    cfops_saida = set(df_saida['CFOP'].unique())
    tests_passed.append(print_test(
        "CFOPs de SAÍDA são 5102 e 6102",
        cfops_saida == {'5102', '6102'}
    ))
    
    return all(tests_passed)


def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "=" * 80)
    print("  TESTES AUTOMATIZADOS - PARSER SPED PIS/COFINS")
    print("  Versão: 1.0 (Stable)")
    print("  Data: 05/12/2025")
    print("=" * 80)
    
    all_results = []
    
    # Executa cada teste
    all_results.append(("Classificação de CFOP", test_classificacao_cfop()))
    all_results.append(("Estrutura do Parser", test_parser_estrutura()))
    all_results.append(("Busca no Registro 0200", test_busca_0200()))
    all_results.append(("CFOP no Campo Correto", test_cfop_correto()))
    all_results.append(("CST PIS e COFINS", test_cst_pis_cofins()))
    all_results.append(("Valores PIS e COFINS", test_valores_pis_cofins()))
    all_results.append(("Separação ENTRADA/SAÍDA", test_separacao_entrada_saida()))
    
    # Resumo final
    print_header("RESUMO DOS TESTES")
    
    total_tests = len(all_results)
    passed_tests = sum(1 for _, passed in all_results if passed)
    
    for test_name, passed in all_results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {status} - {test_name}")
    
    print("\n" + "-" * 80)
    print(f"  Total: {passed_tests}/{total_tests} testes passaram")
    print("-" * 80)
    
    if passed_tests == total_tests:
        print("\n  🎉 TODOS OS TESTES PASSARAM! Parser está funcionando corretamente.")
        print("=" * 80)
        return 0
    else:
        print("\n  ⚠️  ALGUNS TESTES FALHARAM! Verifique o parser antes de fazer deploy.")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
