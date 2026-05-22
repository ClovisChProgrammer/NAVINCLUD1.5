# CHECKLIST DE TESTES - NAVINCLUD 2026 (Pós-Correção)

## ✅ CORREÇÕES APLICADAS

### 1. `aggregate_results.py` - Validação Robusta
- [x] Filtro de prefixo: `navinclud_`
- [x] Validação de schema: chaves `testId`, `timestamp`, `testResults`
- [x] Tratamento de erros JSON
- **Teste**: `python aggregate_results.py .` → Deve mostrar apenas 2 testes (não ler manifest.json)

### 2. `wizard.js` - Correção de Lógica + Renomeação
- [x] `scores` → `errors` (8 ocorrências)
- [x] Criado objeto `timeouts` para controlar placas não respondidas
- [x] Timeout (15s) incrementa `timeouts[plate.type]`, NÃO `errors`
- [x] Resposta errada incrementa `errors[plate.type]`
- [x] Resposta correta incrementa `correctCount` e `scorePoints`
- **Teste**: Console do wizard durante quiz deve mostrar:
  ```javascript
  console.log('correct:', correctCount, 'errors:', errors, 'timeouts:', timeouts)
  ```

### 3. `validate_plates.py` - Script de Validação Criado
- [x] Verifica existência dos arquivos
- [x] Valida dimensões (500x500)
- [x] Verifica tamanho do arquivo (10KB-200KB)
- [x] Testa brilho médio da imagem
- **Teste**: `python validate_plates.py` → Todas placas OK

---

## 🔍 TESTES MANUAIS NO CHROME

### Pré-requisitos
1. Abrir `chrome://extensions`
2. Ativar "Modo do desenvolvedor"
3. "Carregar sem compactação" → Selecionar pasta `NavInclud2026`
4. Abrir Console (F12) em todas as telas

### Teste 1: Popup
- [ ] Clicar ícone da extensão → Popup abre
- [ ] Selecionar "Protanopia" → Mover sliders → Clicar no toggle
- [ ] Abrir aba do Youtube → Filtro aplicado?
- [ ] Botão "CALIBRAR MONITOR" → Abre `calibrate.html`?
- [ ] Botão "ASSISTENTE DE CALIBRAÇÃO" → Abre `wizard.html`?
- [ ] Botão "EXPORTAR TODOS OS TESTES" → Download de JSON?

### Teste 2: Wizard - Fluxo Normal (≥90% acertos)
- [ ] Preencher sexo e turma → Clicar "INICIAR TESTE"
- [ ] Responder **todas** as 18 placas corretamente (escolher número certo)
- [ ] Deve ir para tela "QUESTIONÁRIO" (normal-post-screen)
- [ ] Responder questionário → "FINALIZAR"
- [ ] Resultado: "Você não errou nenhuma das placas"

### Teste 3: Wizard - Fluxo Deficiência (<90%, 1 tipo)
- [ ] Erros apenas em placas de **Protanopia** (3 e 4)
- [ ] Acertos nas demais (incluindo controle)
- [ ] Deve ir para "EXPERIÊNCIA NAVINCLUD" (experience-invite-screen)
- [ ] Clicar "INICIAR" → Abre Youtube/Google Images com filtro
- [ ] Timer 2min → Fecha abas → Volta para questionário
- [ ] Responder → "ACABEI" → Resultado final

### Teste 4: Wizard - Erro em Placas de Controle
- [ ] Errar placa 1 ou 2 (controle)
- [ ] Deve mostrar: "Erro em placas de controle - calibração incorreta"

### Teste 5: Wizard - Múltiplos Tipos de Erro
- [ ] Erros em Protanopia E Deuteranopia
- [ ] Deve mostrar: "Erros em múltiplos tipos de daltonismo"

---

## 📊 VALIDAÇÃO DE DADOS

### Exportação de Testes
1. No popup → "EXPORTAR TODOS OS TESTES"
2. Arquivo baixado: `navinclud_testes_YYYY-MM-DD.json`
3. Verificar se JSON é válido e contém:
   - `testId` (UUID)
   - `testResults.correctPercent`
   - `testResults.detectedDefect`
   - `testResults.errorsByType` (agora chamado corretamente)

### Teste do aggregate_results.py
```bash
# Renomear arquivo exportado para o padrão
cp navinclud_testes_*.json navinclud_chrome.json

# Executar agregação
python aggregate_results.py . --output relatorio_final.txt

# Verificar: Não deve processar manifest.json ou outros JSONs
```

---

## 🐛 PROBLEMAS CONHECIDOS

1. **Fonte arialbd.ttf**: Pode não existir no Linux/Mac (já tem fallback)
2. **Console do wizard**: Pode mostrar warnings de extensão Chrome (ignorar)
3. **Timing**: Às vezes o filtro demora para aplicar (< 1s)

---

## ✅ CRITÉRIOS DE ACEITAÇÃO

- [ ] `aggregate_results.py` lê apenas arquivos `navinclud_*.json`
- [ ] `wizard.js` não incrementa erros no timeout
- [ ] Variável `errors` reflete apenas respostas erradas
- [ ] Todas as 18 placas validadas (tamanho, dimensões)
- [ ] Fluxo completo testado no Chrome (3 cenários de resultado)
- [ ] Exportação e agregação de dados funcionais

---

**Data da correção**: 05/05/2026  
**Versão**: NavInclud 1.3 (Corrigida)  
**Status**: Pronto para testes em produção
