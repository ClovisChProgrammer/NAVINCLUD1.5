# Fluxo Completo do NAVINCLUD — Da Extensão ao Relatório Final

## 1. Visão Geral

```
EXTENSÃO (Chrome)          EXPORTAÇÃO (JSON)          ANÁLISE (Python)
─────────────────          ─────────────────         ─────────────────
Popup → perfil             Exportar Dados            aggregate_results.py
  → Filtro SVG na tela       → navinclud_*.json        → CSV + JSON limpo
Wizard → 18 placas                                    inject_plate_timings.py
  → Pre-teste + percepção                               → tempos simulados
Experience (deficientes)                              stats_navinclud.py
  → Questionário pós-teste                              → gráficos + relatório .md
```

## 2. Fluxo do Usuário (Aluno)

### 2.1 Pré-teste

O aluno abre a extensão e clica "Iniciar Teste". O wizard é aberto em uma nova janela:

```
 ┌────────────────────────────────────────────┐
 │         NAVINCLUD — PRÉ-TESTE              │
 │                                            │
 │  Idade:     [____17____]                   │
 │  Sexo:      [Masculino ▼]                  │
 │  Turma:     [3DS A ▼]                      │
 │  Já fez teste de daltonismo antes?         │
 │              ○ Sim  ● Não                  │
 │                                            │
 │  [   INICIAR TESTE   ]                     │
 └────────────────────────────────────────────┘
```

**Dados coletados:** idade (numérico), sexo (nominal), turma (categórico), alreadyTaken (booleano).

### 2.2 Teste de Ishihara (18 placas)

São apresentadas 18 placas numeradas de Ishihara em ordem fixa, 2 de cada tipo:

| Ordem | Placas | Tipo | Finalidade |
|-------|--------|------|------------|
| 1–2 | 1, 2 | Controle | Verificar compreensão do teste |
| 3–4 | 3, 4 | Deuteranopia | Detectar ausência de cone M |
| 5–6 | 5, 6 | Deuteranomaly | Detectar sensibilidade reduzida do cone M |
| 7–8 | 7, 8 | Protanopia | Detectar ausência de cone L |
| 9–10 | 9, 10 | Protanomaly | Detectar sensibilidade reduzida do cone L |
| 11–12 | 11, 12 | Tritanopia | Detectar ausência de cone S |
| 13–14 | 13, 14 | Tritanomaly | Detectar sensibilidade reduzida do cone S |
| 15–16 | 15, 16 | Achromatopsia | Detectar ausência total de cones |
| 17–18 | 17, 18 | Achromatomaly | Detectar sensibilidade reduzida geral |

**Para cada placa:**
1. O canvas renderiza a placa com cores específicas do eixo de confusão testado
2. O aluno digita o número que vê
3. O sistema registra: acerto/erro, tempo de reação (ms)
4. Os números esperados são configurações fixas por placa (ex: placa 1 = 12, placa 2 = 73)

### 2.3 Percepção do Teste

Após as 18 placas, o aluno seleciona sua percepção (multi-select entre 6 opções):

```
 □ Fácil         □ Difícil        □ Divertido
 □ Estressante   □ Interessante   □ Informativo
```

### 2.4 Pós-teste

**Caso o aluno seja NORMAL (≥ 90% de acerto):**
- Mensagem de "Parabéns" é exibida
- Pergunta "Já fez teste de daltonismo antes?" (Sim/Não)
- Wizard se encerra

**Caso o aluno seja POSITIVO (< 90% de acerto):**
- Convite para experimentar a extensão
- Wizard é fechado e uma nova página (experience.html) é aberta
- O aluno interage com elementos visuais com e sem o filtro ativado
- Responde questionário pós-experiência:
  ```
  1. O filtro melhorou sua visualização?  (Sim/Não)
  2. Como avalia a navegação?  (Muito Fácil / Fácil / Neutra / Difícil)
  3. Indicaria a extensão para outros?  (Sim/Não)
  4. As cores ficaram mais confortáveis?  (Sim/Não / Prefiro não responder)
  ```

## 3. Fluxo de Dados (Técnico)

```
       PRE-TESTE                      TESTE                      POS-TESTE
      ┌──────────┐              ┌──────────────┐              ┌────────────┐
      │  idade   │              │  plate 1-18  │              │ percepção  │
      │  sexo    │              │  acerto/erro │              │ alreadyTaken│
      │  turma   │              │  tempo (ms)  │              │ experiência│
      └────┬─────┘              └──────┬───────┘              └─────┬──────┘
           │                          │                           │
           └──────────┬───────────────┘───────────────────────────┘
                      │
                      ▼
           chrome.storage.local.set({ "test_<UUID>": { ... } })
                      │
                      ▼  (experimentador clica "Exportar")
           Download: navinclud_<data>.json
                      │
                      ▼
           analysis/aggregate_results.py
                      │
           ┌──────────┼──────────┐
           ▼          ▼          ▼
     navinclud_   navinclud_   sala_*.json
     agregado     agregado     sala_*.csv
     .json        .csv
                      │
                      ▼
           analysis/inject_plate_timings.py
                      │
                      ▼
           navinclud_com_tempos.json
                      │
                      ▼
           analysis/stats_navinclud.py
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
     relatorio_*.md         *.png (gráficos)
```

## 4. Fluxo do Filtro em Tempo Real

```
USUÁRIO ATIVA FILTRO NO POPUP
         │
         ▼
popup.js → detecta aba ativa (chrome.tabs.query)
         │
         ▼
Envia mensagem: chrome.tabs.sendMessage(tabId, { profile: "deuteranopia" })
         │
         ▼
content.js.onMessage:
  1. Remove SVG filter anterior (se existir)
  2. Cria novo <svg><filter id="navinclud-filtro"><feColorMatrix></svg>
  3. Insere no <body>
  4. Atualiza regra CSS: html { filter: url(#navinclud-filtro) !important; }
         │
         ▼
Chromium GPU process:
  1. Renderiza página em framebuffer intermediário
  2. Aplica matriz 5x5 em cada pixel via GPU shader
  3. Apresenta resultado na tela
         │
         ▼
USUÁRIO VÊ PÁGINA COM CORES CORRIGIDAS
```

## 5. Arquitetura de Componentes

```
manifest.json (MV3)
  │
  ├── background.js  (service worker)
  │     └── Estado global, ciclo de vida
  │
  ├── content.js     (injetado em <all_urls>)
  │     └── Filtro SVG, mensagens do popup
  │
  ├── popup.html + popup.js + popup.css
  │     └── Interface de seleção de perfil
  │
  ├── wizard.html + wizard.js
  │     └── Teste de Ishihara (18 placas)
  │
  ├── experience.html + experience.js
  │     └── Pós-teste para deficientes
  │
  ├── calibrate.html + calibrate.js
  │     └── Calibração de filtro (ajuste fino)
  │
  └── images/ (18 placas .webp)
        └── Assets visuais do teste
```

## 6. Pipeline de Análise (Python)

### 6.1 aggregate_results.py

**Entrada:** Diretório com arquivos JSON exportados da extensão
**Processamento:**
- Leitura de todos os `*.json` do diretório
- Padronização de nomes de turma ("3A" → "3DS A")
- Correção de typos (TypoCorrector)
- Inserção de dados complementares (paciente Raphael)
- Geração de estatísticas descritivas

**Saída:**
- `navinclud_agregado.json` — dados limpos e consolidados
- `navinclud_agregado.csv` — para análise em Excel/SPSS
- `sala_*.json` + `sala_*.csv` — dados separados por sala

### 6.2 inject_plate_timings.py

**Entrada:** `navinclud_agregado.json`
**Processamento:**
- Para cada aluno, gera 18 tempos de reação (1 por placa)
- Normais: ruído gaussiano ~15% ao redor da média real
- Deficientes: penalidade +50–80% nas placas com erro
- Seed determinística por aluno (reprodutível)

**Saída:** `navinclud_com_tempos.json` (dados originais + plateTimingsMs)

### 6.3 stats_navinclud.py

**Entrada:** `navinclud_agregado.json` (ou `navinclud_com_tempos.json` com `--com-tempos`)
**Processamento:**
- Modo interativo ou automático
- Geração de gráficos (matplotlib/seaborn)
- Cálculo de estatísticas descritivas
- Geração de relatório .md com gráficos embutidos

**Saída:**
- `relatorio_estatistico.md` — relatório completo
- `*.png` — gráficos individuais (distribuição, boxplot, correlação, etc.)
