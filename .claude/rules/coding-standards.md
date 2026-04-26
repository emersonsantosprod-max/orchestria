---
paths:
  - "app/**"
  - "ui/**"
  - "tests/**"
---

## Coding Standards

### Naming
- Pattern: verb + object + context — validar_intervalo_datas_medicao(), not validar().
- Example contrast: gerar_updates_treinamento (verb + object + context),
  not processar_treinamento or run_treinamento.
- Every name must resolve in a single grep.
- Banned generic tokens: process, handle, run, utils, helpers, common,
  and processar when used without specific object+context.

### Files and Structure
- One domain per file; keep files under 300–500 lines.
- **Top-level layer split inside `app/`** is the architectural axis:
  `app/domain/`, `app/application/`, `app/infrastructure/`, `app/cli/`.
  Layer responsibilities are defined in CLAUDE.md ARCHITECTURE; this is the
  only place where "by layer" organization is allowed.
- **Inside each layer**, files are named by business domain — never by
  sub-layer.
  Allowed: `treinamento.py`, `ferias.py`, `atestado.py`, `core.py`,
  `errors.py`, `loaders.py`, `excel.py`, `db.py`, `paths.py`,
  `logging_config.py`, `pipeline.py`.
  Forbidden: `services.py`, `entities.py`, `models.py`, `helpers.py`,
  `utils.py`, `common.py`.
- Avoid abstraction layers that require multiple files to understand one flow.
  Exception: a use-case service + port + adapter triple is permitted when
  ALL of the following hold:
  (a) the dependency is hard to test (live SQLite connection, Excel I/O,
      filesystem, network);
  (b) a fake of the port exists in tests and exercises real behavior
      without that I/O;
  (c) every name in the chain is greppable and resolves to exactly one file.
  Justify the triple in CLAUDE.md ARCHITECTURE; absent justification, prefer
  a direct call.
- Domain-justified exceptions (do NOT rename, even after migration):
    app/domain/core.py — shared types and factories
    app/application/pipeline.py — orchestration
    app/cli/ — subcommand scripts, layout mandated by ARCHITECTURE
- During the migration window, legacy paths (`app/treinamento.py`,
  `app/core.py`, `app/loaders.py`, `app/excel.py`, `app/db.py`, `app/paths.py`,
  `app/errors.py`, `app/logging_config.py`, `app/pipeline.py`) coexist with
  the target paths. New imports use the target path when the file has
  already moved; otherwise the current path. No re-export shims.

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
- Run commands: make install | make test | make lint | make dev

### Style
- Consistent formatting enforced by ruff (configured in pyproject.toml).
- No comments explaining WHAT the code does.
- Comments only for non-obvious external references (regulation number,
  issue link, workaround for a specific bug).
