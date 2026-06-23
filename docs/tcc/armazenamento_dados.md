# Armazenamento de Dados — chrome.storage.local

## 1. Abordagem Arquitetural

A extensão NAVINCLUD **não utiliza banco de dados relacional** (SQL) nem servidor externo. Todo armazenamento é feito localmente no navegador do usuário através da API `chrome.storage.local`, um sistema de armazenamento **NoSQL chave-valor** fornecido pelo Chromium.

| Aspecto | Decisão | Justificativa |
|---------|---------|---------------|
| Tipo | NoSQL (chave-valor) | Simplicidade, sem dependências |
| Localização | Perfil do Chrome no disco | Privacidade, LGPD compliance |
| Capacidade | Até 10 MB por extensão | Suficiente para milhares de testes |
| Persistência | Dados permanecem após fechar navegador | Recall do experimento |
| Sincronização | Sem sincronização (intencional) | Dados não saem do dispositivo |

## 2. Estrutura dos Dados

### 2.1 Esquema de chaves

Cada teste é armazenado como uma **chave única** com prefixo `test_` seguido de um UUID v4:

```
test_<uuid> → { ... objeto JSON do teste ... }
```

### 2.2 Objeto de teste (schema)

```json
{
  "testId": "test_a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2026-05-15T10:30:00.000Z",
  "preTest": {
    "nome": "Aluno (anonimizado)",
    "idade": 17,
    "sexo": "Masculino",
    "turma": "3DS A",
    "jaFezTesteAntes": "Nao"
  },
  "testResults": {
    "correctCount": 15,
    "totalPlates": 18,
    "correctPercent": 83.33,
    "avgReactionTimeMs": 4850,
    "plates": [
      { "plateId": 1, "expected": 12, "answered": 12, "correct": true, "reactionTimeMs": 3200 },
      { "plateId": 2, "expected": 73, "answered": 71, "correct": false, "reactionTimeMs": 5400 }
    ],
    "errorsByType": {
      "deuteranopia": { "total": 2, "errors": 0 },
      "deuteranomaly": { "total": 2, "errors": 0 },
      "protanopia": { "total": 2, "errors": 1 },
      "protanomaly": { "total": 2, "errors": 2 },
      "tritanopia": { "total": 2, "errors": 0 },
      "tritanomaly": { "total": 2, "errors": 0 },
      "achromatopsia": { "total": 2, "errors": 0 },
      "achromatomaly": { "total": 2, "errors": 0 },
      "control": { "total": 2, "errors": 0 }
    }
  },
  "perception": ["Dificil", "Estressante"],
  "postTest": {
    "alreadyTaken": "Nao",
    "experienceRating": null
  }
}
```

### 2.3 Estrutura completa no storage

```
chrome.storage.local
├── test_<uuid_1>        → { testId, timestamp, preTest, testResults, perception, postTest }
├── test_<uuid_2>        → { ... }
├── test_<uuid_n>        → { ... }
├── exportCount          → 42 (contador de exportações)
└── lastExportDate       → "2026-05-20T14:22:00.000Z"
```

## 3. Fluxo de Armazenamento

### 3.1 Durante o teste

```
1. wizard.js gera testId (UUID v4)
2. Usuário preenche preTest (idade, sexo, turma)
3. A cada placa respondida:
   - results.plates.push({ plateId, expected, answered, correct, reactionTimeMs })
4. Ao final das 18 placas:
   - testResults.calculados (correctCount, correctPercent, avgReactionTimeMs, errorsByType)
5. Usuário responde perception (multi-select)
6. wizard.js salva: chrome.storage.local.set({ ["test_" + testId]: objetoCompleto })
```

### 3.2 Pós-teste (deficientes)

```
7. experience.js carrega o testId recém-salvo
8. Usuário interage com a página de experiência
9. Usuário responde questionário pós-experiência
10. experience.js ATUALIZA o registro existente:
    chrome.storage.local.set({ ["test_" + testId]: objetoAtualizado })
```

## 4. Exportação dos Dados

O experimentador utiliza a interface de "Exportar dados" no popup da extensão:

```
popup.js → chrome.storage.local.get(null)
         → filtra chaves que começam com "test_"
         → serializa array de testes para JSON
         → cria Blob e dispara download (URL.createObjectURL + <a>.click)
         → arquivo: navinclud_<data>.json
```

## 5. Pipeline de Análise (pós-exportação)

O JSON exportado é processado por scripts Python no diretório `analysis/`:

```
navinclud_<data>.json  (exportado da extensão)
        │
        ▼
aggregate_results.py  →  padroniza turmas, corrige typos, agrega
        │
        ├── navinclud_agregado.json  (dados limpos)
        ├── navinclud_agregado.csv   (para Excel/SPSS)
        └── sala_*.json / sala_*.csv (por sala)
        │
        ▼
inject_plate_timings.py  →  simula tempos de reação por placa
        │
        └── navinclud_com_tempos.json  (para análise temporal)
        │
        ▼
stats_navinclud.py  →  gráficos + relatório estatístico
        │
        ├── relatorio_estatistico.md  (relatório completo)
        └── *.png                     (gráficos individuais)
```

## 6. Considerações de Privacidade (LGPD)

| Requisito LGPD | Implementação NAVINCLUD |
|----------------|------------------------|
| Consentimento | Termo de Assentimento prévio (DocsPesq/) |
| Minimização de dados | Apenas idade, sexo, turma — sem identificadores reais |
| Armazenamento local | Dados nunca saem do navegador sem exportação explícita |
| Controlador dos dados | O experimentador (escola/pesquisador) |
| Portabilidade | Exportação em JSON padrão, processável externamente |

## 7. Limitações e Justificativas

| Limitação | Justificativa |
|-----------|---------------|
| Sem servidor central | Projeto acadêmico sem infraestrutura de servidor; LGPD mais simples |
| 10 MB máximo | 93 testes ocupam ~180 KB — margem para > 5.000 testes |
| Sem replicação | Dados exportáveis a qualquer momento pelo experimentador |
| Sem criptografia | Dados anonimizados e locais; armazenamento criptografado pelo próprio Chrome em disco |
