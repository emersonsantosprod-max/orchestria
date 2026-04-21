# CLAUDE.md

## PROJECT
Python automation for workforce measurement (medição) in petrochemical
maintenance. Reads Excel inputs, processes férias/treinamentos/atestados,
applies updates, exports results and inconsistency reports.
Stack: Python, openpyxl, SQLite, PyInstaller. Entry points: `python -m app.main` (CLI), `ui/gui.py` (GUI).

## INVARIANTS

- Inconsistência: registro válido extraído que não pôde ser aplicado na planilha.
- Não são inconsistências: férias sem aprovação; dados fora do critério de aplicação.
- PyInstaller spec: `AutomacaoMedicao.spec` (GUI).
- SSOT estrutural: `PROJECT_STRUCTURE.md` (não manter docs paralelas).

## CONTRACTS

- `Update.desconto_min`: domínio entrega em minutos; writer converte para HH:MM — não pré-converter no domínio.
- `Inconsistencia`: construir exclusivamente via `core.inconsistencia(origem, ...)`.
- `Update` e `Inconsistencia` são dataclasses puras — acesso por atributo; não `.get()` / `[key]` / `in`.
- `gerar_updates_treinamento(dados, tabela, obs_existentes)` → `(list[Update], list[Inconsistencia])` — não alterar assinatura.
- `gerar_updates_ferias(dados, base_cobranca, medicao_por_matricula, md_cobranca_por_chave, sg_funcao_por_chave, mes_ref, col_map)` → `(list[Update], list[Inconsistencia])` — não alterar assinatura.
- `pipeline.executar_pipeline(..., conn=None, validar_distribuicao=False)`: DI explícita. `validar_distribuicao=True` exige `conn`; caso contrário levanta `ValueError`.
- Caminho do SQLite é resolvido via `app.paths.db_path()` — não referenciar `Path('data/automacao.db')` diretamente.

## RULES

- Carregar workbooks com `openpyxl.load_workbook(read_only=True, data_only=True)`.
- `indexar_e_ler_dados()`: passada única `iter_rows(values_only=True)` — não usar acesso aleatório.
- `base_treinamentos.xlsx`: col 0 = nome UPPER, col 1 = tipo — sem mapeamento dinâmico; sem fallback.
- Carga multi-dia: replicar integralmente por dia — não dividir carga entre os dias.
- Observação: aplicar `core.deduplicar_observacao` antes de concatenar — não concatenar diretamente.
- Relatório de inconsistências: exportar todas, sem truncamento.

## CRITICAL

- Não substituir `salvar_via_zip` por openpyxl write mode — ~4s → ~42s.
- Não reordenar `updates_treinamento + updates_ferias` em `pipeline.executar_pipeline` — quebra `test_ferias_sobrescreve_observacao_de_treinamento_na_mesma_celula`.
- Não alterar formato de desconto de `HH:MM` — testes fixos nesse formato.
- Não alterar passada única em `indexar_e_ler_dados()` — `read_only` não permite acesso aleatório (crash em runtime).
- Não alterar formato de observação de férias sem atualizar `test_ferias_*`.
- Não alterar chave de índice `(matricula, data)` — usada em indexação (`indexar_e_ler_dados`) e aplicação (`aplicar_updates`); mudança quebra ambos.

## CODING_STANDARDS

Applies to all code under `app/`, `ui/`, and `tests/`. Enforced via `make lint` (ruff) and code review.

### Naming
- Pattern: `verb + object + context` — `validar_intervalo_datas_medicao()`, not `validar()`.
- Every name must resolve in a single grep: `rg nome_do_simbolo` returns only the target.
- Banned generic tokens in symbol names: `process`, `handle`, `run`, `utils`, `helpers`, `common` (and their Portuguese equivalent `processar` when used as a standalone verb without a specific object+context).

### Files and Structure
- One domain per file; keep files under 300–500 lines.
- Organize by business domain, not technical layer (`/ferias`, `/validacao`, `/distribuicao` — yes; `/utils`, `/helpers`, `/services` — no).
- Flat hierarchy; avoid abstraction layers that require multiple files to understand one flow.
- Domain-justified exceptions (do NOT rename): `app/core.py` (shared types + factories), `app/pipeline.py` (orchestration), `app/cli/` (subcommand scripts — layout mandated by ARCHITECTURE).

### Functions
- One responsibility per function; the name must equal the full intent — if it is hard to name precisely, split it.
- Prefer direct calls over factories, dynamic dispatch, or runtime injection.
- Prefer specific + light duplication over an abstraction with no domain name.

### Tests
- Headless, single-command, machine-parseable output.
- Declared run commands (see `Makefile` at repo root):
  - `make install` — install dev dependencies (`pip install -e .[dev]`).
  - `make test` — run the full pytest suite.
  - `make lint` — run `ruff check app/ tests/ ui/`.
  - `make dev` — start CLI (`python -m app.main`).

### Style
- Consistent formatting enforced by `ruff` (configured in `pyproject.toml`).
- No comments that explain WHAT the code does — names carry that responsibility.
- Comments only for non-obvious external references (regulation number, issue link, workaround for a specific bug).

## ARCHITECTURE
Flow: entrada/ → loaders.py → pipeline.py → [ferias|treinamento|atestado|distribuicao] → aplicar_updates → saida/
Layers: loaders (I/O only) → domain modules (logic only) → pipeline (orchestration only) → excel.py (write only)
Rules:
- Domain modules do not import from each other
- loaders.py does not contain business logic
- pipeline.py does not contain business logic; não abre conexões de DB nem executa bootstrap
- excel.py does not import domain modules
- Bootstrap de SQLite (`db.popular_bd_se_vazio`) é responsabilidade da application boundary (`app/main.py`, `ui/gui.py`), executado ANTES de chamar `pipeline.executar_pipeline()`
- Scripts CLI vivem em `app/cli/` (normalizar, validar_dist, validar_consist); `app/main.py` é o único entry-point, com subcomandos argparse. Não criar `.py` soltos na raiz.
- Distribuição contratual é persistida em SQLite (carga única a partir do xlsx empacotado via PyInstaller `datas=`); demais entradas permanecem efêmeras via `loaders.py`.

## Git — Commit & Push Rules

### When to commit
Commit after each of these:
- Feature or sub-feature completed
- Bug fixed
- Code refactored
- Config or dependency changed
- Before starting any experimental/risky change

### Commit message format
Use Conventional Commits in English:
- `feat: add login screen`
- `fix: correct email validation`
- `refactor: simplify cart logic`
- `chore: update dependencies`
- `docs: update README`

### When to push
Push automatically after every commit (or after 2–3 related commits).
Always push at the end of a work session.

### Standard flow
Run this after completing any task:
```bash
git add .
git commit -m "type: clear description of what changed"
git push origin main
```

> Do not wait for user instruction. Commit and push as a natural part of completing work.