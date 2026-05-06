Plan: /home/emersonagi/.claude/plans/fetch-this-design-file-velvety-swing.md

## Last Completed Step
Bootstrap loading UI + DB probe — app/api/routes/initial_data.py, app/api/schemas/initial_data.py, tests/api/test_routes_config.py, ui/web/src/App.jsx, ui/web/src/styles/colors_and_type.css
Test count: 224 passed, 0 failed | Lint: 2 pre-existing errors (registry.py, loaders.py) — não tocados por esta sessão

## Next Step
Verificação manual no `make dev` + `make build-win` (Windows) para validar SPA empacotada no .exe
Blocker (if any): none

## Invariants Exercised This Session
- /api/initial-data response shape: ✓ (new modules/config/tables fields acrescentados sem quebrar campos legados)
- Repository pattern (conn injetada, sem commit interno): ✓ — reuso de TreinamentosRepository, MedicaoRepository, RegistryRepository, DistribuicaoRepository

## Files Modified
- app/api/schemas/initial_data.py (ModuleStatus + ConfigStatus added)
- app/api/routes/initial_data.py (modules/config/tables derivation)
- tests/api/test_routes_config.py (test for new shape)
- ui/web/src/App.jsx (bootstrap state + phased reveal + skeletons)
- ui/web/src/styles/colors_and_type.css (msvshimmer keyframe)

## TODO
- [x] Backend: estender /api/initial-data
- [x] Frontend: bootstrap UX (skeletons, faseado, blocked-while-bootstrapping)
- [x] CSS: msvshimmer keyframe
- [x] Build ui/web/dist via Vite
- [ ] make build-win (Windows) — gerar AutomacaoMedicao.exe com a SPA atualizada