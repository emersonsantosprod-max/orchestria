---
paths:
  - "app/**/*.py"
  - "tests/**/*.py"
---

## Layer Boundaries

### app/domain/
Allowed imports: stdlib, `app.domain.*`
Forbidden: `sqlite3`, `openpyxl`, `from app.application`, `from app.infrastructure`
Files named by business domain (treinamento, ferias, atestado, core, errors) — never by layer.

### app/application/services/
Allowed imports: stdlib, `app.domain.*`, `typing.Protocol`
Forbidden: `app.infrastructure.*`, `sqlite3`, `openpyxl`
Exception: `pipeline.py` is the multi-domain composition point — may import `app.infrastructure.*`.

### app/infrastructure/
Sole layer that touches `sqlite3`, `openpyxl`, and filesystem.
Subpaths: `loaders.py`, `excel.py`, `db.py`, `paths.py`, `logging_config.py`, `adapters/*.py`

### app/main.py, app/cli/, ui/
Composition root. Only place where adapters are instantiated and injected into services.

### Enforcement
`tests/test_layer_boundaries.py` is the automated check — run before merging any change to
`app/domain/` or `app/application/services/`.
