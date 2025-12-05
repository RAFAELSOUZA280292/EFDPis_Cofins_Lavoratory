# 📊 Analisador SPED PIS/COFINS - LavoraTax Advisor

**Versão:** 1.0 (Stable)  
**Status:** ✅ Produção  
**URL:** https://efdpiscofinslavoratax.streamlit.app

---

## 🎯 Sobre o Projeto

Aplicação web para análise de arquivos SPED PIS/COFINS, gerando relatórios separados de **Notas Fiscais de Entrada** e **Saída** com todos os campos fiscais necessários.

---

## ✨ Funcionalidades

- ✅ Upload de até 12 arquivos SPED (.txt ou .zip)
- ✅ Processamento automático de registros 0200, C100 e C170
- ✅ Relatórios separados: ENTRADA (CFOP 1,2,3) e SAÍDA (CFOP 5,6,7)
- ✅ Extração completa de campos:
  - Número da NF-e
  - Chave de Acesso
  - Data de Emissão
  - Código do Produto
  - Descrição do Produto (do registro 0200)
  - NCM (do registro 0200)
  - CFOP
  - CST PIS e CST COFINS
  - Base de Cálculo PIS e COFINS
  - Valor PIS e COFINS
- ✅ KPIs por tipo de operação
- ✅ Download de relatórios em CSV
- ✅ Formatação brasileira de valores (R$ 1.234,56)

---

## 🚀 Como Usar

### Online (Recomendado)
Acesse: **https://efdpiscofinslavoratax.streamlit.app**

### Local

1. Clone o repositório:
```bash
git clone https://github.com/RAFAELSOUZA280292/EFDPis_Cofins_Lavoratory.git
cd EFDPis_Cofins_Lavoratory
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
streamlit run app.py
```

---

## 📁 Estrutura do Projeto

```
EFDPis_Cofins_Lavoratory/
├── app.py                          # Aplicação Streamlit principal
├── sped_parser.py                  # Parser SPED PIS/COFINS
├── requirements.txt                # Dependências Python
├── MAPEAMENTO_CAMPOS.md           # 📋 Documentação completa do mapeamento
├── test_parser_validation.py      # 🧪 Testes automatizados
├── CHECKLIST_VALIDACAO.md         # ✅ Checklist para mudanças
└── README.md                       # Este arquivo
```

---

## 🔒 Segurança e Backup

### Branch Stable
- **Branch:** `stable-v1.0-working`
- **Commit:** c5718dd4
- **Status:** Versão validada e funcionando

Para voltar para a versão estável:
```bash
git checkout stable-v1.0-working
```

### Documentação
- **MAPEAMENTO_CAMPOS.md:** Documentação completa dos campos SPED
- **CHECKLIST_VALIDACAO.md:** Checklist obrigatório para mudanças

### Testes Automatizados
Execute antes de qualquer mudança:
```bash
python3.11 test_parser_validation.py
```

Todos os 7 testes devem passar (7/7) ✅

---

## 🧪 Testes

### Executar Testes
```bash
python3.11 test_parser_validation.py
```

### Testes Incluídos
1. ✅ Classificação de CFOP
2. ✅ Estrutura do Parser
3. ✅ Busca no Registro 0200
4. ✅ CFOP no Campo Correto
5. ✅ CST PIS e COFINS
6. ✅ Valores PIS e COFINS
7. ✅ Separação ENTRADA/SAÍDA

---

## 📊 Exemplos Validados

### Entrada (CFOP 2102)
```
Produto: HB VPJ COSTELA ANGUS 66X160G - CX 10,16KG
NCM: 02023000
CFOP: 2102 (ENTRADA)
CST PIS: 73
Valor PIS: R$ 0,00
CST COFINS: 73
Valor COFINS: R$ 0,00
```

### Saída (CFOP 5102)
```
Produto: MOLHO ZAFRAN THAI SWEET CHILI DP CX C/ 5,25KG
NCM: 21039099
CFOP: 5102 (SAÍDA)
CST PIS: 01
Base PIS: R$ 255,53
Valor PIS: R$ 4,22
CST COFINS: 01
Base COFINS: R$ 255,53
Valor COFINS: R$ 19,42
```

---

## 🛠️ Tecnologias

- **Python:** 3.11+
- **Streamlit:** 1.40.0
- **Pandas:** 2.2.3
- **Encoding:** Latin-1 (padrão SPED)

---

## 📝 Mapeamento de Campos (Resumo)

### Registro 0200 (Cadastro de Produtos)
- [2] = Código do Item
- [3] = Descrição do Produto
- [8] = NCM

### Registro C100 (Cabeçalho NF-e)
- [8] = Número do Documento
- [9] = Chave de Acesso
- [10] = Data de Emissão

### Registro C170 (Itens da NF-e)
- [3] = Código do Item (buscar no 0200)
- [11] = CFOP ⚠️
- [25] = CST PIS
- [26] = Base Cálculo PIS
- [30] = Valor PIS
- [31] = CST COFINS
- [32] = Base Cálculo COFINS
- [36] = Valor COFINS

**Documentação completa:** `MAPEAMENTO_CAMPOS.md`

---

## ⚠️ Antes de Modificar o Código

1. ✅ Leia `MAPEAMENTO_CAMPOS.md`
2. ✅ Execute `test_parser_validation.py`
3. ✅ Siga o `CHECKLIST_VALIDACAO.md`
4. ✅ Faça backup do código atual
5. ✅ Teste com arquivo SPED real

---

## 🐛 Troubleshooting

### Problema: CFOP errado (ex: 090 em vez de 2102)
**Solução:** CFOP está no campo [11], não [10]. Verifique `MAPEAMENTO_CAMPOS.md`

### Problema: NCM ou Descrição vazios
**Solução:** Devem ser buscados do registro 0200. Verifique o relacionamento no parser.

### Problema: Valores PIS/COFINS zerados
**Solução:** Verifique se está extraindo dos campos corretos [30] e [36].

### Problema: Testes falhando
**Solução:** Volte para branch stable: `git checkout stable-v1.0-working`

---

## 📈 Roadmap

- [ ] Gráficos visuais de análise
- [ ] Exportação para Excel com formatação
- [ ] Análise de tendências mensais
- [ ] Filtros por período
- [ ] Comparativo entre competências

---

## 👥 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. **Execute os testes:** `python3.11 test_parser_validation.py`
4. **Siga o checklist:** `CHECKLIST_VALIDACAO.md`
5. Commit suas mudanças (`git commit -m 'Add: MinhaFeature'`)
6. Push para a branch (`git push origin feature/MinhaFeature`)
7. Abra um Pull Request

---

## 📄 Licença

Este projeto é de propriedade de **RAFAELSOUZA280292**.

---

## 📞 Suporte

- **Issues:** https://github.com/RAFAELSOUZA280292/EFDPis_Cofins_Lavoratory/issues
- **Documentação:** Veja os arquivos `.md` neste repositório

---

## 🏆 Créditos

**Desenvolvido por:** Manus AI - Programador Senior  
**Validado por:** RAFAELSOUZA280292  
**Data:** 05/12/2025  
**Versão:** 1.0 (Stable)

---

## ⭐ Status do Projeto

![Status](https://img.shields.io/badge/Status-Produção-success)
![Testes](https://img.shields.io/badge/Testes-7%2F7%20Passando-success)
![Versão](https://img.shields.io/badge/Versão-1.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40.0-red)

---

**🔥 PEGOU FOGO! Aplicação funcionando perfeitamente!** 🔥
