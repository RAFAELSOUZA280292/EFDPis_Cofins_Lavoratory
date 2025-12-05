# ✅ Checklist de Validação - Mudanças no Parser SPED

**Versão:** 1.0  
**Data:** 05/12/2025  
**Status:** Obrigatório para qualquer alteração

---

## 🎯 QUANDO USAR ESTE CHECKLIST

Use este checklist **ANTES** de fazer qualquer mudança no código relacionada a:
- Parser SPED (`sped_parser.py`)
- Aplicação Streamlit (`app.py`)
- Mapeamento de campos
- Extração de dados
- Cálculos de valores

---

## 📋 CHECKLIST PRÉ-MUDANÇA

### 1. Documentação
- [ ] Li a documentação completa em `MAPEAMENTO_CAMPOS.md`
- [ ] Entendi os índices corretos dos campos
- [ ] Verifiquei exemplos validados na documentação
- [ ] Consultei a estrutura dos registros 0200, C100 e C170

### 2. Backup
- [ ] Branch `stable-v1.0-working` existe e está atualizada
- [ ] Fiz commit do código atual antes de modificar
- [ ] Anotei o hash do último commit funcional

### 3. Testes Atuais
- [ ] Executei `python3.11 test_parser_validation.py`
- [ ] Todos os 7 testes passaram (7/7)
- [ ] Salvei o resultado dos testes como referência

---

## 📋 CHECKLIST DURANTE A MUDANÇA

### 4. Código
- [ ] Não alterei os índices dos campos validados
- [ ] Mantive a busca de NCM e Descrição no registro 0200
- [ ] CFOP continua sendo extraído do campo [11]
- [ ] CST PIS continua no campo [25]
- [ ] Valor PIS continua no campo [30]
- [ ] CST COFINS continua no campo [31]
- [ ] Valor COFINS continua no campo [36]

### 5. Lógica de Negócio
- [ ] Classificação ENTRADA/SAÍDA mantida (CFOP 1,2,3 vs 5,6,7)
- [ ] Conversão de valores numéricos funcionando
- [ ] Formatação brasileira mantida (R$ 1.234,56)
- [ ] Relacionamento 0200 → C170 preservado

---

## 📋 CHECKLIST PÓS-MUDANÇA

### 6. Testes Automatizados
- [ ] Executei `python3.11 test_parser_validation.py`
- [ ] **TODOS os 7 testes passaram (7/7)**
- [ ] Nenhum teste regrediu
- [ ] Não ignorei nenhum teste que falhou

### 7. Validação Manual com Arquivo Real
- [ ] Testei com arquivo SPED real (09.2025_BLUE.txt ou similar)
- [ ] Verifiquei ENTRADA com CFOP 2102
  - [ ] NCM extraído corretamente
  - [ ] Descrição extraída corretamente
  - [ ] CFOP = 2102
  - [ ] CST PIS e COFINS extraídos
  - [ ] Valores corretos
- [ ] Verifiquei SAÍDA com CFOP 5102
  - [ ] NCM extraído corretamente
  - [ ] Descrição extraída corretamente
  - [ ] CFOP = 5102
  - [ ] CST PIS e COFINS extraídos
  - [ ] Valores corretos

### 8. Validação de Totais
- [ ] Total de registros processados está correto
- [ ] Quantidade de ENTRADA está correta
- [ ] Quantidade de SAÍDA está correta
- [ ] Soma de PIS está correta
- [ ] Soma de COFINS está correta

### 9. Interface Streamlit
- [ ] Aplicação inicia sem erros
- [ ] Upload de arquivo funciona
- [ ] Relatório de ENTRADA exibe corretamente
- [ ] Relatório de SAÍDA exibe corretamente
- [ ] KPIs calculados corretamente
- [ ] Download CSV funciona
- [ ] Formatação de valores está correta (R$ 1.234,56)

---

## 📋 CHECKLIST PRÉ-DEPLOY

### 10. Commit e Documentação
- [ ] Commit tem mensagem descritiva
- [ ] Atualizei documentação se necessário
- [ ] Adicionei comentários no código se mudança foi complexa
- [ ] Versão do código está identificada

### 11. Deploy
- [ ] Fiz push para branch de desenvolvimento primeiro
- [ ] Testei no Streamlit Cloud antes de fazer merge para main
- [ ] Avisei o usuário sobre a mudança
- [ ] Mantive branch stable intocada

---

## ⚠️ CRITÉRIOS DE BLOQUEIO

**NÃO FAÇA DEPLOY SE:**

❌ Qualquer teste automatizado falhou  
❌ CFOP não está sendo extraído corretamente  
❌ NCM ou Descrição não estão sendo buscados do 0200  
❌ Valores PIS ou COFINS estão zerados quando deveriam ter valor  
❌ Classificação ENTRADA/SAÍDA está errada  
❌ Formatação de valores está incorreta  
❌ Aplicação Streamlit não inicia  
❌ Não testou com arquivo SPED real  

---

## 🔄 PROCESSO DE ROLLBACK

Se algo der errado após o deploy:

### Opção 1: Voltar para Commit Anterior
```bash
git checkout <hash_do_commit_funcional>
git push origin main --force
```

### Opção 2: Voltar para Branch Stable
```bash
git checkout stable-v1.0-working
git branch -D main
git checkout -b main
git push origin main --force
```

### Opção 3: Reverter Commit Específico
```bash
git revert <hash_do_commit_problemático>
git push origin main
```

---

## 📝 TEMPLATE DE VALIDAÇÃO

Use este template ao fazer mudanças:

```
DATA: ___/___/_____
MUDANÇA: ________________________________________
DESENVOLVEDOR: __________________________________

PRÉ-MUDANÇA:
✅ Documentação lida
✅ Backup feito (commit: _________)
✅ Testes executados (7/7 passaram)

DURANTE MUDANÇA:
✅ Índices de campos não alterados
✅ Lógica de negócio preservada

PÓS-MUDANÇA:
✅ Testes automatizados (7/7 passaram)
✅ Validação manual ENTRADA (CFOP 2102) - OK
✅ Validação manual SAÍDA (CFOP 5102) - OK
✅ Totais conferidos - OK
✅ Interface Streamlit - OK

DEPLOY:
✅ Commit: ________
✅ Push: OK
✅ Streamlit Cloud: OK

OBSERVAÇÕES:
_________________________________________________
_________________________________________________
```

---

## 📞 EM CASO DE DÚVIDA

1. **Consulte a documentação:** `MAPEAMENTO_CAMPOS.md`
2. **Execute os testes:** `python3.11 test_parser_validation.py`
3. **Compare com exemplos validados** na documentação
4. **Volte para branch stable** se necessário
5. **Não faça deploy** se não tiver certeza

---

## 🎯 LEMBRE-SE

> **"Se não passou em TODOS os testes, NÃO faça deploy!"**

> **"Quando em dúvida, consulte a documentação e volte para a versão stable."**

> **"Melhor perder 10 minutos testando do que 2 horas corrigindo em produção."**

---

**✅ CHECKLIST COMPLETO = DEPLOY SEGURO**

---

*Checklist criado por: Manus AI - Programador Senior*  
*Validado por: RAFAELSOUZA280292*  
*Versão: 1.0 (Stable)*
