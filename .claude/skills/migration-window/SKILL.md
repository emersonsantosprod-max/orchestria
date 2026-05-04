---
name: migration-window
description: Migration window state — which legacy paths remain, what has moved, and import conventions during the transition.
---

# Migration Window

Active during the refactor from flat `app/` to layered `app/domain/` + `app/application/` + `app/infrastructure/`.

## Migrated (use target paths for new imports)

| Domain | Target | Legacy (removed) |
|--------|--------|-----------------|
| Core types | `app/domain/core.py` | `app/core.py` (legacy, still coexists) |
| Errors | `app/domain/errors.py` | `app/errors.py` (legacy, still coexists) |
| Treinamento | `app/domain/treinamento.py` | `app/treinamento.py` (legacy, still coexists) |
| Férias | `app/domain/ferias.py` | `app/ferias.py` (removed) |
| Atestado | `app/domain/atestado.py` | `app/atestado.py` (removed) |
| Distribuição | `app/domain/distribuicao.py` | `app/validar_distribuicao.py` (removed) |
| Distribuição contratual (domain) | `app/domain/distribuicao_contratual.py` | `app/distribuicao_contratual.py` (removed) |
| Distribuição contratual (infra) | `app/infrastructure/adapters/excel_distribuicao_contratual.py` | — |
| Relatório distribuição | `app/infrastructure/adapters/relatorio_distribuicao.py` | — |
| Validação distribuição (service) | `app/application/services/validacao_distribuicao.py` | — |
| Pipeline | `app/application/pipeline.py` | `app/pipeline.py` (legacy, still coexists) |
| Loaders | `app/infrastructure/loaders.py` | `app/loaders.py` (legacy, still coexists) |
| Excel | `app/infrastructure/excel.py` | `app/excel.py` (legacy, still coexists) |
| DB | `app/infrastructure/db.py` | `app/db.py` (legacy, still coexists) |
| Paths | `app/infrastructure/paths.py` | `app/paths.py` (legacy, still coexists) |

## Not yet migrated

- `app/validar_horas.py` — still flat; no target path yet.
- Legacy coexisting files above — migration pending.

## Import convention during the window

- If the file has been moved to target: use target path.
- If still in legacy location: use legacy path. No re-export shims.
- Do not import from both paths in the same module.

## Adapters deleted (need adaptation)

The following adapters were deleted intentionally — code that imported them must migrate to the new layer structure:
- `app/infrastructure/adapters/__init__.py`
- `app/infrastructure/adapters/excel_distribuicao_contratual.py` (check if reimplemented)
- `app/infrastructure/adapters/relatorio_distribuicao.py` (check if reimplemented)
- `app/infrastructure/adapters/sqlite_tabela_classificacao.py`

Affected files: `app/application/pipeline.py`, `app/cli/`, and their tests.
