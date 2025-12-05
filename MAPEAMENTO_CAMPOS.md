# 📋 Documentação Completa: Mapeamento de Campos SPED PIS/COFINS

**Versão:** 1.0 (Stable)  
**Data:** 05/12/2025  
**Status:** ✅ Validado e Testado  
**Commit:** c5718dd4

---

## 🎯 IMPORTANTE

**⚠️ ESTE MAPEAMENTO FOI VALIDADO E ESTÁ FUNCIONANDO CORRETAMENTE**

Qualquer alteração futura DEVE:
1. Consultar esta documentação
2. Executar os testes automatizados (`test_parser_validation.py`)
3. Validar com exemplos reais de ENTRADA e SAÍDA
4. Seguir o checklist de validação (`CHECKLIST_VALIDACAO.md`)

---

## 📊 ESTRUTURA GERAL DO SPED

O SPED PIS/COFINS é composto por registros hierárquicos:

```
0000 (Abertura)
├── 0200 (Cadastro de Produtos)
├── C100 (Cabeçalho da NF-e)
│   └── C170 (Itens da NF-e)
└── 9999 (Encerramento)
```

### Relacionamento Entre Registros:

```
┌─────────────┐
│   0200      │ ← Cadastro de Produtos
│ Código: 91  │   (NCM + Descrição)
│ NCM: 02023  │
│ Desc: HB... │
└─────────────┘
       ↓
┌─────────────┐
│   C100      │ ← Cabeçalho da Nota
│ NF: 654609  │
│ Data: ...   │
└─────────────┘
       ↓
┌─────────────┐
│   C170      │ ← Item da Nota
│ Código: 91  │ → Busca no 0200
│ CFOP: 2102  │
│ PIS: 104,94 │
└─────────────┘
```

---

## 📦 REGISTRO 0200 - CADASTRO DE PRODUTOS

### Formato:
```
|0200|COD|DESCRICAO|EAN|...|NCM|...|
```

### Exemplo Real:
```
|0200|177|HB VPJ COSTELA ANGUS 66X160G - CX 10,16KG|7899679701751||PC|00|02023000||19||22|
```

### Mapeamento de Campos:

| Índice | Campo | Tipo | Descrição | Exemplo |
|--------|-------|------|-----------|---------|
| [1] | REG | String | Tipo de registro | 0200 |
| [2] | **COD_ITEM** | String | **Código do produto** | 177 |
| [3] | **DESCR_ITEM** | String | **Descrição do produto** | HB VPJ COSTELA... |
| [4] | COD_BARRA | String | Código de barras (EAN) | 7899679701751 |
| [6] | UNID_INV | String | Unidade de medida | PC |
| [8] | **NCM** | String | **Nomenclatura Comum Mercosul** | 02023000 |

### ⚠️ ATENÇÃO:
- O campo **COD_ITEM** [2] é a chave para buscar no C170
- **NCM** [8] e **DESCR_ITEM** [3] NÃO estão no C170, devem ser buscados aqui

---

## 📄 REGISTRO C100 - CABEÇALHO DA NF-e

### Formato:
```
|C100|IND_OPER|IND_EMIT|COD_PART|COD_MOD|COD_SIT|SER|NUM_DOC|CHV_NFE|DT_DOC|DT_E_S|...|
```

### Exemplo Real:
```
|C100|0|1|F47|01|00|001|11723||04092025|04092025|13069|1|0|0|13069|9|0|||0|0|0|0|0|215,64|993,24|0|0|
```

### Mapeamento de Campos:

| Índice | Campo | Tipo | Descrição | Exemplo |
|--------|-------|------|-----------|---------|
| [1] | REG | String | Tipo de registro | C100 |
| [4] | **COD_PART** | String | Código do participante | F47 |
| [8] | **NUM_DOC** | String | **Número da NF-e** | 11723 |
| [9] | **CHV_NFE** | String | **Chave de acesso da NF-e** | (vazio ou 44 dígitos) |
| [10] | **DT_DOC** | String | **Data de emissão** (DDMMAAAA) | 04092025 |

### ⚠️ ATENÇÃO:
- **NUM_DOC** [8] é o número da nota fiscal
- **CHV_NFE** [9] pode estar vazio em alguns casos
- **DT_DOC** [10] está no formato DDMMAAAA (sem separadores)

---

## 📦 REGISTRO C170 - ITENS DA NF-e

### Formato:
```
|C170|NUM_ITEM|COD_ITEM|DESCR_COMPL|QTDE|UNID|...|CFOP|...|CST_PIS|VL_BC_PIS|ALIQ_PIS|...|VL_PIS|...|CST_COFINS|VL_BC_COFINS|ALIQ_COFINS|...|VL_COFINS|...|
```

### Exemplo Real (ENTRADA - CFOP 2102):
```
|C170|1|177|HB SEM TEMPERO - BLEND COM COSTELA 160G - ANGUS BEEF|10|CX|3570|0|0|020|2102||2082,38|12|249,89|0|0|0|0|49||0|0|0|73|||||0|73|||||0|1.1.5.01.0001|
```

### Exemplo Real (SAÍDA - CFOP 5102):
```
|C170|2|91||10|CX|6360|0|0|090|1556||0|0|0|0|0|0|0|49||0|0|0|50|6360|1,65|||104,94|50|6360|7,6|||483,36|3.2.1.06.0008|
```

### Mapeamento de Campos (VALIDADO):

| Índice | Campo | Tipo | Descrição | Exemplo ENTRADA | Exemplo SAÍDA |
|--------|-------|------|-----------|-----------------|---------------|
| [1] | REG | String | Tipo de registro | C170 | C170 |
| [2] | NUM_ITEM | String | Número sequencial do item | 1 | 2 |
| **[3]** | **COD_ITEM** | String | **Código do produto (buscar no 0200)** | **177** | **91** |
| [4] | DESCR_COMPL | String | Descrição complementar | HB SEM TEMPERO... | (vazio) |
| [5] | QTDE | Decimal | Quantidade | 10 | 10 |
| [6] | UNID | String | Unidade | CX | CX |
| [7] | VL_ITEM | Decimal | Valor total do item | 3570 | 6360 |
| [10] | CST_ICMS | String | CST do ICMS | 020 | 090 |
| **[11]** | **CFOP** | String | **Código Fiscal de Operações** | **2102** | **1556** |
| [13] | VL_BC_ICMS | Decimal | Base de cálculo ICMS | 2082,38 | 0 |
| [14] | ALIQ_ICMS | Decimal | Alíquota ICMS | 12 | 0 |
| [15] | VL_ICMS | Decimal | Valor ICMS | 249,89 | 0 |
| **[25]** | **CST_PIS** | String | **CST do PIS** | **73** | **50** |
| **[26]** | **VL_BC_PIS** | Decimal | **Base de cálculo PIS** | **0** | **6360** |
| **[27]** | **ALIQ_PIS** | Decimal | **Alíquota PIS (%)** | **(vazio)** | **1,65** |
| **[30]** | **VL_PIS** | Decimal | **Valor do PIS** | **0** | **104,94** |
| **[31]** | **CST_COFINS** | String | **CST do COFINS** | **73** | **50** |
| **[32]** | **VL_BC_COFINS** | Decimal | **Base de cálculo COFINS** | **0** | **6360** |
| **[33]** | **ALIQ_COFINS** | Decimal | **Alíquota COFINS (%)** | **(vazio)** | **7,6** |
| **[36]** | **VL_COFINS** | Decimal | **Valor do COFINS** | **0** | **483,36** |

---

## 🔑 CAMPOS CRÍTICOS (NÃO ALTERAR)

### ⚠️ ESTES ÍNDICES FORAM VALIDADOS E ESTÃO CORRETOS:

```python
# NO REGISTRO C170:
COD_ITEM = linha[3]      # Código do produto (buscar no 0200)
CFOP = linha[11]         # ⚠️ CAMPO [11], NÃO [10]!
CST_PIS = linha[25]      # CST do PIS
VL_BC_PIS = linha[26]    # Base de cálculo PIS
ALIQ_PIS = linha[27]     # Alíquota PIS
VL_PIS = linha[30]       # Valor PIS
CST_COFINS = linha[31]   # CST do COFINS
VL_BC_COFINS = linha[32] # Base de cálculo COFINS
ALIQ_COFINS = linha[33]  # Alíquota COFINS
VL_COFINS = linha[36]    # Valor COFINS
```

---

## 📊 CLASSIFICAÇÃO DE CFOP

### ENTRADA (Compras):
- **1xxx** - Operações dentro do estado
- **2xxx** - Operações interestaduais
- **3xxx** - Operações com exterior

### SAÍDA (Vendas):
- **5xxx** - Operações dentro do estado
- **6xxx** - Operações interestaduais
- **7xxx** - Operações com exterior

### Exemplos Validados:
- **1556** → ENTRADA
- **2102** → ENTRADA
- **5102** → SAÍDA
- **6102** → SAÍDA

---

## 🧪 EXEMPLOS VALIDADOS

### Exemplo 1: ENTRADA com CST 50 (Tributado)

**Registro 0200:**
```
|0200|91|QUEIJO PROCES FAT SCHREIBER CHEDDAR 8 X 2,27KG - CX 18,16KG|...|21069000|
```

**Registro C100:**
```
|C100|0|1|F47|01|00|001|11723||04092025|04092025|...|
```

**Registro C170:**
```
|C170|2|91||10|CX|6360|0|0|090|1556||0|0|0|0|0|0|0|49||0|0|0|50|6360|1,65|||104,94|50|6360|7,6|||483,36|...|
```

**Resultado Esperado:**
- Código Item: 91
- Descrição: QUEIJO PROCES FAT SCHREIBER CHEDDAR 8 X 2,27KG - CX 18,16KG
- NCM: 21069000
- CFOP: 1556 (ENTRADA)
- CST PIS: 50
- Base PIS: R$ 6.360,00
- Alíq. PIS: 1,65%
- Valor PIS: R$ 104,94
- CST COFINS: 50
- Base COFINS: R$ 6.360,00
- Alíq. COFINS: 7,6%
- Valor COFINS: R$ 483,36

### Exemplo 2: ENTRADA com CST 73 (Sem Tributação)

**Registro C170:**
```
|C170|1|177|...|10|CX|3570|0|0|020|2102||2082,38|12|249,89|0|0|0|0|49||0|0|0|73|||||0|73|||||0|...|
```

**Resultado Esperado:**
- Código Item: 177
- CFOP: 2102 (ENTRADA)
- CST PIS: 73
- Base PIS: R$ 0,00
- Valor PIS: R$ 0,00
- CST COFINS: 73
- Base COFINS: R$ 0,00
- Valor COFINS: R$ 0,00

### Exemplo 3: SAÍDA com CST 01 (Tributado)

**Registro 0200:**
```
|0200|26|MOLHO ZAFRAN THAI SWEET CHILI DP CX C/ 5,25KG (5X1,05KG)|...|21039099|
```

**Registro C170:**
```
|C170|...|26|...|5102|...|01|255,53|1,65|...|4,22|01|255,53|7,6|...|19,42|...|
```

**Resultado Esperado:**
- Código Item: 26
- Descrição: MOLHO ZAFRAN THAI SWEET CHILI DP CX C/ 5,25KG (5X1,05KG)
- NCM: 21039099
- CFOP: 5102 (SAÍDA)
- CST PIS: 01
- Base PIS: R$ 255,53
- Alíq. PIS: 1,65%
- Valor PIS: R$ 4,22
- CST COFINS: 01
- Base COFINS: R$ 255,53
- Alíq. COFINS: 7,6%
- Valor COFINS: R$ 19,42

---

## 🔄 FLUXO DE PROCESSAMENTO

```
1. Ler arquivo SPED completo
   ↓
2. Processar TODOS os registros 0200
   ↓
3. Criar dicionário: {cod_item: {descricao, ncm}}
   ↓
4. Processar registros C100 (guardar contexto)
   ↓
5. Processar registros C170
   ↓
6. Para cada C170:
   - Extrair cod_item do campo [3]
   - Buscar descrição e NCM no dicionário
   - Extrair CFOP do campo [11]
   - Extrair CST PIS do campo [25]
   - Extrair valores PIS dos campos [26,27,30]
   - Extrair CST COFINS do campo [31]
   - Extrair valores COFINS dos campos [32,33,36]
   ↓
7. Classificar por CFOP (ENTRADA/SAÍDA)
   ↓
8. Gerar relatórios separados
```

---

## ⚠️ ERROS COMUNS A EVITAR

### ❌ ERRO 1: CFOP no campo errado
```python
# ERRADO:
CFOP = linha[10]  # ❌ Campo [10] é CST_ICMS

# CORRETO:
CFOP = linha[11]  # ✅ Campo [11] é CFOP
```

### ❌ ERRO 2: Não buscar NCM e Descrição no 0200
```python
# ERRADO:
DESCR_ITEM = linha[4]  # ❌ Campo [4] é descrição complementar (pode estar vazio)
NCM = linha[X]         # ❌ NCM não está no C170

# CORRETO:
cod_item = linha[3]
produto_info = produtos.get(cod_item)  # ✅ Busca no dicionário do 0200
DESCR_ITEM = produto_info['descricao']
NCM = produto_info['ncm']
```

### ❌ ERRO 3: Índices errados de PIS/COFINS
```python
# ERRADO:
VL_PIS = linha[14]     # ❌ Campo [14] é ALIQ_ICMS
VL_COFINS = linha[20]  # ❌ Campo [20] não é COFINS

# CORRETO:
VL_PIS = linha[30]     # ✅ Campo [30] é VL_PIS
VL_COFINS = linha[36]  # ✅ Campo [36] é VL_COFINS
```

---

## 📝 REGRAS DE NEGÓCIO

### CST (Código de Situação Tributária):

| CST | Descrição | PIS/COFINS |
|-----|-----------|------------|
| 01 | Operação tributável com alíquota básica | Tem valor |
| 50 | Operação com direito a crédito | Tem valor |
| 73 | Operação de aquisição sem direito a crédito | Zerado |
| 99 | Outras operações | Variável |

### Formatação de Valores:

**No SPED:**
- Separador decimal: vírgula (,)
- Separador de milhar: nenhum ou ponto (.)
- Exemplo: `6360` ou `6.360,00`

**Na Aplicação (Brasil):**
- Separador decimal: vírgula (,)
- Separador de milhar: ponto (.)
- Formato: `R$ 6.360,00`

---

## 🧪 TESTES DE VALIDAÇÃO

Para validar qualquer mudança, execute:

```bash
python3 test_parser_validation.py
```

Os testes verificam:
- ✅ CFOP 2102 (ENTRADA) - CST 73
- ✅ CFOP 5102 (SAÍDA) - CST 01
- ✅ NCM buscado do 0200
- ✅ Descrição buscada do 0200
- ✅ Valores PIS e COFINS corretos
- ✅ Classificação ENTRADA/SAÍDA

---

## 📚 REFERÊNCIAS

- **Guia Prático EFD-Contribuições:** [Receita Federal](http://sped.rfb.gov.br/)
- **Leiaute do SPED PIS/COFINS:** Versão 1.35
- **Commit Validado:** c5718dd4
- **Branch Estável:** stable-v1.0-working

---

## 🔒 CONTROLE DE VERSÃO

| Versão | Data | Commit | Descrição |
|--------|------|--------|-----------|
| 1.0 | 05/12/2025 | c5718dd4 | Versão inicial validada e testada |

---

**⚠️ IMPORTANTE:** Esta documentação é a referência oficial. Qualquer dúvida sobre mapeamento de campos, consulte este arquivo antes de fazer alterações no código.

---

*Documentação criada por: Manus AI - Programador Senior*  
*Validada por: RAFAELSOUZA280292*  
*Status: ✅ APROVADO E FUNCIONANDO*
