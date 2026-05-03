---
name: repository-pattern
description: Repository pattern for app/infrastructure/data/ — conn injected, no internal commit, fake for tests.
paths:
  - "app/infrastructure/data/**"
  - "tests/test_*repository*.py"
  - "tests/infrastructure/**"
---

# Repository Pattern

Used in `app/infrastructure/data/repositories/`.

## Rules

- **Connection injection:** every repository method receives `conn: sqlite3.Connection` as its first argument — never opens a connection itself.
- **No commit inside:** repositories never call `conn.commit()` — the caller (composition root or service) owns the transaction boundary.
- **No schema inside:** schema bootstrap is `db.popular_bd_se_vazio()` in the composition root, not in the repository.
- **Structural typing:** repositories implement ports via Protocol (structural subtyping) — no inheritance.
- **Test fake:** tests use `sqlite3.connect(":memory:")` + schema setup inline — no fixture files on disk.

## Template

```python
# app/infrastructure/data/repositories/meu_dominio.py
import sqlite3
from app.application.ports import MeuPort  # Protocol


class MeuRepositorio:
    def listar(self, conn: sqlite3.Connection) -> list[...]:
        cur = conn.execute("SELECT ... FROM ...")
        return [... for row in cur.fetchall()]
```

```python
# tests/infrastructure/test_meu_repository.py
import sqlite3

def test_listar():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE ...")
    conn.execute("INSERT INTO ... VALUES (...)")
    repo = MeuRepositorio()
    result = repo.listar(conn)
    assert result == [...]
```

## Port naming

Business name, not technical: `TabelaClassificacao`, not `TabelaClassificacaoRepository`.
