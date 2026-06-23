# Fluxograma NAVINCLUD — Fluxo Completo do Teste

> Código Mermaid.js para inserção direta em editores compatíveis (Obsidian, GitHub, draw.io, docs com plugin Mermaid).

```mermaid
flowchart TD
    classDef fase fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20
    classDef tela fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    classDef decisao fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#bf360c
    classDef negativo fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px,color:#1b5e20
    classDef positivo fill:#fce4ec,stroke:#c62828,stroke-width:3px,color:#b71c1c
    classDef erro fill:#ffebee,stroke:#b71c1c,stroke-width:2px,color:#c62828
    classDef botao fill:#f5f5f5,stroke:#616161,stroke-width:1px,color:#212121,stroke-dasharray:5 5
    classDef destaque fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#4a148c

    %% ===== FASE 0: CALIBRAÇÃO =====
    subgraph FASE0["FASE 0 — CALIBRAÇÃO DO MONITOR"]
        CALIBRAR_HTML["calibrate.html<br/><strong>NAVINCLUD - Calibração de Monitor</strong>"]:::tela
        INSTRUCOES["Instruções:<br/>• Temperatura D65 (6500K)<br/>• Gamma 2.2 (sRGB)<br/>• Luminância 80–120 cd/m²<br/>• Desativar modos dinâmicos"]:::tela
        TESTES["4 Testes Visuais:<br/>1. Rampa de Cinza (0–255)<br/>2. Barras Cores (R,G,B,Y,M,C)<br/>3. Texto Baixo Contraste<br/>4. Texto Pequeno 10px"]:::tela
        VALIDACAO["Validação:<br/>"Todos os elementos devem estar<br/>claramente visíveis para prosseguir""]:::tela
        BOTAO_PROX["Botão:<br/><strong>Próximo: Iniciar Teste</strong>"]:::botao
    end

    %% ===== FASE 1: PRÉ-TESTE =====
    subgraph FASE1["FASE 1 — PRÉ-TESTE (wizard.html)"]
        PRETESTE["<strong>INFORMAÇÕES INICIAIS</strong><br/>"Estas informações são usadas<br/>apenas para fins estatísticos.""]:::tela
        PERGUNTAS["• Sexo de nascimento<br/>• Idade (5–100)<br/>• Sala e Turma"]:::tela
        INFO_TIMER["Informação do timer:<br/>18 placas × 15s máximo<br/>🟢 0–5s: Boa reação<br/>🟠 6–10s: Pouca dificuldade<br/>🔴 11–15s: Dificuldade"]:::tela
        BOTAO_INICIAR["Botão:<br/><strong>INICIAR TESTE</strong>"]:::botao
    end

    %% ===== FASE 2: TESTE ISHIHARA =====
    subgraph FASE2["FASE 2 — TESTE DE ISHIHARA (18 placas)"]
        PLACA["Exibe placa Ishihara (250×250)<br/>"Que número você identifica<br/>na imagem?"<br/>Timer: 0s → 15s"]:::tela
        OPCOES["4 opções em grid 2×2<br/>(ordem aleatória)"]:::tela
        ACERTO{"Acertou?"}:::decisao
        PONTUACAO["Sim:<br/>• ≤5s → +1 ponto<br/>• 6–10s → +0.5 ponto<br/>• 11–15s → +0 ponto<br/><br/>Não:<br/>• Incrementa erro do tipo"]:::tela
        TIMEOUT["Aos 15s →<br/>avança automaticamente"]:::erro
        PROXIMA{"18ª placa?"}:::decisao
    end

    %% ===== FASE 3: PERCEPÇÃO =====
    subgraph FASE3["FASE 3 — PERCEPÇÃO DO TESTE"]
        PERCEPCAO["<strong>O QUE ACHOU DO TESTE?</strong><br/>"Marque todas as opções que<br/>se aplicam (obrigatório):""]:::tela
        CHECKBOXES["☐ Fácil ☐ Difícil<br/>☐ Interessante ☐ Divertido<br/>☐ Estressante ☐ Informativo"]:::tela
        BOTAO_CONTINUAR["Botão:<br/><strong>CONTINUAR</strong>"]:::botao
    end

    %% ===== FASE 4: ANÁLISE =====
    subgraph FASE4["FASE 4 — ANÁLISE DOS RESULTADOS"]
        CALCULO["Cálculo:<br/>correctPercent = (acertos / 18) × 100"]:::decisao
        DECISAO_CTRL{"Erro em placa<br/>de controle?"}:::decisao
        DECISAO_NORMAL{"correctPercent<br/>>= 90%?"}:::decisao
        DECISAO_1DEF{"Exatamente 1<br/>tipo de defeito?"}:::decisao
    end

    %% ===== RAMO A: ERRO CONTROLE =====
    subgraph RAMOA["RAMO A — ERRO EM PLACA DE CONTROLE"]
        ERRO_CTRL["<strong>RESULTADO</strong><br/><br/>"Erro em placas de controle —<br/>calibração de monitor incorreta."<br/><br/>"Por favor, recalibre seu monitor<br/>usando a página de calibração<br/>e refaça o teste.""]:::erro
        BOTOES_ERRO["🔴 <strong>RECALIBRAR MONITOR</strong><br/>🔄 <strong>REFAZER TESTE</strong>"]:::botao
    end

    %% ===== RAMO B: VISÃO NORMAL (NEGATIVO) =====
    subgraph RAMOB["RAMO B — VISÃO NORMAL (NEGATIVO)"]
        QUEST02["<strong>QUESTIONÁRIO 02</strong><br/>"Você já havia feito<br/>este teste antes?"<br/><br/>○ Sim ○ Não"]:::tela
        BOTAO_GRAVAR["Botão:<br/><strong>GRAVAR E CONTINUAR</strong>"]:::botao
        PARABENS["<strong>PARABÉNS!</strong><br/><br/>"Obrigado por participar<br/>da pesquisa de TCC."<br/><br/>"Seus dados foram<br/>gravados com sucesso.""]:::negativo
        BOTAO_NOVO_TESTE["Botão:<br/><strong>NOVO TESTE</strong>"]:::botao
    end

    %% ===== RAMO C: DEFICIÊNCIA DETECTADA (POSITIVO) =====
    subgraph RAMOC["RAMO C — DEFICIÊNCIA DETECTADA (POSITIVO)"]
        CONVITE["<strong>EXPERIÊNCIA NAVINCLUD</strong><br/><br/>"De acordo com seu teste,<br/>ele está apontando possível<br/>[TIPO_DE_DEFEITO]."<br/><br/>"Por isso convidamos você a<br/>fazer uma experiência de<br/>2 minutos apenas.""]:::destaque
        INFO_EXP[""Você será convidado a navegar<br/>por 2 minutos com o filtro<br/>ativado em páginas como<br/>Youtube e Google Images.""]:::tela
        BOTAO_INICIAR_EXP["Botão:<br/><strong>INICIAR</strong>"]:::botao
        EXPERIENCIA["experience.html<br/><strong>NAVINCLUD - Experiência em Andamento</strong><br/><br/>Timer: 2:00 → 0:00<br/><br/>Páginas abertas:<br/>• youtube.com (com filtro)<br/>• Google Images — "fotos bonitas<br/>&nbsp;&nbsp;e coloridas" (com filtro)"]:::destaque
        BOTAO_ENERRAR["Botão:<br/><strong>ENCERRAR NAVEGAÇÃO</strong>"]:::botao
        DECISAO_EXP{"Tempo esgotou<br/>ou clicou<br/>"Encerrar"?"}:::decisao
        QUEST03["<strong>AVALIE A EXPERIÊNCIA</strong><br/>"Todas as perguntas são obrigatórias.""]:::tela
        Q1["1. "Você notou melhora na<br/>visualização das cores durante<br/>a navegação?"<br/>○ Sim ○ Não"]:::tela
        Q2["2. "A navegação foi fácil<br/>com a extensão ligada?"<br/>○ Muito Fácil ○ Fácil<br/>○ Neutra ○ Difícil"]:::tela
        Q3["3. "Você indicaria a extensão<br/>para outras pessoas com<br/>a mesma condição?"<br/>○ Sim ○ Não"]:::tela
        Q4["4. "As cores ficaram mais<br/>confortáveis para visualizar?"<br/>○ Sim ○ Não ○ Prefiro não responder"]:::tela
        BOTAO_GRAVAR_EXP["Botão:<br/><strong>GRAVAR AS RESPOSTAS</strong>"]:::botao
        OBRIGADO_EXP["<strong>OBRIGADO!</strong><br/><br/>"Obrigado pela participação!<br/>Seus dados são<br/>muito importantes."<br/><br/>(Fechando em 5 segundos...)"]:::positivo
        AUTO_FECHA["Auto-fecha a janela<br/>após 5 segundos"]:::botao
    end

    %% ===== RAMO D: MÚLTIPLOS DEFEITOS =====
    subgraph RAMOD["RAMO D — MÚLTIPLOS DEFEITOS DETECTADOS"]
        MULTI_ERRO["<strong>RESULTADO</strong><br/><br/>"Erros em múltiplos tipos de<br/>daltonismo detectados."<br/><br/>"Recomendamos recalibrar o<br/>monitor e refazer o teste.""]:::erro
        BOTOES_MULTI["🔴 <strong>RECALIBRAR MONITOR</strong><br/>🔄 <strong>REFAZER TESTE</strong>"]:::botao
    end

    %% ===== CONEXÕES =====
    %% Conexão inicial (popup)
    POPUP["POPUP NAVINCLUD"]:::fase

    POPUP -->|"🎨 CALIBRAR MONITOR"| CALIBRAR_HTML
    POPUP -->|"⚡ INICIAR TESTE"| PRETESTE

    %% FASE 0 → FASE 1
    CALIBRAR_HTML --> INSTRUCOES --> TESTES --> VALIDACAO --> BOTAO_PROX
    BOTAO_PROX -->|abre wizard.html| PRETESTE

    %% FASE 1 → FASE 2
    PRETESTE --> PERGUNTAS --> INFO_TIMER --> BOTAO_INICIAR
    BOTAO_INICIAR -->|valida campos| PLACA

    %% FASE 2 (loop 18x)
    PLACA --> OPCOES --> ACERTO
    ACERTO -->|Sim| PONTUACAO
    ACERTO -->|Não| TIMEOUT
    ACERTO -->|"Não sei"| TIMEOUT
    TIMEOUT --> PROXIMA
    PONTUACAO --> PROXIMA
    PROXIMA -->|"Não → próxima placa"| PLACA
    PROXIMA -->|"Sim → avançar"| PERCEPCAO

    %% FASE 3 → FASE 4
    PERCEPCAO --> CHECKBOXES --> BOTAO_CONTINUAR
    BOTAO_CONTINUAR -->|"valida ≥1 checkbox"| CALCULO
    CALCULO --> DECISAO_CTRL

    %% RAMO A
    DECISAO_CTRL -->|"Sim"| ERRO_CTRL --> BOTOES_ERRO

    %% RAMO B (NEGATIVO)
    DECISAO_CTRL -->|"Não"| DECISAO_NORMAL
    DECISAO_NORMAL -->|"Sim → Normal"| QUEST02
    QUEST02 --> BOTAO_GRAVAR
    BOTAO_GRAVAR -->|"salva dados"| PARABENS
    PARABENS --> BOTAO_NOVO_TESTE
    BOTAO_NOVO_TESTE -->|"reseta teste"| PRETESTE

    %% RAMO C (POSITIVO)
    DECISAO_NORMAL -->|"Não"| DECISAO_1DEF
    DECISAO_1DEF -->|"Sim → 1 defeito"| CONVITE
    CONVITE --> INFO_EXP --> BOTAO_INICIAR_EXP
    BOTAO_INICIAR_EXP -->|"abre experience.html<br/>aplica filtro"| EXPERIENCIA
    EXPERIENCIA -->|"timer rodando"| DECISAO_EXP
    BOTAO_ENERRAR -->|"clique manual"| DECISAO_EXP
    DECISAO_EXP -->|"Tempo = 0"| QUEST03
    DECISAO_EXP -->|"Clicou Encerrar"| QUEST03
    QUEST03 --> Q1 --> Q2 --> Q3 --> Q4
    Q4 --> BOTAO_GRAVAR_EXP
    BOTAO_GRAVAR_EXP -->|"salva dados"| OBRIGADO_EXP
    OBRIGADO_EXP --> AUTO_FECHA

    %% RAMO D
    DECISAO_1DEF -->|"Não → múltiplos"| MULTI_ERRO --> BOTOES_MULTI
```

---

## Notas sobre o Fluxo

| Item | Detalhe |
|------|---------|
| **Timer das placas** | Cada placa tem 15s. Aos 15s, avança automaticamente (conta como erro). |
| **Pontuação** | Acerto ≤5s = +1pt \| 6–10s = +0.5pt \| 11–15s = +0pt |
| **Tipos de defeito** | protanopia, protanomalia, deuteranopia, deuteranomalia, tritanopia, tritanomalia, acromatopsia, acromatomalia |
| **Cálculo do filtro** | Se só erro em -omaly (sem -opia): intensity=80, shift=0.6. Padrão: intensity=100, shift=0.5 |
| **Pós-experiência** | A janela de experiência auto-fecha 5s após o "OBRIGADO!". Usuário volta ao popup para novo teste. |
