# Learnings

Corrections, insights, and knowledge gaps captured during development.

---

### `LRN-20260623-001` — Reorganização de repositório com `git mv` + path fix

**Contexto:** Reorganizar 44 arquivos em 12 subdiretórios sem quebrar scripts.

**Metodologia comprovada:**
1. Mapear TODOS os hardcoded paths (`os.path.dirname(__file__)`, defaults, docstrings) antes de mover
2. Calcular `_PROJECT_ROOT` com `os.path.join(os.path.dirname(__file__), ".." [x N])` e usar como BASE
3. Commitar em duas etapas:
   - `git mv` primeiro (só renames, sem modificações)
   - Depois aplicar as edições de path e commitar separadamente
4. Verificar com `py_compile` + execução real

**Por que funciona:** `git mv` preserva o histórico mas não modifica conteúdo. Separar renames de edits evita conflitos.

---

### `LRN-20260623-002` — Extensão Chrome deve ficar na raiz

**Contexto:** O manifesto MV3 exige que `manifest.json`, páginas HTML e scripts de conteúdo estejam acessíveis por caminhos relativos. Mover para subpasta quebraria todas as referências internas.

**Regra:** A raiz do repositório = raiz da extensão. Subdiretórios são para código de suporte (análise, simulação, docs, branding).

