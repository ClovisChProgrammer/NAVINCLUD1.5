# Guia de Submissão — Chrome Web Store (NAVINCLUD v1.5)

## Pré-requisitos

- Conta de desenvolvedor: **US$ 5,00** (taxa única) em [chrome.google.com/webstore/devconsole](https://chrome.google.com/webstore/devconsole)
- ZIP da extensão gerado (veja passo a passo abaixo)
- Screenshots (1280×800 ou 640×400)
- Política de privacidade publicada em uma URL

---

## 1. Gerar o ZIP de Submissão

```powershell
# Na raiz do projeto (G:\...\NAVINCLUD1.5):
$src = Get-Location
$zip = Join-Path $src "navinclud-cws.zip"
Add-Type -AssemblyName System.IO.Compression.FileSystem
$files = @(
    "manifest.json", "popup.html", "popup.js", "popup.css",
    "background.js", "content.js",
    "wizard.html", "wizard.js",
    "calibrate.html", "calibrate.js",
    "icon16.png", "icon48.png", "icon128.png"
)
$dist = Join-Path $src "_cws_build"
if (Test-Path $dist) { Remove-Item -Recurse -Force $dist }
New-Item -ItemType Directory -Path $dist | Out-Null
foreach ($f in $files) {
    Copy-Item -Path (Join-Path $src $f) -Destination (Join-Path $dist $f)
}
$imgDir = Join-Path $dist "images"
New-Item -ItemType Directory -Path $imgDir -Force | Out-Null
Get-ChildItem -Path (Join-Path $src "images") -Filter "*.webp" | Copy-Item -Destination $imgDir
if (Test-Path $zip) { Remove-Item -Force $zip }
[System.IO.Compression.ZipFile]::CreateFromDirectory($dist, $zip, [System.IO.Compression.CompressionLevel]::Optimal, $false)
Remove-Item -Recurse -Force $dist
Write-Host "ZIP criado: $zip"
```

O ZIP conterá: `manifest.json`, `popup.{html,js,css}`, `background.js`, `content.js`, `wizard.{html,js}`, `calibrate.{html,js}`, `icon{16,48,128}.png`, `images/*.webp`.

---

## 2. Acessar o CWS Dashboard

1. Vá para [chrome.google.com/webstore/devconsole](https://chrome.google.com/webstore/devconsole)
2. Faça login com a **Conta Google do desenvolvedor**
3. Clique em **"Novo item"** (ou selecione o item existente se for uma atualização)

---

## 3. Preencher os Campos

### Aba "Listing" (Listagem)

| Campo | Valor |
|-------|-------|
| **Product name** | `NAVINCLUD - Acessibilidade Cromática` |
| **Short description** (máx. 132 caracteres) | `Filtros dinâmicos de correção de cores para pessoas com daltonismo e acromatopsia.` |
| **Detailed description** | `O NAVINCLUD ajuda pessoas com dificuldades de discriminação de cores através de um teste rápido de 18 placas Ishihara. Ao final, se identificada alguma dificuldade, a extensão aplica automaticamente filtros de correção cromática em tempo real em qualquer página web.\n\nRecursos:\n• Teste cromático digital baseado no método Ishihara\n• Filtros ajustáveis (intensidade e shift de cor)\n• Calibração de monitor integrada\n• Suporte a protanopia, protanomalia, deuteranopia, deuteranomalia, tritanopia, tritanomalia, acromatopsia e acromatomalia\n\nComo usar:\n1. Abra o popup da extensão e clique em "INICIAR TESTE"\n2. Identifique os números em 18 placas de cores\n3. Veja o resultado: se houver indicação de dificuldade, o filtro é aplicado automaticamente\n4. Ajuste a intensidade e o shift conforme sua preferência\n\nPrivacidade: Nenhum dado é coletado, armazenado em servidores ou compartilhado com terceiros. Todas as configurações ficam apenas no seu navegador.` |
| **Category** | `Accessibility` |
| **Language** | `Português (Brasil)` |
| **Homepage URL** | `https://clovischprogrammer.github.io/Navinclud1.5/` |
| **Privacy policy URL** | `https://clovischprogrammer.github.io/Navinclud1.5/privacy` |

### Aba "Store listing images"

Faça upload das **5 screenshots** (você precisará gerar novas — as antigas mostram o wizard com TCC references):

1. **Popup**: popup da extensão com os controles (título, botões, sliders, toggle)
2. **Teste em andamento**: wizard mostrando uma placa Ishihara com as opções
3. **Resultado NEGATIVO**: tela de resultado com "TESTE NEGATIVO"
4. **Resultado POSITIVO**: tela de resultado com "TESTE POSITIVO" e o nome da deficiência
5. **Filtro aplicado**: página web com o filtro ativo (mostrar a diferença)

**Requisitos das screenshots**:
- Formato: PNG ou JPEG
- Tamanho: 1280×800px **ou** 640×400px
- Cada uma com legenda em português explicando a funcionalidade

> ⚠️ **IMPORTANTE**: As screenshots antigas em `INATIVOS/artifacts/` mostram o wizard PRETO (com pré-teste, TCC etc.). Você PRECISA gerar novas screenshots que reflitam o novo fluxo simplificado.

### Aba "Privacy" (Privacidade)

- Marque **"Não estou enviando dados de usuários"** (a extensão não coleta nenhum dado)
- No campo de justificativa, informe: *A extensão armazena apenas preferências de filtro (tipo, intensidade, shift) localmente no chrome.storage.local. Nenhum dado é enviado para servidores externos.*

### Aba "Permissions" (Permissões)

- **`storage`**: para salvar as preferências de filtro do usuário
- **`http://*/*` e `https://*/*`** (`host_permissions`): necessário para aplicar os filtros SVG em todas as páginas web

Justificativa para `<all_urls>`: *A extensão precisa aplicar filtros de correção cromática em qualquer página web que o usuário visitar, para garantir a acessibilidade contínua durante a navegação.*

---

## 4. Política de Privacidade

Publique o conteúdo abaixo em `https://clovischprogrammer.github.io/Navinclud1.5/privacy`:

---

# Política de Privacidade — NAVINCLUD

**Última atualização:** junho de 2026

## Resumo

O NAVINCLUD respeita sua privacidade. Nenhum dado pessoal é coletado, armazenado em servidores ou compartilhado com terceiros.

## Dados Armazenados

A extensão armazena exclusivamente no dispositivo do usuário (chrome.storage.local):

- **Preferências de filtro** — tipo de filtro, intensidade e ajuste de shift.

Nenhum resultado de teste é armazenado após o fechamento do assistente de teste.

## Dados que NÃO Coletamos

- Dados pessoais identificáveis (nome, email, CPF, endereço)
- Histórico de navegação ou URLs visitadas
- Credenciais (senhas, tokens, cookies)
- Analytics ou rastreadores
- Qualquer tipo de dado biométrico ou de saúde

## Armazenamento

Todos os dados são armazenados exclusivamente no `chrome.storage.local` — área interna do navegador, isolada e não acessível a terceiros. Nenhum dado é transmitido para servidores remotos.

## Compartilhamento com Terceiros

O NAVINCLUD não compartilha nenhum dado com terceiros.

## Direitos do Usuário (LGPD)

Em conformidade com a Lei nº 13.709/2018:

- **Confirmação e acesso**: visualize suas preferências no popup da extensão
- **Correção**: ajuste os filtros manualmente nos controles da extensão
- **Exclusão**: remova a extensão para apagar todos os dados locais

## Segurança

A extensão usa o modelo de segurança do Manifest V3 com menos permissões possíveis. Todo processamento é local no navegador do usuário.

## Contato

**Desenvolvedor:** Clóvis Ch.
**Repositório:** [github.com/ClovisChProgrammer/Navinclud1.5](https://github.com/ClovisChProgrammer/Navinclud1.5)

---

## 5. Submeter para Revisão

1. Após preencher todas as abas, clique em **"Submit for Review"**
2. A Google analisa automaticamente (geralmente leva de **algumas horas a alguns dias**)
3. Acompanhe o status pelo dashboard — se houver rejeição, a Google envia um email com o motivo ("Purple Potassium" etc.)
4. Se rejeitado, corrija o apontado e reenvie (o histórico de aprendizado KAI mostra que isso pode levar rounds)

---

## Checklist Final Pré-Submissão

- [ ] ZIP gerado com apenas os 14 arquivos essenciais + 18 placas
- [ ] Nenhum arquivo .md, .py, .txt, analysis/ ou docs/ dentro do ZIP
- [ ] `manifest.json` com `homepage_url` apontando para `Navinclud1.5`
- [ ] Nenhuma referência a "TCC", "pesquisa", "científico" no código
- [ ] Política de privacidade publicada na URL informada
- [ ] Screenshots refletem o wizard SIMPLIFICADO (sem pré-teste, sem TCC)
- [ ] Permissões justificadas no dashboard
- [ ] Versão bumpada (v1.5)
