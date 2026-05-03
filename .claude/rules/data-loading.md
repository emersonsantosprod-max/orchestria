---
paths:
  - "app/loaders.py"
  - "app/core.py"
  - "app/excel.py"
  - "app/db.py"
  - "app/paths.py"
  - "app/infrastructure/loaders.py"
  - "app/infrastructure/excel.py"
  - "app/infrastructure/db.py"
  - "app/infrastructure/paths.py"
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
- mapear_colunas: colunas opcionais ausentes vão para `_ausentes` (tupla);
  pipeline transforma faltantes-críticos em inconsistência quando
  validar_distribuicao=True — não silenciar.
- indexar_e_ler_dados: registrar `obs_divergentes` / `desc_divergentes` quando
  múltiplas linhas (matricula, data) divergem; aplicar_updates emite
  inconsistência apenas para tipo='treinamento' (semântica append). Férias e
  atestado sobrescrevem por contrato — não emitir divergência.
