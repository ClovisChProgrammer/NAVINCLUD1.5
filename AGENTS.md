## Goal
- Criar simulador automatizado (`simulate_5salas_testes.py`) que gera 100 testes reais com timings realistas, usando Selenium + Chrome for Testing + extensão NAVINCLUD, e pausa a cada sala para export manual.

## Constraints & Preferences
- Responder sempre em pt-BR
- Usar metodologia 3x3RA+ antes de decisões
- Preservar snapshots (5 níveis) antes de modificações
- Não modificar filtros, sliders, toggle ou placas Ishihara
- Usuário é profissional multidisciplinar — sem disclaimers
- Total: 100 alunos (19+17+22+24+18) distribuídos em 5 salas com sexo, idade e defeitos específicos
- Tempo de reação: normais 2-11s (60% rápido, 40% lento), deficientes 6-11s (100% lento)
- Percepção: 1-3 opções, sem "Fácil"+"Difícil" juntos
- alreadyTaken: 8% "Sim"
- Pós-experiência (7 deficientes): todos respondem que extensão ajudou
- Export manual após cada sala completa

## Decisions
- **`--load-extension` bloqueado no Chrome estável desde ~129** — usar Chrome for Testing (CfT) é a solução oficial
- CfT baixado automaticamente (150MB, 1 vez) via `requests` + `zipfile`
- Shadow DOM do `chrome://extensions/` usa Lit templates: `extensions-manager > #itemsList (shadowRoot) > extensions-item#ID`
- Extension ID detectado com polling (até 10s) para aguardar renderização
- Perfil temporário `perfil_temporario/` (startup rápido)
- Cache de Extension ID em `extension_id.txt`
- **Wizard aberto em janela separada** (não aba) para que `chrome.windows.remove()` do wizard.js não mate a sessão Selenium
- Aluno deficiente: após wizard fechar, navega uma janela sobrevivente para `experience.html`, responde questionário pós-experiência
- `--fast`: reações de 0.5-2s para testar fluxo (padrão: 2-11s realistas)

## Architecture
```
simulate_5salas_testes.py  ← script principal
├── weighted_age()         ← idade ponderada por moda
├── generate_students()    ← gera 100 alunos com sexo/idade/defeitos
├── pick_perception()      ← 1-3 opções sem Facil+Dificil
├── ensure_chrome_for_testing() ← baixa CfT se necessário
├── kill_chrome_processes()
├── setup_driver(cft_exe)  ← inicia CfT + extensão
├── get_extension_id()     ← detecta ID via shadow DOM (polling)
├── run_single_test()      ← fluxo completo de 1 aluno
│   ├── Abre wizard em nova JANELA
│   ├── Preenche pre-teste
│   ├── 18 placas Ishihara (clique com delay)
│   ├── Percepção (checkboxes)
│   ├── [se normal] Post-test → Parabéns → NOVO TESTE
│   ├── [se deficiente] Convite → experience.html
│   │   ├── Fecha wizard, navega p/ experience.html
│   │   ├── Exit experience → questionário → save
│   │   └── about:blank (evita thankyou fechar janela)
│   └── Retorna True/False
├── save/load_progress()
└── main()
```

## Defeitos por Sala
| Sala | Total | M/F | Deficientes |
|------|-------|-----|-------------|
| 3A   | 19    | 16M/3F | 2 deuteran (M) |
| 3B   | 17    | 13M/4F | 1 deuteran (M), 1 tritan (M) |
| 2A   | 22    | 16M/6F | nenhum |
| 2B   | 24    | 16M/8F | 1 deuteran (M), 1 protan (M) |
| 1A   | 18    | 11M/7F | 1 protan (F) |
| **Total** | **100** | **72M/28F** | **7 deficientes** |

## Key Files
- `simulate_5salas_testes.py` — simulador principal (~630 linhas)
- `chromedriver-win64/chromedriver.exe` — ChromeDriver 148.0.7778.178
- `chrome_for_testing/chrome-win64/chrome.exe` — CfT (baixado automaticamente)
- `extension_id.txt` — cache do ID da extensão
- `perfil_temporario/` — perfil Chrome limpo para CfT (gitignorado)
- `.gitignore` — ignora `simulacao_progresso.json`, `extension_id.txt`, `chromedriver_ext*.log`

## Running
```powershell
# Teste rapido (reacoes 0.5-2s):
python simulate_5salas_testes.py --fast

# Simulacao completa (reacoes realistas 2-11s, ~3h):
python simulate_5salas_testes.py

# RETOMAR de onde parou (preserva perfil + progresso):
python simulate_5salas_testes.py --resume

# Retomar pulando X alunos (ex: pulando 73 primeiros):
python simulate_5salas_testes.py --resume --skip 73

# Usar seed diferente para reprodutibilidade:
python simulate_5salas_testes.py --seed 12345
```

## Novas Funcionalidades (Retomo)
- **`--resume`**: NÃO deleta o perfil `perfil_temporario/` existente. Preserva os dados já salvos no `chrome.storage.local`.
- **`--skip N`**: Pula os primeiros N alunos. Útil quando a simulação parou no meio de uma sala.
- **`--seed N`**: Seed fixa para reprodutibilidade (padrão: 42). Garante que os mesmos alunos serão gerados na mesma ordem.
- **Progresso automático**: O arquivo `simulacao_progresso.json` é salvo após CADA aluno, não só após cada sala. Se a simulação for interrompida, basta rodar com `--resume` que ela continua automaticamente.

## Cenário de Falha Recuperado
Se o HD for desconectado ou o computador desligar no meio da simulação:
1. Os dados dos alunos já testados permanecem no `perfil_temporario/`
2. O arquivo `simulacao_progresso.json` tem o número exato de alunos completados
3. Execute: `python simulate_5salas_testes.py --resume`
4. O simulador automaticamente pula os alunos já feitos e continua do ponto certo

## CWS Submission Checklist (promovido de .learnings/LRN-20260602-002)
Antes de cada submissão ao Chrome Web Store:
1. Auditar `permissions[]` — remover qualquer permissão não utilizada (especialmente `activeTab`, `tabs`, `scripting`)
2. Verificar `privacy_policy` — **não** é chave válida do manifest MV3; configurar no CWS Developer Dashboard
3. Garantir **zero scripts remotos** — todo código deve estar bundled na extensão (sem CDN, sem scripts externos)
4. Rodar `build-cws-zip.ps1` para gerar ZIP limpo
5. Verificar `host_permissions` — usar escopo mínimo necessário (<all_urls> é aceito, mas justificar)
6. Confirmar versão bump correta no manifest.json

## Session Log Discipline (promovido de .learnings/ERR-20260602-001)
Atualizar `Andamentos KAI.md` ao final de **cada sessão**, mesmo que breve. Mínimo: data, resumo dos commits/tarefas, estado atual.

## Known Issues
- `python simulate_5salas_testes.py` (modo realista) leva ~3h para 100 alunos
- ChromeDriver 148.0.7778.178 travou com versão CfT diferente — manter sincronizado
- Experience popup do wizard.js fecha com `chrome.windows.remove()` — janela separada do Selenium sobrevive
