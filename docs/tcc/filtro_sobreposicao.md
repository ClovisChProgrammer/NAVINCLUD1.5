# Filtro de Correção de Cores — Mecanismo de Sobreposição em Qualquer Tela

## 1. Arquitetura da Extensão

A extensão NAVINCLUD é construída sobre o modelo de arquitetura **Manifest V3** do Google Chrome, composta por três camadas principais que se comunicam por mensagens assíncronas:

| Componente | Arquivo | Função |
|------------|---------|--------|
| Popup | `popup.html` + `popup.js` | Interface do usuário para seleção do perfil de daltonismo |
| Background | `background.js` | Gerenciamento de estado e ciclo de vida da extensão |
| Content Script | `content.js` | Injeção e manipulação do filtro SVG na página ativa |

## 2. O Mecanismo SVG Filter

O núcleo tecnológico do filtro é um **SVG `<filter>` aplicado via CSS global**. Este mecanismo funciona em três etapas:

### 2.1 Definição do filtro (SVG in-page)

Um elemento `<svg>` contendo um `<filter>` com uma matriz `feColorMatrix` é inserido no `<body>` da página:

```svg
<svg xmlns="http://www.w3.org/2000/svg" height="0" width="0">
  <filter id="navinclud-filtro">
    <feColorMatrix type="matrix" values="
      Rr Rg Rb Ra 0
      Gr Gg Gb Ga 0
      Br Bg Bb Ba 0
      0  0  0  1  0
    "/>
  </filter>
</svg>
```

Cada perfil de daltonismo (deuteranopia, protanopia, tritanopia, etc.) possui uma matriz 5×5 específica, derivada do modelo de confusão de cores.

### 2.2 Aplicação via CSS global

O content script injeta uma regra CSS no `document.head`:

```css
html {
  filter: url(#navinclud-filtro) !important;
}
```

### 2.3 Renderização GPU-accelerada

Quando o navegador encontra esta regra CSS, ele:

1. **Renderiza a página completa** em um buffer off-screen (bitmap intermediário)
2. **Aplica a matriz de transformação** pixel a pixel via pipeline de renderização GPU
3. **Exibe o resultado transformado** na tela

Este processo é conhecido como **"filter pipeline" do Chromium** — a transformação ocorre no **GPU process**, não na CPU, resultando em desempenho praticamente idêntico ao da página sem filtro.

## 3. Por que funciona em qualquer página?

O segredo está na combinação de duas permissões do Manifest V3:

1. **`"matches": ["<all_urls>"]`** no content script — instrui o Chrome a executar o `content.js` em TODAS as URLs (http, https, file, etc.)
2. **Seletor CSS `html`** com `!important` — garante que o filtro se aplique ao documento inteiro, independente do CSS da página hospedeira

Quando o usuário seleciona um perfil no popup:

```
popup.js → chrome.tabs.query() → aba ativa
         → chrome.tabs.sendMessage(tabId, {profile: "deuteranopia"})
         → content.js.onMessage → substitui matriz feColorMatrix
         → navegador re-renderiza com nova matriz
```

## 4. Vantagem técnica sobre abordagens concorrentes

| Abordagem | Mecanismo | Performance | Complexidade |
|-----------|-----------|-------------|--------------|
| **SVG Filter (NAVINCLUD)** | GPU pipeline nativa | ✅ Zero overhead | ✅ Simples |
| Canvas 2D pixel por pixel | CPU, loop JavaScript | ❌ Lento (~30fps) | ❌ Complexo |
| CSS mix-blend-mode | Composição de camadas | ⚠️ Médio | ❌ Limitado |
| WebGL fragment shader | GPU customizada | ✅ Rápido | ❌ Muito complexo |

## 5. Limitações conhecidas

- **Iframes:** O filtro não se aplica automaticamente a documentos dentro de iframes de origem cruzada (cross-origin), por restrição de segurança do navegador
- **Canvas/WebGL:** Conteúdo renderizado por Canvas 2D ou WebGL não é afetado pelo filtro CSS, pois esses elementos têm seu próprio pipeline de rendering
- **Vídeos:** Elementos `<video>` podem apresentar comportamento inconsistente entre navegadores

## 6. Referências técnicas

- Chromium Filter Effects Specification: https://drafts.fxtf.org/filter-effects/
- MDN: `<feColorMatrix>` — https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feColorMatrix
- W3C CSS Filter Effects Module Level 1: https://www.w3.org/TR/filter-effects-1/
