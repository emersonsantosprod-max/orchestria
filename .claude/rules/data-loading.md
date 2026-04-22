---
paths:
  - "app/loaders.py"
  - "app/core.py"
  - "app/excel.py"
  - "app/db.py"
  - "app/paths.py"
---

## Data Loading Rules

- Load workbooks with openpyxl.load_workbook(read_only=True, data_only=True).
- indexar_e_ler_dados(): single-pass iter_rows(values_only=True) — no random access.
- base_treinamentos.xlsx: col 0 = name UPPER, col 1 = type — no dynamic mapping,
  no fallback.
- Multi-day load: replicate fully per day — do not split load across days.
- Observation: apply core.deduplicar_observacao before concatenating — never
  concatenate directly.
- Inconsistency report: export all records, no truncation.
