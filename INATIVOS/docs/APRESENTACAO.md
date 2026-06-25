# NAVINCLUD 2026 - Apresentação TCC

## 1. O QUE É O NAVINCLUD?

O **NAVINCLUD** é uma extensão para Google Chrome desenvolvida como parte de um Trabalho de Conclusão de Curso (TCC). O projeto tem como objetivo auxiliar usuários com deficiências de visão de cores (daltonismo) através de uma abordagem inovadora que combina:

- **Teste Diagnóstico Digital** baseado no método Ishihara
- **Filtros de Correção em Tempo Real** para navegação web
- **Calibração Científica** de monitor para garantir precisão

### Público-Alvo
- Pessoas com daltonismo (cerca de 8% dos homens e 0,5% das mulheres)
- Instituições de ensino para triagem visual
- Pesquisadores na área de acessibilidade digital

---

## 2. O QUE O NAVINCLUD FAZ?

### 2.1. Teste Ishihara Digital (18 Placas)

O sistema gera **18 placas Ishihara sintéticas** usando Python/Pillow, divididas cientificamente:

| Tipo de Placa | Quantidade | Objetivo |
|----------------|------------|----------|
| **Controle** | 2 placas | Validar calibração do monitor |
| **Protanopia** | 2 placas | Detectar cegueira vermelho-verde (completa) |
| **Protanomaly** | 2 placas | Detectar cegueira vermelho-verde (parcial) |
| **Deuteranopia** | 2 placas | Detectar cegueira verde-vermelho (completa) |
| **Deuteranomaly** | 2 placas | Detectar cegueira verde-vermelho (parcial) |
| **Tritanopia** | 2 placas | Detectar cegueira azul-amarelo (completa) |
| **Tritanomaly** | 2 placas | Detectar cegueira azul-amarelo (parcial) |
| **Achromatopsia** | 2 placas | Detectar ausência total de cor |
| **Achromatomaly** | 2 placas | Detectar visão de cores reduzida |

**Diferencial**: O sistema distingue entre **Nopia** (defeito completo) e **Malia** (defeito parcial), oferecendo maior precisão diagnóstica.

### 2.2. Sistema de Pontuação por Tempo

O teste utiliza um cronômetro de **15 segundos por placa** com pontuação diferenciada:

- **0-5 segundos**: 1 ponto (resposta rápida - visão normal)
- **6-10 segundos**: 0,5 pontos (resposta lenta - suspeita)
- **>10 segundos**: 0 pontos (timeout - dificuldade severa)

### 2.3. Filtros de Correção em Tempo Real

A extensão aplica matrizes de transformação de cores (`feColorMatrix` SVG) no navegador:

```javascript
// Exemplo: Matriz para Protanopia
[0.567, 0.433, 0, 0.558, 0.442, 0,
 0.242, 0.758, 0, 0, 0, 0,
 0, 0, 1, 0, 0, 0, 0, 0, 1, 0]
```

**Controles Disponíveis**:
- **Tipo de Filtro**: 8 opções (Protanopia, Deuteranopia, Tritanopia, Acromatopsia + versões Malia)
- **Intensidade**: 0-150% (ajuste fino)
- **Shift**: 0-1,0 (ajuste de brilho)

### 2.4. Calibração Científica de Monitor

Antes do teste, o usuário deve calibrar o monitor segundo padrões científicos:

1. **Temperatura de Cor**: D65 (6500K)
2. **Gama (Gamma)**: 2.2 (padrão sRGB)
3. **Luminância**: 80-120 cd/m²
4. **Desativar**: Brilho automático, contraste dinâmico, modo noturno

**Testes de Validação**:
- Rampa de escala de cinza (0-255)
- Barras de cores primárias (RGB/CMY)
- Textos de baixo contraste
- Texto pequeno (10px)

### 2.5. Experiência de Navegação (2 Minutos)

Após o diagnóstico, usuários com deficiência são convidados a navegar por **2 minutos** com o filtro ativado em:
- Youtube
- Google Images

**Questionários de Avaliação**:
1. "Você notou melhora na visualização dos elementos durante a navegação?" (Sim/Não)
2. "O filtro deixou as imagens mais confortáveis para visualizar?" (Sim/Não)
3. "Você recomendaria esse filtro para outras pessoas com a mesma condição?" (Sim/Não)

### 2.6. Armazenamento e Exportação de Dados

- **Local**: `chrome.storage.local` (histórico de testes `testHistory`)
- **Exportação**: Botão no popup baixa JSON com **todos** os testes da máquina
- **Agregação**: Script Python (`aggregate_results.py`) processa múltiplos JSONs e gera relatório estatístico

---

## 3. COMO USAR O NAVINCLUD?

### 3.1. Pré-requisitos

1. **Google Chrome** atualizado (suporta Manifest V3)
2. **Python 3.7+** com Pillow instalado (`pip install Pillow`)
3. **Monitor calibrado** (seguir instruções em `calibrate.html`)

### 3.2. Instalação e Configuração

#### Passo 1: Gerar Placas Ishihara
```bash
cd NavInclud2026
python main.py
```
**Resultado**: 18 placas geradas na pasta `images/` (`plate1.webp` a `plate18.webp`)

#### Passo 2: Carregar no Chrome
1. Acessar `chrome://extensions`
2. Ativar **"Modo do Desenvolvedor"**
3. Clicar **"Carregar sem compactação"**
4. Selecionar a pasta `NavInclud2026`

#### Passo 3: Calibrar Monitor
1. Clicar no ícone da extensão → **"CALIBRAR MONITOR"**
2. Seguir as instruções de calibração (D65, Gama 2.2, Luminância 80-120 cd/m²)
3. Verificar se todos os testes de validação estão legíveis
4. Clicar **"Próximo: Iniciar Teste"**

### 3.3. Fluxo Completo do Teste

#### Tela 1: Informações Iniciais (Pré-Teste)
- Selecionar **sexo** (Masculino/Feminino/Outro/Prefiro não responder)
- Informar **sala e turma** (ex: 3A, 2B)
- Clicar **"INICIAR TESTE"**

#### Tela 2: Quiz (18 Placas)
- **Tempo**: 15 segundos por placa (cronômetro visual)
- **Ação**: Identificar o número na imagem (ou "Não sei")
- **Cores do Timer**:
  - Verde: >10s (normal)
  - Laranja: 5-10s (aviso)
  - Vermelho: <5s (crítico)

#### Tela 3: Resultados do Diagnóstico

**Cenário A: Sem Deficiência (≥90% acertos)**
- Exibe questionário: "Já fizera o teste antes?" + "O que achou do teste?"
- Finaliza com mensagem de parabenização

**Cenário B: Deficiência Detectada (<90%, 1 tipo)**
- Convite para experiência de 2 minutos
- Clicar **"INICIAR"** → Abre Youtube e Google Images com filtro
- Timer de 2 minutos na tela
- Ao final → Questionário de avaliação da experiência

**Cenário C: Erro em Placas de Controle**
- Alerta: "Calibração incorreta"
- Recomendação: Recalibrar monitor e refazer teste

**Cenário D: Múltiplos Tipos de Erro**
- Alerta: "Erros em múltiplos tipos"
- Recomendação: Recalibrar monitor

#### Tela 4: Experiência de Navegação (2 min)
- **Timer visível no Popup**: "Em Teste: 01:28"
- **Botão "SAIR DO TESTE"**: Interrompe experiência a qualquer momento
- **Abas abertas**: Youtube e Google Images com filtro aplicado
- **Ao final**: Perguntas obrigatórias sobre a experiência

#### Tela 5: Finalização
- **Mensagem de agradecimento**: "Obrigado pela participação! Seus dados são muito importantes."
- **Fechamento automático**: Janela fecha após 5 segundos
- **Sistema pronto**: Novo ciclo disponível

### 3.4. Exportação de Dados

1. Clicar no ícone da extensão
2. Clicar **"EXPORTAR TODOS OS TESTES"**
3. **Arquivo baixado**: `navinclud_3_testes_2026-05-05T14-30-45.json`

**Conteúdo do JSON exportado**:
```json
[
  {
    "testId": "sim-001",
    "timestamp": "2026-05-05T14:30:45.123Z",
    "terminalId": "navinclud-sim-01",
    "preTest": {
      "sexo": "Masculino",
      "turma": "3A"
    },
    "testResults": {
      "totalPlates": 18,
      "correctCount": 14,
      "correctPercent": 77.8,
      "avgReactionTimeMs": 4500,
      "errorsByType": {
        "protanopia": 2,
        "control": 0,
        ...
      },
      "detectedDefect": "protanopia"
    },
    "experiencePostTest": {
      "visualImprovement": "Sim",
      "comfortImprovement": "Sim",
      "recommendFilter": "Sim"
    },
    "appliedFilter": {
      "type": "protanopia",
      "intensity": 100,
      "shift": 0.5,
      "enabled": true
    }
  }
]
```

### 3.5. Agregação de Resultados (Para Pesquisadores)

```bash
# Copiar todos os JSONs exportados para uma pasta
mkdir resultados
cp navinclud_*.json resultados/

# Executar script de agregação
python aggregate_results.py resultados/ --output relatorio_final.txt
```

**Saída**: Relatório consolidado com:
- Distribuição por sexo
- Testes normais vs. deficientes
- Por tipo de deficiência
- Respostas de questionários
- Estatísticas por terminal/máquina

---

## 4. ARQUITETURA TÉCNICA

### 4.1. Tecnologias Utilizadas
- **Frontend**: HTML5, CSS3, JavaScript (Manifest V3)
- **Backend/Scripts**: Python 3.12+ (Pillow para geração de imagens)
- **Extensão**: Chrome Extensions API (Storage, Tabs, Messaging, Windows)

### 4.2. Estrutura de Arquivos
```
NavInclud2026/
├── manifest.json           # Configuração da extensão (Manifest V3)
├── popup.html/js          # Interface principal da extensão
├── wizard.html/js          # Assistente de teste (6 telas)
├── calibrate.html         # Página de calibração de monitor
├── experience.html       # Página de experiência (2 min)
├── background.js          # Service Worker (eventos de abas)
├── content.js            # Injeção de filtro nas páginas
├── main.py               # Geração das placas Ishihara
├── aggregate_results.py  # Agregação de resultados (relatórios)
├── simulate_205.py       # Simulação de 205 pessoas
├── validate_plates.py    # Validação das placas geradas
├── images/               # Placas Ishihara (plate1-18.webp)
└── DocsPesq/            # Documentação de pesquisa
```

### 4.3. Fluxo de Dados
```
Usuário → Pre-Teste → Quiz (18 placas) → Diagnóstico → Experiência (2 min) → Pós-Teste
     ↓              ↓               ↓                ↓                    ↓
  chrome.storage.local → test_${uuid} → testHistoryIds → Export JSON → aggregate_results.py
```

---

## 5. RESULTADOS ESPERADOS (SIMULAÇÃO)

### 5.1. Simulação com 205 Pessoas
- **Base Estatística**: Dados globais (4,34% daltonismo)
- **Distribuição**: 105 homens, 100 mulheres
- **Daltônicos Esperados**: 9 pessoas (8 homens, 1 mulher)

### 5.2. Eficácia do NAVINCLUD
| Indicador | Valor Esperado | Valor Simulado |
|-----------|-----------------|-----------------|
| Sensibilidade | 100% | 100% |
| Especificidade | 100% | 100% |
| Precisão | 100% | 100% |
| Daltônicos Detectados | 9 (4,4%) | 9 (4,4%) |

---

## 6. CONCLUSÃO

O NAVINCLUD 2026 representa uma solução completa e acessível para:
1. **Diagnóstico preciso** de daltonismo via teste Ishihara digital
2. **Correção em tempo real** para navegação web
3. **Coleta sistemática** de dados para pesquisa acadêmica
4. **Interface intuitiva** com fluxo guiado (wizard)

**Diferenciais**:
- Distingue entre Nopia (completo) e Malia (parcial)
- Calibração científica garante validade dos resultados
- Dados exportáveis para análise estatística
- Código aberto e extensível

---

## 7. REFERÊNCIAS

- **Método Ishihara**: Shinobu Ishihara (1917) - Teste de Visão de Cores
- **Padrão sRGB**: IEC 61966-2-1 (Gamma 2.2, D65)
- **Chrome Extensions**: Manifest V3 Documentation
- **Pillow**: Python Imaging Library (Geração de placas)
- **WCAG 2.1**: Diretrizes de Acessibilidade Web

---

**Autor**: Clovis Ch. Programmer / NAVINCLUD Team  
**Repositório**: https://github.com/ClovisChProgrammer/NavInclud2026  
**Versão**: 1.3 (Corrigida - Maio 2026)  
**Licença**: MIT
