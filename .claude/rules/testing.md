---
paths:
  - "tests/**/*.py"
---

## Testing Rules

- Use fakes (Protocol implementations) for ports — never real SQLite files in domain tests.
- SQLite infra tests use `:memory:` — never a file on disk.
- `tests/test_layer_boundaries.py` is the architecture enforcement — do not break it.
- Error message format `"<tipo> [<md>] esperado=<f.4> realizado=<f.4> diff=<f.4>"` is a frozen contract
  covered by regex in `tests/test_distribuicao_contract_guard.py` — do not alter.
- For fixtures, parametrize, and mocking patterns: see `.claude/skills/python-testing/SKILL.md`.
