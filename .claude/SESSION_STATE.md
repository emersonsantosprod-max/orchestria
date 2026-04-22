## Last Completed Step
Fix lint error in ui/gui_handlers.py — ui/gui_handlers.py (ruff --fix applied: Callable moved to collections.abc)
Test count: 105 passed, 0 failed | Lint: clean

## Next Step
Strip WHAT-comments across app/ — scan app/**/*.py, remove comments that describe what code does; keep only non-obvious external references
Blocker: none

## Invariants Exercised This Session
- CODING_STANDARDS style: ✓ ruff clean across app/ tests/ ui/

## Files Modified
- ui/gui_handlers.py (Callable import moved to collections.abc)

## Baseline
Commit: 4801e3a refactor: enforce CODING_STANDARDS and rename banned-token symbols
Tests: 105 passed — must remain 105 throughout


## Plan
File Path: "\\wsl.localhost\Ubuntu\home\emersonagi\.claude\plans\brainstorming-rules-modular-avalanche.md"

## TODO
- [x] Split app/cli/validar_consist.py (615 lines)
- [x] Split ui/gui.py (591 lines)
- [x] Fix lint error in ui/gui_handlers.py (ruff --fix, then make lint clean)
- [ ] Strip WHAT-comments across app/
- [ ] Pass B: clean parameter names if still violating (make test green)
- [ ] Final verification: make test + make lint + rg banned-token sweep + git diff --stat
- [ ] Commits: one per logical phase, pushed to origin/main
