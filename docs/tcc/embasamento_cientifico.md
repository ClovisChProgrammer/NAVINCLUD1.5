# Embasamento Científico — Matrizes de Correção de Cores

> **Aviso importante:** Esta ferramenta possui caráter exclusivamente educacional e de simulação. Não substitui exames oftalmológicos ou consultas com profissionais de saúde qualificados. Não constitui diagnóstico médico.
>
> O nome "Ishihara" é utilizado como referência de metodologia científica, não como identificação do produto. Este projeto foi inspirado na metodologia de **Shinobu Ishihara**, oftalmologista japonês que desenvolveu o teste de percepção cromática em 1917. A implementação aqui presente utiliza um conjunto reduzido de 18 pranchas por decisão de design e escopo de software, não replicando o exame clínico completo (que utiliza 24 a 38 pranchas).

## 1. Fundamentos da Visão de Cores

A visão de cores humana baseia-se na existência de três tipos de cones na retina, cada um sensível a uma faixa espectral distinta:

| Cone | Pico de sensibilidade | Cor associada | Nome científico |
|------|----------------------|---------------|-----------------|
| L | ~560 nm | Vermelho (longo) | Eritropsina |
| M | ~530 nm | Verde (médio) | Cloropsina |
| S | ~420 nm | Azul (curto) | Cianopsina |

A **discromatopsia** (daltonismo) ocorre quando um ou mais tipos de cone estão ausentes (dicromacia) ou com sensibilidade alterada (tricromacia anômala).

## 2. Modelo de Confusão de Cores (Vienot, Brettel & Mollon, 1999)

### 2.1 O artigo de referência

**Título:** "Digital Video Colourmaps for Checking the Legibility of Displays by Dichromats"
**Autores:** Françoise Viénot, Hans Brettel, John D. Mollon
**Publicação:** Color Research & Application, 1999
**DOI:** 10.1002/(SICI)1520-6378(199908)24:4<243::AID-COL5>3.0.CO;2-3

### 2.2 Conceito central

Os autores demonstraram que a percepção de cor de um daltônico dicromata pode ser simulada projetando as cores do espaço LMS (Long, Medium, Short) em um **plano de confusão** — o plano de cores que o observador dicromata não consegue distinguir.

Para cada tipo de dicromacia, as cores são projetadas ortogonalmente ao eixo do cone ausente:

```
Protanopia (sem cone L):  projeta no plano M-S
Deuteranopia (sem cone M): projeta no plano L-S
Tritanopia (sem cone S):  projeta no plano L-M
```

### 2.3 Nossa abordagem: o inverso da simulação

Enquanto Viénot et al. **simulam** o que o daltônico vê, a NAVINCLUD **compensa** o deficit aplicando a **transformação inversa** — deslocando as cores da tela para fora do plano de confusão do usuário, de modo que ele perceba a diferença que naturalmente não perceberia.

**Analogia:** Se um rádio não capta determinada frequência, o filtro NAVINCLUD "desloca" o sinal para uma frequência que o rádio consegue captar, preservando o conteúdo da informação visual.

### 2.4 Matrizes de transformação

Cada matriz `feColorMatrix` 5×5 é calculada a partir do espaço LMS:

```
Matriz_Deuteranopia = M_LMS→RGB × Projeção_M × M_RGB→LMS
```

Onde:
- `M_RGB→LMS`: transforma RGB para o espaço de cones (Smith & Pokorny, 1975)
- `Projeção_M`: projeta as cores no plano L-S (elimina o eixo M)
- `M_LMS→RGB`: retorna ao espaço RGB para exibição na tela

## 3. Teoria de Oponência de Cores (Hurvich & Jameson, 1957)

### 3.1 O artigo de referência

**Título:** "An opponent-process theory of color vision"
**Autores:** Leo M. Hurvich, Dorothea Jameson
**Publicação:** Psychological Review, 1957
**DOI:** 10.1037/h0044128

### 3.2 Conceito central

O sistema visual humano processa cores em **canais oponentes** após o estágio dos cones:

```
Canal        +              -
───────────────────────────────
Vermelho-Verde   Vermelho    Verde
Azul-Amarelo     Azul        Amarelo
Preto-Branco     Preto       Branco (luminância)
```

### 3.3 Aplicação no NAVINCLUD

Em vez de simplesmente deslocar matizes no círculo cromático HSV (abordagem adotada por extensões concorrentes), as matrizes do NAVINCLUD atuam **diretamente nos canais oponentes**:

- **Deuteranopia:** intensifica a componente do canal Vermelho-Verde que o cone M deficitário não está processando
- **Protanopia:** desloca o matiz vermelho para uma região que o cone L ausente não compromete a discriminação
- **Tritanopia:** atua no canal Azul-Amarelo, compensando a perda do cone S

**Resultado:** a correção é perceptual, não apenas espectral — o usuário **vê a diferença** mesmo não possuindo o cone biológico para aquela frequência.

## 4. Preservação de Luminância (CIE 1931)

### 4.1 O padrão CIE 1931

A Comissão Internacional de Iluminação (CIE) definiu em 1931 o espaço de cor **CIE XYZ**, que separa a luminância (eixo Y) da cromaticidade (x, y). Subsequentemente, o espaço **CIE L\*a\*b\*** (1976) tornou-se o padrão para medição de diferença perceptual de cor.

### 4.2 Restrição fundamental

Nossa implementação impõe que **L\* (luminância) seja preservada** após a transformação. Isso significa:

```python
L_original = L_transformada  # inalterado
a_original → a_corrigido     # canal vermelho-verde ajustado
b_original → b_corrigido     # canal azul-amarelo ajustado
```

**Por que isso é crítico:** Um daltônico pode não distinguir vermelho de verde, mas **ainda percebe contraste de luminância**. Se a transformação alterar L\*, o usuário pode perder informação visual crucial (como texto sobre fundo colorido).

### 4.3 Validação matemática

Para cada pixel transformado:
```
ΔL* = |L*_original - L*_transformada| < 0.5 (em escala 0-100)
```

Isso garante que a diferença de luminância é **imperceptível ao olho humano** (o limiar de discriminação é ~1 unidade L\*).

## 5. Perfis implementados e base científica

| Perfil | Deficit | Base científica | Canal afetado |
|--------|---------|----------------|---------------|
| Protanopia | Ausência cone L | Vienot 1999, Smith & Pokorny 1975 | Vermelho |
| Protanomaly | Sensibilidade reduzida cone L | DeMarco et al. 1992 | Vermelho (parcial) |
| Deuteranopia | Ausência cone M | Vienot 1999, Smith & Pokorny 1975 | Verde |
| Deuteranomaly | Sensibilidade reduzida cone M | DeMarco et al. 1992 | Verde (parcial) |
| Tritanopia | Ausência cone S | Vienot 1999 | Azul |
| Tritanomaly | Sensibilidade reduzida cone S | Pokorny et al. 1979 | Azul (parcial) |
| Achromatopsia | Ausência todos os cones | Sharpe & Nordby 1990 | Todos (perda total) |
| Achromatomaly | Sensibilidade reduzida todos os cones | Sharpe & Nordby 1990 | Todos (parcial) |

## 6. Referências completas

1. **Viénot, F., Brettel, H., & Mollon, J. D.** (1999). Digital video colourmaps for checking the legibility of displays by dichromats. *Color Research & Application*, 24(4), 243–252.
2. **Hurvich, L. M., & Jameson, D.** (1957). An opponent-process theory of color vision. *Psychological Review*, 64(6), 384–404.
3. **Smith, V. C., & Pokorny, J.** (1975). Spectral sensitivity of the foveal cone photopigments between 400 and 500 nm. *Vision Research*, 15(2), 161–171.
4. **DeMarco, P., Pokorny, J., & Smith, V. C.** (1992). Full-spectrum cone sensitivity functions for X-chromosome-linked anomalous trichromats. *Journal of the Optical Society of America A*, 9(9), 1465–1476.
5. **Pokorny, J., Smith, V. C., & Lutze, M.** (1979). A computer-controlled briefcase anomaloscope. *Documenta Ophthalmologica Proceedings Series*, 19, 67–73.
6. **Sharpe, L. T., & Nordby, K.** (1990). Total colour blindness: An introduction. In *Night Vision* (pp. 253–268). Cambridge University Press.
7. **CIE** (1931). Commission Internationale de l'Éclairage proceedings. Cambridge University Press.
8. **Birch, J.** (2012). Worldwide prevalence of red-green color deficiency. *Journal of the Optical Society of America A*, 29(3), 313–320.
