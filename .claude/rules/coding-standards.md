---
paths:
  - "app/**"
  - "ui/**"
  - "tests/**"
---

## Coding Standards

### Naming
- Pattern: verb + object + context — validar_intervalo_datas_medicao(), not validar().
- Every name must resolve in a single grep.
- Banned generic tokens: process, handle, run, utils, helpers, common,
  and processar when used without specific object+context.

### Files and Structure
- One domain per file; keep files under 300–500 lines.
- Organize by business domain, not technical layer.
- Flat hierarchy; avoid abstraction layers that require multiple files to
  understand one flow.
- Domain-justified exceptions (do NOT rename):
    app/core.py — shared types and factories
    app/pipeline.py — orchestration
    app/cli/ — subcommand scripts, layout mandated by ARCHITECTURE

### Functions
- One responsibility per function; name must equal full intent — split when
  hard to name precisely.
- Prefer direct calls over factories, dynamic dispatch, or runtime injection.
- Prefer specific + light duplication over an abstraction with no domain name.

### Tests
- Headless, single-command, machine-parseable output.
- Run commands: make install | make test | make lint | make dev

### Style
- Consistent formatting enforced by ruff (configured in pyproject.toml).
- No comments explaining WHAT the code does.
- Comments only for non-obvious external references (regulation number,
  issue link, workaround for a specific bug).
