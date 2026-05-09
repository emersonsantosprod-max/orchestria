Plan: /home/emersonagi/.claude/plans/problemas-indentificados-mudan-as-feitas-zesty-parnas.md
Active session: .claude/sessions/2026-05-09-entrega-2-testes-isolamento.tmp (closed)

## Last Completed Step
Entrega 2 (V3) concluída — testes: fixture única opt-in `isolated_paths` em `tests/conftest.py` (sem autouse, sem sentinelas); migração de `tests/api/test_routes_{config,config_validacao,run}.py`; `processed_output_path` assume mkdir; `app/cli/normalizar.py` defere resolução de `exports_dir()` para `main()` (antes criava `data/exports` no import). `data/` removida fisicamente; suíte confirmada não-recriadora.
Test count: 265 passed, 0 failed | Lint: 2 erros pré-existentes (não introduzidos) | Quality gate: clean (violations 0 delta, duplication −214, demais métricas <+10%).

## Next Step
Entrega 3 — UI: navegação, rename, gating, modularização.
Blocker: none.

Pendência menor: `.vscode/settings.json` permanece no repo desde commit `d1d386f` (config local benigna).

## Invariants Exercised This Session
- Isolamento de filesystem por opt-in explícito (parallel-safe, xdist-compatible): ✓
- Patches em consumer-modules permanecem onde local binding existe (`app.api.routes.config.uploads_dir`, `app.infrastructure.data.bootstrap.uploads_dir`): ✓
- `processed_output_path` resolve sob `isolated_paths / exports`: ✓ (test_isolamento_paths)
- Sem autouse, sem `request.fixturenames` sentinel, sem assert contra estado global: ✓
- Suíte não recria `data/` após `rm -rf data/`: ✓

## Files Modified
- tests/conftest.py (NEW: isolated_paths fixture, opt-in)
- app/infrastructure/paths.py (mkdir explícito em processed_output_path)
- tests/api/test_routes_config.py (isolated_paths)
- tests/api/test_routes_config_validacao.py (isolated_paths)
- tests/api/test_routes_run.py (isolated_paths)
- tests/api/test_isolamento_paths.py (NEW: 1 case)
- app/cli/normalizar.py (lazy exports_dir resolution)

Cleanup: `data/` removida fisicamente (gitignored, sem commit).

## TODO
- [x] Entrega 1 (V3) — backend: paths, validação, domínio
- [x] Entrega 2 (V3) — testes: isolamento explícito
- [ ] Entrega 3 — UI: navegação, rename, gating, modularização
- [ ] Entrega 4 — Cleanup documental