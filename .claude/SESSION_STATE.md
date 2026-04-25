## Last Completed Step
feat: senior-engineer upgrade — atestado fix, silent-corruption guards, file logging — app/pipeline.py, app/excel.py, app/core.py, app/paths.py, app/logging_config.py, app/main.py, app/treinamento.py, app/validar_distribuicao.py, app/validar_horas.py, ui/gui.py, ui/gui_handlers.py
Test count: 123 passed, 0 failed | Lint: clean

## Next Step
GUI smoke on real Windows machine: launch GUI → click "Lançar atestados" (was AttributeError) → confirm output xlsx + log file at logs/automacao.log.
Blocker: sem ambiente Windows/GUI headless neste branch.

## Invariants Exercised This Session
- atestado pipeline: ✓ pipeline.executar_pipeline → atestado.gerar_updates_atestado (was broken: processar_atestados nonexistent)
- single-month referência: ✓ _mes_referencia raises PlanilhaInvalidaError on multi-month
- col_map _ausentes: ✓ mapear_colunas surfaces missing optional cols; pipeline warns when validar_distribuicao=True with cols absent
- multi-row divergence: ✓ indexar_e_ler_dados tracks obs_divergentes/desc_divergentes; aplicar_updates emits 'writer' inconsistência for treinamento
- desconto idempotência: ✓ aplicar_updates skips stacking when obs já contém 'TREIN.'
- frozen-aware paths: ✓ paths.saida_dir() / logs_dir() resolvem por _exe_dir vs _project_root
- main-thread tk: ✓ filedialog.askdirectory marshalled via ctx.marshal_to_main(janela.after)
- LIMITE_HH SSOT: ✓ core.LIMITE_HORAS_TRABALHADAS importado por treinamento.py e validar_horas.py
- file logging: ✓ logging_config.setup_logging idempotente; rotating handler em logs/automacao.log

## Files Modified
- app/pipeline.py (atestado call fix; multi-month raise; _ausentes warn; divergência kwargs)
- app/excel.py (mapear_colunas _ausentes; indexar_e_ler_dados retorna 9-tupla; aplicar_updates aceita divergência sets + guard idempotência treinamento)
- app/core.py (LIMITE_HORAS_TRABALHADAS)
- app/paths.py (saida_dir, logs_dir)
- app/logging_config.py (novo: setup_logging idempotente)
- app/main.py (setup_logging + logger.exception)
- app/treinamento.py (LIMITE_HH = core.LIMITE_HORAS_TRABALHADAS)
- app/validar_distribuicao.py (imports normalizados; saida_dir())
- app/validar_horas.py (LIMITE_HH = core.; saida_dir())
- ui/gui.py (setup_logging; ctx.marshal_to_main)
- ui/gui_handlers.py (logger; marshal_to_main no GuiContext; mostrar_resultado dispatched to main thread)
- tests/test_integration.py (acomoda novo aviso de validar_distribuicao)

## Baseline
Commit: 37603ba (pushed to origin/main)
Tests: 123 passed (+9 novos: atestado_pipeline, idempotencia_treinamento, logging_config, multi_row_divergente, pipeline_mes_referencia)

## Plan
File Path: /home/emersonagi/.claude/plans/role-senior-engineer-upgrade-luminous-rossum.md

## TODO
- [x] A.1 Fix atestado pipeline call + add test
- [x] A.2 Move filedialog.askdirectory to main thread
- [x] A.3 Add paths.saida_dir() and replace CWD-based _DIR_SAIDA
- [x] B.1 Detect multi-row obs/desconto divergence + emit inconsistência
- [x] B.2 Guard treinamento double-desconto on re-run
- [x] B.3 Validate medição reference month (raise on multi-month)
- [x] C.1 Surface missing optional columns via _ausentes
- [x] D.1 Dedupe LIMITE_HH to core.LIMITE_HORAS_TRABALHADAS
- [x] D.2 Normalize imports in validar_distribuicao.py
- [x] E.1 Add structured file logging (app/logging_config.py)
- [x] make test green (123/123)
- [x] make lint clean
- [x] Commit and push (37603ba)
- [ ] GUI smoke end-to-end (requires Windows/GUI environment)