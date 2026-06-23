# Prompt para Gemini — Fluxograma NAVINCLUD

> Copie e cole este prompt no Gemini 2.5 Flash (ou modelo com geração de imagem) para obter um fluxograma profissional, pronto para inserção em documento de TCC.

---

## INÍCIO DO PROMPT

Crie uma imagem de fluxograma profissional, formato paisagem (proporção 16:9, resolução mínima 3840×2160), com fundo branco, para ser inserido em um Trabalho de Conclusão de Curso (TCC) de nível superior. O fluxograma deve ser LIMPO, LEGÍVEL e com HIERARQUIA VISUAL CLARA.

### ESTILO GERAL

- Fundo: branco puro (#FFFFFF)
- Bordas dos blocos: 2px sólidas, cantos arredondados (8px)
- Fontes: sans-serif limpa (Arial, Helvetica ou similar), sem serifa
- Tamanhos de fonte:
  - Título das fases (backgrounds): 14pt negrito, MAIÚSCULO
  - Título de cada tela: 12pt negrito
  - Texto descritivo dentro dos blocos: 9-10pt
  - Texto de botões / ações: 8pt itálico
- Setas direcionais: 1.5px, pretas (#333333), com pontas sólidas
- Espaçamento generoso entre blocos (mínimo 20px) para evitar poluição visual
- Alinhamento: fluxo PRINCIPAL no centro vertical, ramificações laterais

### PALETA DE CORES (Consistente em todo o fluxograma)

| Elemento | Cor | Uso |
|----------|-----|-----|
| Fase/Fundo de seção | #E8F5E9 (verde claro) | Fundo das fases numeradas |
| Bloco de tela/página | #E3F2FD (azul claro) | Telas, páginas, questionários |
| Bloco de decisão | #FFF3E0 (laranja claro) | Losangos/hexágonos de decisão |
| Bloco RAMO NEGATIVO | #E8F5E9 (verde) | Resultado "Visão Normal → Obrigado" |
| Bloco RAMO POSITIVO | #FCE4EC (rosa claro) | Resultado "Deficiência → Experiência → Obrigado" |
| Bloco RAMO ERRO | #FFEBEE (vermelho claro) | Erro em placa de controle / múltiplos defeitos |
| Bloco de destaque | #F3E5F5 (roxo claro) | Convite para experiência |
| Bloco de botão/ação | #F5F5F5 (cinza claro) | Botões (borda tracejada) |
| Borda de bloco normal | #1565C0 (azul escuro) | Telas |
| Borda de decisão | #E65100 (laranja escuro) | Decisões |
| Borda negativo | #2E7D32 (verde escuro) | 3px — Ramo B |
| Borda positivo | #C62828 (vermelho escuro) | 3px — Ramo C |
| Borda erro | #B71C1C (vermelho) | 2px — Ramos A e D |
| Borda destaque | #7B1FA2 (roxo) | 3px — Convite experiência |

### ESTRUTURA DO FLUXOGRAMA

O fluxograma DEVE ser organizado em 5 colunas verticais principais (sentido: cima para baixo), com 4 ramificações laterais. O título principal no topo: **"NAVINCLUD — Fluxo Completo do Teste de Visão Cromática"** (18pt, negrito, azul #0072B2).

Use CAIXA ALTA para títulos de telas e botões. Use texto normal para descrições e perguntas.

---

### BLOCO 1 — ESQUERDA: FASE 0 — CALIBRAÇÃO DO MONITOR (+ CONEXÃO COM POPUP)

Desenhe um bloco inicial no topo chamado **POPUP NAVINCLUD** retângulo verde escuro (#2E7D32, texto branco).

Duas setas partem dele:
- Seta para a esquerda com rótulo: "🎨 CALIBRAR MONITOR" → leva ao bloco **calibrate.html — NAVINCLUD - Calibração de Monitor**
- Seta para baixo com rótulo: "⚡ INICIAR TESTE" → leva ao bloco do Pré-Teste (BLOCO 2)

**Sub-blocos da Calibração (em sequência vertical):**
1. Bloco de instruções: "Instruções: Temperatura D65 (6500K) | Gamma 2.2 (sRGB) | Luminância 80–120 cd/m² | Desativar modos dinâmicos"
2. Bloco: "4 Testes Visuais: Rampa de Cinza (0–255) | Barras Cores (R,G,B,Y,M,C) | Texto Baixo Contraste | Texto Pequeno 10px"
3. Bloco de validação: "Validação: Todos os elementos devem estar claramente visíveis para prosseguir"
4. Bloco de botão (borda tracejada): "Próximo: Iniciar Teste" → seta voltando para o bloco do Pré-Teste

---

### BLOCO 2 — CENTRAL: FASE 1 — PRÉ-TESTE

Caixa envolvente verde claro (#E8F5E9) com título "FASE 1 — PRÉ-TESTE".

Blocos internos (sequência vertical):
1. **INFORMAÇÕES INICIAIS** — "Estas informações são usadas apenas para fins estatísticos."
2. "Perguntas: Sexo de nascimento (Masculino/Feminino/Outro/Prefiro não responder) | Idade (5–100) | Sala e Turma"
3. Bloco informativo: "18 placas × 15s máximo | 🟢 0–5s: Boa reação | 🟠 6–10s: Pouca dificuldade | 🔴 11–15s: Dificuldade"
4. Bloco botão (borda tracejada): "INICIAR TESTE"

Seta descendente para o BLOCO 3.

---

### BLOCO 3 — CENTRAL: FASE 2 — TESTE DE ISHIHARA (18 PLACAS)

Caixa envolvente verde claro com título "FASE 2 — TESTE DE ISHIHARA (18 placas)".

NÃO liste as 18 placas individualmente. Use um fluxo genérico com indicação de LOOP:

1. Bloco: "Imagem placa Ishihara (250×250) | 'Que número você identifica na imagem?' | Timer 0s → 15s"
2. Bloco: "4 opções em grid 2×2 (ordem aleatória)"
3. Losango de decisão (#FFF3E0): "Acertou?"
   - Seta "Sim" → Bloco de pontuação: "≤5s = +1pt | 6–10s = +0.5pt | 11–15s = +0pt"
   - Seta "Não" / "Não sei" → Bloco vermelho claro: "Incrementa erro do tipo específico"
4. Losango de decisão: "18ª placa?"
   - Seta "Não" → seta curva voltando ao início do loop (próxima placa)
   - Seta "Sim" → seta descendente para BLOCO 4

**IMPORTANTE:** Desenhe uma seta de loop clara (curva, voltando para cima) indicando que as placas 1 a 18 são iteradas.

---

### BLOCO 4 — CENTRAL: FASE 3 — PERCEPÇÃO DO TESTE

Caixa envolvente verde claro com título "FASE 3 — PERCEPÇÃO DO TESTE".

1. Bloco: **"O QUE ACHOU DO TESTE?"** — "Marque todas as opções que se aplicam (obrigatório):"
2. Bloco com 6 checkboxes alinhados em grid 3×2:
   - ☐ Fácil | ☐ Difícil | ☐ Interessante | ☐ Divertido | ☐ Estressante | ☐ Informativo
3. Bloco botão (borda tracejada): "CONTINUAR"

Seta descendente para o BLOCO 5.

---

### BLOCO 5 — CENTRAL: FASE 4 — ANÁLISE DOS RESULTADOS

Caixa envolvente laranja claro (#FFF3E0) com título "FASE 4 — ANÁLISE DOS RESULTADOS".

Três losangos de decisão em sequência vertical:

**Losango 1:** "Erro em placa de controle?"
- Seta "Sim" → RAMO A (para a esquerda)
- Seta "Não" → Losango 2

**Losango 2:** "correctPercent ≥ 90%?"
- Seta "Sim" → RAMO B (para a direita)
- Seta "Não" → Losango 3

**Losango 3:** "Exatamente 1 tipo de defeito?"
- Seta "Sim" → RAMO C (para a direita, abaixo do Ramo B)
- Seta "Não" → RAMO D (para a esquerda, abaixo do Ramo A)

---

### RAMO A (esquerda, topo) — ERRO EM PLACA DE CONTROLE

Caixa envolvente vermelho claro (#FFEBEE).

1. Bloco **RESULTADO**:
   - "Erro em placas de controle — calibração de monitor incorreta."
   - "Por favor, recalibre seu monitor usando a página de calibração e refaça o teste."
2. Dois blocos de botão empilhados:
   - 🔴 **RECALIBRAR MONITOR** (fundo laranja #D55E00, texto branco)
   - 🔄 **REFAZER TESTE**

Ambos com setas voltando para blocos anteriores (Recalibrar → Calibração, Refazer → Pré-Teste).

---

### RAMO B (direita, topo) — VISÃO NORMAL — RESULTADO NEGATIVO ✅

Caixa envolvente verde (#E8F5E9) com borda 3px verde escuro. Título da seção: "RESULTADO NEGATIVO — VISÃO NORMAL".

1. Bloco **QUESTIONÁRIO 02**:
   - "Você já havia feito este teste antes?"
   - ○ Sim ○ Não
2. Bloco botão: "GRAVAR E CONTINUAR"
3. Bloco **PARABÉNS!** (verde escuro, borda 3px):
   - "Obrigado por participar da pesquisa de TCC."
   - "Seus dados foram gravados com sucesso."
4. Bloco botão: "NOVO TESTE" → seta curva voltando ao início do Pré-Teste (BLOCO 2)

**IMPORTANTE:** Coloque um selo visual ou badge verde escrito "NEGATIVO" no canto superior direito deste ramo.

---

### RAMO C (direita, abaixo do Ramo B) — DEFICIÊNCIA DETECTADA — RESULTADO POSITIVO 🔴

Caixa envolvente rosa claro (#FCE4EC) com borda 3px vermelha. Título da seção: "RESULTADO POSITIVO — DEFICIÊNCIA DETECTADA".

Use fundo roxo claro (#F3E5F5, borda 3px roxa) para os blocos de destaque (convite e experiência).

**Sub-etapas (sequência vertical):**

1. Bloco **EXPERIÊNCIA NAVINCLUD** (roxo):
   - "De acordo com seu teste, ele está apontando possível [TIPO_DE_DEFEITO]."
   - "Por isso convidamos você a fazer uma experiência de 2 minutos apenas."
2. Bloco informativo: "Você será convidado a navegar por 2 minutos com o filtro ativado em páginas como Youtube e Google Images."
3. Bloco botão (borda tracejada): "INICIAR"
4. Bloco **experience.html — NAVINCLUD - Experiência em Andamento** (roxo):
   - "Timer: 2:00 → 0:00 (contagem regressiva)"
   - Páginas abertas com filtro:
     - youtube.com
     - Google Images com pesquisa "fotos bonitas e coloridas"
5. Bloco botão vermelho: "ENCERRAR NAVEGAÇÃO" (fundo #DC3545, texto branco)
6. Losango de decisão: "Tempo esgotou ou clicou 'Encerrar'?"
   - Seta "Sim" → próximo bloco
   - (a seta "Não" é implícita — o timer continua)

**Após fim da experiência:**
7. Bloco **AVALIE A EXPERIÊNCIA**: "Todas as perguntas são obrigatórias."
8. Quatro blocos de perguntas empilhados:
   - **P1:** "Você notou melhora na visualização das cores durante a navegação?" — ○ Sim ○ Não
   - **P2:** "A navegação foi fácil com a extensão ligada?" — ○ Muito Fácil ○ Fácil ○ Neutra ○ Difícil
   - **P3:** "Você indicaria a extensão para outras pessoas com a mesma condição?" — ○ Sim ○ Não
   - **P4:** "As cores ficaram mais confortáveis para visualizar?" — ○ Sim ○ Não ○ Prefiro não responder
9. Bloco botão: "GRAVAR AS RESPOSTAS"
10. Bloco **OBRIGADO!** (vermelho escuro, texto branco):
    - "Obrigado pela participação! Seus dados são muito importantes."
    - "(Fechando em 5 segundos...)"
11. Bloco final: "Auto-fecha a janela após 5 segundos → retorna ao popup"

**IMPORTANTE:** Coloque um selo visual ou badge vermelho escrito "POSITIVO" no canto superior direito deste ramo.

---

### RAMO D (esquerda, abaixo do Ramo A) — MÚLTIPLOS DEFEITOS

Caixa envolvente vermelho claro (#FFEBEE).

1. Bloco **RESULTADO**:
   - "Erros em múltiplos tipos de daltonismo detectados."
   - "Recomendamos recalibrar o monitor e refazer o teste."
2. Dois blocos de botão empilhados (mesmo estilo do Ramo A):
   - 🔴 **RECALIBRAR MONITOR**
   - 🔄 **REFAZER TESTE**

---

### INSTRUÇÕES FINAIS DE FORMATAÇÃO

1. **SETAS:** Todas as setas devem ser retas (não curvas, exceto no loop do teste Ishihara), com 1.5px, cor #333.
2. **RÓTULOS DE SETA:** Use texto pequeno (8pt) ao lado das setas onde houver indicação de ação, ex: "Sim", "Não", "abre wizard.html", "salva dados".
3. **BALANCEAMENTO:** Distribua visualmente os 4 ramos de forma equilibrada: Ramos A e D à esquerda, Ramos B e C à direita. O tronco principal (Fases 0–5) deve ficar visivelmente no centro.
4. **ESPACEJAMENTO:** Mantenha distância suficiente entre os ramos para que não se toquem ou se sobreponham.
5. **ÍCONES:** Use ícones simples (🎨, ⚡, 🔴, 🟢, 🔄, ✅, ☐) para enriquecer visualmente — disponíveis em qualquer fonte Unicode.
6. **QUALIDADE PARA TCC:** A imagem final deve parecer um diagrama profissional de engenharia de software, não um rabisco. Consistência de cores, alinhamento preciso, texto perfeitamente legível.
7. **SEM ERROS DE DIGITAÇÃO:** Verifique cada palavra do texto em português antes de gerar. Preste atenção especial a: "Questionário" (com ç), "Obrigado" (com b), "Participação" (com ç), "Experiência" (com ê e i), "Calibração" (com ç), "Incorreta" (com rr), "Visualização" (com ç), "Confortáveis" (com f), "Navegação" (com ç).
8. **ACENTUAÇÃO:** Preserve todos os acentos: à, é, ê, ã, õ, ç. Exemplos corretos: "Informações", "estatísticos", "obrigatório", "já havia feito", "Você será".

---

### RESUMO DOS 4 RAMOS PARA REFERÊNCIA RÁPIDA

| Ramo | Gatilho | Resultado | Cor |
|------|---------|-----------|-----|
| **A** | Erro em placa de controle | "Recalibrar monitor e refaça o teste" | Vermelho |
| **B** | ≥90% acertos + controle ok | "Parabéns! Obrigado por participar" → Novo Teste | Verde ✅ |
| **C** | <90% + 1 tipo de defeito | Convite → Experiência 2min → Questionário → Obrigado! | Rosa/Vermelho 🔴 |
| **D** | <90% + múltiplos defeitos | "Recomendamos recalibrar e refazer" | Vermelho |

---

## FIM DO PROMPT
