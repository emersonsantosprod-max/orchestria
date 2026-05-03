---
paths:
  - "app/**"
  - "ui/**"
  - "tests/**"
---

## Coding Standards

### Naming
- Pattern: verb + object + context — `validar_intervalo_datas_medicao()`, not `validar()`.
- Example contrast: `gerar_updates_treinamento` (verb + object + context),
  not `processar_treinamento` or `run_treinamento`.
- Every name must resolve in a single grep.
- Banned generic tokens: `process`, `handle`, `run`, `utils`, `helpers`, `common`,
  and `processar` when used without specific object+context.

### Files
- One domain per file; keep files under 300–500 lines.
- Layer split, layer rules, and forbidden-imports are defined in `.claude/rules/boundary.md`.
- Domain-justified exceptions (do NOT rename, even after migration):
  `app/domain/core.py`, `app/application/pipeline.py`, `app/cli/`.

### Functions
- One responsibility per function; name must equal full intent — split when
  hard to name precisely.
- Prefer direct calls. Forbidden: factories-by-string, dynamic dispatch
  (`getattr(module, name)()`), service locators, runtime DI containers,
  adapter registries resolved by name.
- Permitted indirection: a `typing.Protocol` port consumed by a service,
  with the adapter constructed in the composition root and passed by
  argument. One port per refactor. Each port carries a business name
  (`TabelaClassificacao`, not `Repository`).
- Prefer specific + light duplication over an abstraction with no domain name.

### Tests
- Headless, single-command, machine-parseable output.
- Run commands: `make install` | `make test` | `make lint` | `make dev`

### Style
- Consistent formatting enforced by ruff (configured in `pyproject.toml`).
- No comments explaining WHAT the code does.
- Comments only for non-obvious external references (regulation number,
  issue link, workaround for a specific bug).
