# NAVINCLUD 2026TCC

> **Versão de Apresentação TCC** - Curso de Desenvolvimento de Sistemas  
> **Instituição**: ETEC Comendador João Rays de Barra Bonita/SP  
> **Autores**: Clóvis Ch. e Alberto B.

---

## ⚠️ AVISO MÉDICO

Embora as placas de Ishihara presentes nesta extensão tenham sido produzidas com o máxima fidelidade ao método original, **esta extensão não substitui a opinião de um médico competente**. Em caso de suspeita de problemas de visão de cores, **consulte um especialista**.

---

## 1. O QUE É O NAVINCLUD?

O **NAVINCLUD** é uma extensão para Google Chrome desenvolvida como parte de um Trabalho de Conclusão de Curso (TCC) do curso técnico em **Desenvolvimento de Sistemas** na **ETEC Comendador João Rays de Barra Bonita/SP**.

**Autores/Desenvolvedores**: 
- Clóvis Ch. (Pesquisa e desenvolvimento)
- Alberto B. (Pesquisa e documentação)

**Orientadores**
2º DS - Profa. Mestre Rosiene
3º DS - Prof. Mestre Gallo Junior

O projeto tem como objetivo auxiliar usuários com deficiências de visão de cores (daltonismo) através de uma abordagem inovadora que combina:

- **Teste Diagnóstico Digital** baseado no método Ishihara
- **Filtros de Correção em Tempo Real** para navegação web
- **Calibração Científica** de monitor para garantir precisão

### Público-Alvo
- Pessoas com daltonismo (cerca de 8% dos homens e 0,5% das mulheres)
- Instituições de ensino para triagem visual
- Pesquisadores na área de acessibilidade digital

---

## 2. OBJETIVOS DE DESENVOLVIMENTO SUSTENTÁVEL (ODS)

Além da tecnologia, a proposta conecta-se aos **Objetivos de Desenvolvimento Sustentável (ODS)** da ONU:

- **ODS 3** (Saúde e Bem-estar): Reduz o esforço visual de daltônicos
- **ODS 4** (Educação de Qualidade): Democratiza o acesso à informação visual
- **ODS 8** (Trabalho Decente): Amplia condições de empregabilidade para daltônicos
- **ODS 9** (Inovação e Infraestrutura): Traz inovação na tecnologia de acessibilidade
- **ODS 10** (Redução das Desigualdades): Garante equidade no uso da internet

### Conformidade Legal
- **LGPD** (Lei Geral de Proteção de Dados): Dados armazenados localmente via `chrome.storage.local`
- **ADA** (Americans with Disabilities Act): Extensão pode "ultrapassar fronteiras" ao oferecer acessibilidade digital

### Visão Futura
- Implementação de opções **bilíngues, trilíngues ou polilíngues**
- Expansão para outras plataformas além do Chrome

---

## 3. O QUE O NAVINCLUD FAZ?

### 3.1. Teste Ishihara Digital (18 Placas)

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

### 3.2. Sistema de Pontuação por Tempo

O teste utiliza um cronômetro de **15 segundos por placa** com pontuação diferenciada:

- **0-5 segundos**: 1 ponto (resposta rápida - visão normal)
- **6-10 segundos**: 0,5 pontos (resposta lenta - suspeita)
- **>10 segundos**: 0 pontos (timeout - dificuldade severa)

> **Importante**: O tempo de reação é fundamental para o diagnóstico (sugestão de Gallo).

### 3.3. Filtros de Correção em Tempo Real

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

### 3.4. Calibração Científica de Monitor

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

### 3.5. Experiência de Navegação (2 Minutos)

Após o diagnóstico, usuários com deficiência são convidados a navegar por **2 minutos** com o filtro ativado em:
- Youtube
- Google Images

**Questionários de Avaliação**:
1. "Você notou melhora na visualização dos elementos durante a navegação?" (Sim/Não)
2. "O filtro deixou as imagens mais confortáveis para visualizar?" (Sim/Não)
3. "Você recomendaria esse filtro para outras pessoas com a mesma condição?" (Sim/Não)

### 3.6. Armazenamento e Exportação de Dados

- **Local**: `chrome.storage.local` (histórico de testes `testHistory`)
- **Exportação**: Botão no popup baixa JSON com **todos** os testes da máquina
- **Agregação**: Script Python (`aggregate_results.py`) processa múltiplos JSONs e gera relatório estatístico

---

## 4. COMO USAR O NAVINCLUD?

### 4.1. Pré-requisitos

1. **Google Chrome** atualizado (suporta Manifest V3)
2. **Python 3.7+** com Pillow instalado (`pip install Pillow`)
3. **Monitor calibrado** (seguir instruções em `calibrate.html`)

### 4.2. Instalação e Configuração

#### Passo 1: Gerar Placas Ishihara
```bash
cd Navinclud2026TCC
python main.py
```
**Resultado**: 18 placas geradas na pasta `images/` (`plate1.webp` a `plate18.webp`)

#### Passo 2: Carregar no Chrome
1. Acessar `chrome://extensions`
2. Ativar **"Modo do Desenvolvedor"**
3. Clicar **"Carregar sem compactação"**
4. Selecionar a pasta `Navinclud2026TCC`

#### Passo 3: Calibrar Monitor
1. Clicar no ícone da extensão → **"CALIBRAR MONITOR"**
2. Seguir as instruções de calibração (D65, Gama 2.2, Luminância 80-120 cd/m²)
3. Verificar se todos os testes de validação estão legíveis
4. Clicar **"Próximo: Iniciar Teste"**

> **Sugestão**: Na primeira tela (pré-teste), perguntar também a **IDADE** (conforme sugestão de Gallo).

### 4.3. Fluxo Completo do Teste

#### Tela 1: Informações Iniciais (Pré-Teste)
- Selecionar **sexo** (Masculino/Feminino/Outro/Prefiro não responder)
- Informar **idade** (sugestão: incluir campo idade)
- Informar **sala e turma** (ex: 3A, 2B)
- Clicar **"INICIAR TESTE"**

#### Tela 2: Quiz (18 Placas)
- **Tempo**: 15 segundos por placa (cronômetro visual)
- **Ação**: Identificar o número na imagem (ou "Não sei")
- **Cores do Timer**:
  - Verde: >10s (normal)
  - Laranja: 5-10s (aviso)
  - Vermelho: <5s (crítico)

> **Alerta**: O tempo de reação é fundamental para o diagnóstico!

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

### 4.4. Exportação de Dados

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
      "idade": 25,
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
      "detectedDefect": "protanopia",
      "testPerception": ["Fácil", "Interessante"]
    },
    "normalPostTest": {
      "alreadyTaken": "Não"
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

### 4.5. Agregação de Resultados (Para Pesquisadores)

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

## 5. ARQUITETURA TÉCNICA

### 5.1. Tecnologias Utilizadas

| Tecnologia | Aplicação |
|------------|-------------|
| **HTML5/CSS3/JS** | Frontend da extensão (Manifest V3) |
| **Python 3.12+** | Geração de placas (Pillow), agregação de dados, simulação |
| **Chrome API** | Storage, Downloads, Messaging, Windows |
| **SVG feColorMatrix** | Filtros de correção de cores em tempo real |
| **Selenium + Chrome for Testing** | Simulador automatizado de testes |

### 5.2. Estrutura de Arquivos

```
Navinclud2026TCC/
├── manifest.json               # Configuração (Manifest V3)
├── popup.html/js/css           # Interface principal
├── wizard.html/js              # Assistente de teste (6 telas)
├── calibrate.html/js           # Calibração de monitor
├── experience.html/js          # Experiência de navegação
├── content.js                  # Injeção de filtros em tempo real
├── background.js               # Service Worker
├── main.py                     # Geração de placas Ishihara
├── simulate_5salas_testes.py   # Simulador automatizado (Selenium)
├── validate_plates.py          # Validação das placas
├── aggregate_results.py        # Agregação de resultados
├── converter_resultados.py     # Conversão de formatos
├── extrair_dados.py            # Extração de dados do storage
├── nav_charts.py               # Geração de gráficos
├── nav_query.py                # Consultas aos dados
├── nav_export.py               # Exportação de dados
├── build-cws-zip.ps1           # Script de build para CWS
├── snapshot.py                 # Sistema de snapshots
├── PRIVACY_POLICY.md           # Política de privacidade
├── AGENTS.md                   # Instruções para IA
├── images/                     # 18 placas (plate1-18.webp)
├── gui/                        # Recursos de interface
├── snapshots/                  # Snapshots do projeto
└── DocsPesq/                   # Documentação de pesquisa
```

### 5.3. Fluxo de Dados

```
Usuário → Pré-Teste → Quiz (18 placas) → Diagnóstico → Experiência → Pós-Teste
     ↓              ↓               ↓                ↓                    ↓
  chrome.storage.local → test_${uuid} → testHistoryIds → Export JSON → aggregate_results.py
```

---

## 6. RESULTADOS ESPERADOS (SIMULAÇÃO)

### 6.1. Simulação com 205 Pessoas
- **Base Estatística**: Dados globais (4,34% daltonismo)
- **Distribuição**: 105 homens, 100 mulheres
- **Daltônicos Esperados**: 9 pessoas (8 homens, 1 mulher)

### 6.2. Eficácia do NAVINCLUD

| Indicador | Valor Esperado | Valor Simulado |
|-----------|-----------------|-----------------|
| Sensibilidade | 100% | 100% |
| Especificidade | 100% | 100% |
| Precisão | 100% | 100% |
| Daltônicos Detectados | 9 (4,4%) | 9 (4,4%) |

### 6.3. Simulação com 58 Pessoas
- **Base**: 30 homens, 28 mulheres
- **Daltônicos Esperados**: 3 pessoas (5,2%)
- **Terminais**: Laranja_Vermelha, Carro_Preto, Blusa_Verde

### 6.4. Simulador Automatizado (100 Alunos — 5 Salas)
O script `simulate_5salas_testes.py` automatiza testes com **100 alunos** distribuídos em **5 salas**, usando Selenium + Chrome for Testing:

| Sala | Total | M/F | Deficientes |
|------|-------|-----|-------------|
| 3A   | 19    | 16M/3F | 2 deuteran (M) |
| 3B   | 17    | 13M/4F | 1 deuteran (M), 1 tritan (M) |
| 2A   | 22    | 16M/6F | nenhum |
| 2B   | 24    | 16M/8F | 1 deuteran (M), 1 protan (M) |
| 1A   | 18    | 11M/7F | 1 protan (F) |
| **Total** | **100** | **72M/28F** | **7 deficientes** |

**Recursos**: reações realistas (2-11s), pesos por idade, percepção variada, alreadyTaken 8%, questionário pós-experiência para deficientes, export manual após cada sala, sistema de retomo com `--resume` e `--skip`.

---

## 7. DIFERENCIAIS DA VERSÃO 2026TCC

1. **Nopia vs Malia**: Distingue defeitos completos (Nopia) de parciais (Malia)
2. **Pontuação por Tempo**: 1 ponto (0-5s), 0,5 (6-10s), 0 (>10s)
3. **Shift como Brilho**: Ajuste de 0-1 para correção de luminosidade
4. **Estrutura de Dados Consistente**: `testResults` unificado
5. **Agregação Científica**: Relatórios com estatísticas por sexo, turma e terminal
6. **Conformidade com LGPD e ADA**: Dados armazenados localmente
7. **Simulador Automatizado**: 100 alunos, 5 salas, com Selenium e retomo
8. **Build para Chrome Web Store**: Script `build-cws-zip.ps1` para submissão CWS

---

## 8. REFERÊNCIAS

- **Método Ishihara**: Shinobu Ishihara (1917) - Teste de Visão de Cores
- **Padrão sRGB**: IEC 61966-2-1 (Gamma 2.2, D65)
- **Chrome Extensions**: Manifest V3 Documentation
- **Pillow**: Python Imaging Library (Geração de placas)
- **WCAG 2.1**: Diretrizes de Acessibilidade Web

---

## 9. CONCLUSÃO

O **NAVINCLUD 2026TCC** representa uma solução completa para:
1. ✅ Diagnóstico preciso via teste Ishihara digital
2. ✅ Correção em tempo real para navegação web
3. ✅ Coleta sistemática de dados para pesquisa acadêmica
4. ✅ Interface intuitiva com fluxo guiado
5. ✅ Contribuição inovadora para o curso de Desenvolvimento de Sistemas

**Diferenciais**:
- Distingue entre Nopia (completo) e Malia (parcial)
- Calibração científica garante validade dos resultados
- Dados exportáveis para análise estatística
- Código aberto e extensível

---

## 10. INFORMAÇÕES DO PROJETO

**Autores**: 
- Clóvis Ch. (Desenvolvedor Principal)
- Alberto B. (Co-autor)

**Instituição**: ETEC Comendador João Rays de Barra Bonita/SP  
**Curso**: Desenvolvimento de Sistemas  
**Repositório**: https://github.com/ClovisChProgrammer/Navinclud2026TCC  
**Versão**: 1.4 (Junho 2026)  
**Licença**: MIT

---

## 11. AGRADECIMENTOS

Agradecemos à coordenação da **ETEC Comendador João Rays de Barra Bonita/SP** pelo suporte durante o desenvolvimento deste TCC, e a todos os participantes das simulações que contribuíram para a validação da extensão.

---

## 12. DICAS PARA O MÁXIMO PROVEITO

1. **Sempre realize a calibração antes do teste** (D65, Gamma 2.2)
2. **Responda o questionário pós-teste honestamente**
3. **Para daltônicos**: teste diferentes intensidades de filtro (80-100%)
4. **Exporte os dados para acompanhamento estatístico**
5. **Utilize em pesquisas acadêmicas citando devidamente os autores**
6. **Consulte um especialista** em caso de diagnóstico positivo

---

**Versão de Apresentação TCC - Junho 2026**
