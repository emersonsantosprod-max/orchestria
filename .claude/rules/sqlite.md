---
paths:
  - "app/**/*.py"
  - "ui/**/*.py"
---

## SQLite Rules

- Connection per request — never reuse the composition root's connection in a worker thread.
- Schema bootstrap (`db.popular_bd_se_vazio`) runs once in the composition root, before worker threads start. Worker threads never call `popular_*`.
- Worker threads open and close their own connection within the task scope (`check_same_thread` violation if reused).
- Writes (`registrar_bd`, `registrar_medicao`) are serialized via `threading.Lock` in the GUI singleton.
- `app.paths.db_path()` is the single source for the DB path — never hardcode `Path('data/automacao.db')`.
- Distribuição contratual loads once from xlsx into SQLite at bootstrap; all other inputs are ephemeral via `loaders.py`.
