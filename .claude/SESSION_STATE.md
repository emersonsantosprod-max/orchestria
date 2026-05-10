Plan: /home/emersonagi/.claude/plans/ler-home-emersonagi-workspace-automacao-jazzy-trinket.md
Active session: Entrega 4a — App lifecycle (path-based registry + dialog nativo)

## Last Completed Step
Entrega 4a (V3+) concluída — lifecycle completo:
- Helpers: `obter_mes_referencia_medicao_lite` (primeira data vence; sem mes_referencia_unico) + `validar_arquivo_referenciado` (fonte canônica de validação de path).
- Desktop: `app/desktop_entry.py` reescrito com pywebview (substitui `webbrowser.open`); JsApi expõe `escolher_arquivo` para JS-bridge.
- API: rotas `POST /api/registry/<tipo>` (JSON path-based) substituem `/api/config/<tipo>` (legacy UploadFile removido). `/api/run/*` lê filepath da medição do registry; relatório continua via multipart.
- UI: default view = `'config'`. SessionBlock + ConfigCard usam dialog nativo + `/api/registry`. Modules extraídos: `modules/{registry,gating,formatters,lifecycle}/`. LogPanel toggle (CSS hide; preserva estado interno; FAB para reabrir).
- Storage: `data/uploads/` descontinuado; `_persistir_*` e `uploads_dir()` removidos.
- CLAUDE.md atualizado: novos INVARIANTS (medição lite no register, registry como SoT de ownership) + CONTRACTS (`/api/registry`, `validar_arquivo_referenciado`).

Test count: 268 passed, 0 failed | npm build: clean (176.61 KB JS) | Lint: 1 erro pré-existente (não introduzido).

⚠️ **Smoke do build empacotado pendente** (PyInstaller + WebView2 requerem ambiente Windows; rodar `pyinstaller AutomacaoMedicao.spec` + abrir o .exe e validar dialog nativo, registro de arquivos, Execute, restart persistence).

## Next Step
Entrega 4b — Férias TAG feature (11 commits): normalizacao canônica + base_tags loader + Update.tag + writer genérico + FeriasContext + UI Base de Tags + gating.
Blocker: none.

## Invariants Exercised This Session
- `mes_referencia_unico` continua estrito no pipeline (defesa-em-profundidade): ✓
- `registro_arquivos` guarda caminho original; SQLite é materialização lookup: ✓
- `validar_arquivo_referenciado` é fonte canônica (register + Execute): ✓
- App.jsx coordena estado/views (modules extraídos para `modules/`): ✓
- Backend é fonte de verdade; UI bloqueio é UX: ✓
- LogPanel preserva estado interno via CSS hide (sem unmount): ✓

## Files Modified (Entrega 4a)
Backend:
- app/infrastructure/paths.py (validar_arquivo_referenciado; drop uploads_dir)
- app/infrastructure/data/bootstrap.py (obter_mes_referencia_medicao_lite; drop _persistir_*)
- app/api/routes/registry.py (NEW — path-based)
- app/api/routes/atestado.py, ferias.py, treinamentos.py, distribuicao.py (lê medicao do registry)
- app/api/routes/config.py (REMOVED — legacy UploadFile)
- app/api/main.py (drop config router)
- app/desktop_entry.py (pywebview + JsApi)
- pyproject.toml (+pywebview==5.4)
- AutomacaoMedicao.spec (+webview hidden imports)
- CLAUDE.md (INVARIANTS + CONTRACTS)

Frontend:
- app/ui/web/src/App.jsx (default view=config; LogPanel toggle; modules imports; API.run só relatorio)
- app/ui/web/src/modules/registry/index.js (NEW)
- app/ui/web/src/modules/gating/index.js (NEW — getRunBlockReason canônico)
- app/ui/web/src/modules/formatters/index.js (NEW — re-export)
- app/ui/web/src/modules/lifecycle/reducer.js (NEW — reducer + initialState + LOGS_TOGGLE)
- app/ui/web/src/components/SessionBlock.jsx (dialog nativo + /api/registry)
- app/ui/web/src/components/ConfigCard.jsx (dialog nativo + /api/registry)
- app/ui/web/src/components/ConfigView.jsx (drop fileRefs prop)
- app/ui/web/src/components/LogPanel.jsx (collapsed prop)
- app/ui/web/src/components/ModuleRow.jsx (drop medicao do payload)

Tests:
- tests/test_validar_arquivo_referenciado.py (NEW — 5 cases)
- tests/test_obter_mes_referencia_lite.py (NEW — 2 cases)
- tests/test_desktop_entry_pywebview.py (NEW — 5 cases)
- tests/api/test_routes_registry.py (NEW — 7 cases)
- tests/api/test_routes_run.py (migrado para registry-based)
- tests/api/test_routes_config*.py (REMOVED — legacy)
- tests/conftest.py (drop uploads_dir patch)

## TODO
- [x] Entrega 1 (V3) — backend: paths, validação, domínio
- [x] Entrega 2 (V3) — testes: isolamento explícito
- [x] Entrega 3 (V3) — UI: navegação, rename, gating, modularização
- [x] Entrega 4a (V3+) — lifecycle: path-based registry + dialog nativo + LogPanel toggle
- [ ] Entrega 4b — Férias TAG feature (normalizacao + base_tags + Update.tag + FeriasContext)
- [ ] Entrega 5 — Cleanup documental (futura)