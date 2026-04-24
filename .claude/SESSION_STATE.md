## Last Completed Step
chore: remove "Importar Base de Treinamentos" manual surface (UI + CLI) and tighten connection hygiene — app/main.py, ui/gui.py, ui/gui_handlers.py, app/pipeline.py, tests/test_db.py
Test count: 114 passed, 0 failed | Lint: clean

## Next Step
GUI smoke on real machine: delete data/automacao.db → launch GUI → click "Lançar treinamentos" twice back-to-back → confirm no `database is locked` in log and saida/medicao_processada.xlsx gerado.
Blocker: sem ambiente Windows/GUI headless neste branch.

## Invariants Exercised This Session
- Pipeline DI de conn: ✓ pipeline.executar_pipeline permanece orquestração-only, não abre conn
- Bootstrap na boundary: ✓ popular_bd_se_vazio + popular_treinamentos_se_vazio chamados em app/main.py e ui/gui_handlers.py._executar_fluxo
- Single-connection hygiene: ✓ iniciar_validacao agora usa try/finally explícito; _executar_fluxo já tinha try/finally; conn nunca fica zombie
- registrar_base_treinamentos: ✓ mantido como carrier interno do bootstrap (apenas uma call site em app/db.py:257)

## Files Modified
- app/main.py (remove _comando_importar_base_treinamentos + subparser + dispatch; add popular_treinamentos_se_vazio para CLI)
- ui/gui.py (remove botao_importar_base + import + entry em _todos_botoes)
- ui/gui_handlers.py (remove iniciar_importar_base_treinamentos + pre_check_conn; try/finally em iniciar_validacao)
- app/pipeline.py (atualiza mensagem de erro obsoleta para bootstrap/assets)
- tests/test_db.py (remove test_registrar_base_treinamentos_substitui_dados_anteriores — cenário manual-only)

## Baseline
Commit: a ser criado
Tests: 114 passed — reduziu em 1 (teste obsoleto de substituição manual removido)

## Plan
File Path: /home/emersonagi/.claude/plans/brainstorming-plano-de-harmonic-wigderson.md

## TODO
- [x] Remove CLI subcommand importar-base-treinamentos
- [x] Remove UI button Importar Base de Treinamentos
- [x] Remove iniciar_importar_base_treinamentos handler
- [x] Fix iniciar_validacao connection hygiene
- [x] Clean obsolete tests
- [x] make test green (114/114)
- [x] make lint clean
- [x] Commit and push
- [ ] GUI smoke end-to-end (requires Windows/GUI environment)
