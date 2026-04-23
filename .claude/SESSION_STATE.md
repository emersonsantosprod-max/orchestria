## Last Completed Step
Strip WHAT-comments across app/ — validar_distribuicao.py (Step 1/2/3/4 + Relatório banner), excel.py (ZIP-patch banner condensed to single WHY line), ui/gui.py (7 section banners removed; ruff --fix consolidated imports). Audited atestado.py, loaders.py, db.py, paths.py, errors.py, app/cli/* — only docstrings remain (acceptable per CODING_STANDARDS).
Test count: 105 passed, 0 failed | Lint: clean

## Next Step
Optional: strip section banners from tests/ (test_ferias_*, test_validar_*, test_distribuicao_contratual.py — ~30 banner pairs). Then Pass B: review parameter names against verb+object+context naming.
Blocker: none

## Invariants Exercised This Session
- CODING_STANDARDS style: ✓ no banner/WHAT comments in app/ or ui/; WHY comments preserved (excel.py ZIP-patch CLAUDE.md CRITICAL note; validar_distribuicao.py "universo temporal" invariant)
- Tests: ✓ 105/105 passed throughout

## Files Modified
- app/validar_distribuicao.py (removed Step 1-4 banners + Relatório banner; condensed WHY note)
- app/excel.py (collapsed ZIP-patch dashed banner to single WHY line referencing CLAUDE.md CRITICAL)
- ui/gui.py (removed 7 section banners; ruff auto-consolidated imports)

## Baseline
Commit: 629e8fa refactor: split oversized files into domain-named modules
Tests: 105 passed — must remain 105 throughout

## Plan
File Path: "\\wsl.localhost\Ubuntu\home\emersonagi\.claude\plans\brainstorming-rules-modular-avalanche.md"

## TODO
- [x] Split app/cli/validar_consist.py (615 lines)
- [x] Split ui/gui.py (591 lines)
- [x] Fix lint error in ui/gui_handlers.py (ruff --fix, then make lint clean)
- [x] Strip WHAT-comments across app/ (complete: ferias, treinamento, main, pipeline, core, validar_horas, excel, distribuicao_contratual, validar_distribuicao)
- [x] Strip section banners in ui/gui.py
- [ ] Optional: strip section banners in tests/ (~30 banner pairs)
- [ ] Pass B: clean parameter names if still violating (make test green)
- [ ] Final verification: make test + make lint + rg banned-token sweep + git diff --stat
- [ ] Commits: one per logical phase, pushed to origin/main
