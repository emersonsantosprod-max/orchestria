Plan: /home/emersonagi/.claude/plans/problemas-indentificados-mudan-as-feitas-zesty-parnas.md
Active session: .claude/sessions/2026-05-09-entrega-1-backend-paths-validacao.tmp (closed)

## Last Completed Step
Entrega 1 (V3) concluída — backend: `exports_dir` + `processed_output_path`, remoção de `saida_dir`, `app/domain/reference_month.py` com `mes_referencia_unico` (streaming, early-exit, generator-friendly), refactor de `pipeline._mes_referencia` e rename `obter_mes_referencia_excel` → `obter_mes_referencia_medicao`, novos `obter_medicao_atual` e `obter_mes_referencia_relatorio_treinamento`, validação "sem dados" em `registrar_base_treinamentos`/`registrar_cobranca`, gating de mês em `/api/run/treinamentos` (422 se relatório ≠ medição). UI rename "Base de cobrança" + decisão de não validar mês em base estática (Configurações) registrada via clarificação do usuário.
Test count: 264 passed, 0 failed | Lint: 2 erros pré-existentes (não introduzidos) | Quality gate: clean (violations 0 delta, duplication −214, demais métricas <+10%).

## Next Step
Entrega 2 — Testes: isolamento sem hardcode (fixture `isolated_paths` + guard autouse leve em `tests/conftest.py`); migrar `tests/api/test_routes_run.py` e `test_routes_config*` para o novo padrão; `rm -rf data/` na raiz.
Blocker: none.

Pendência menor: commit `d1d386f` incluiu `.vscode/settings.json` por engano — decidir se manter (config local benigna) ou remover em commit separado.

## Invariants Exercised This Session
- Boundary respeitado (`app/domain/reference_month.py` sem sqlite/openpyxl): ✓
- Schema idempotente / Excel sempre via context manager: ✓ (mantido)
- `mes_referencia_unico` aceita generator + early-exit (consumed=2 em mismatch na 3ª): ✓
- exports_dir deriva de `db_path().parent` (não acoplada a `saida_dir`): ✓
- Backend valida mês mesmo após gating UI (UI bloqueio é UX): ✓ (gating já em rota)
- registry: `obter_medicao_atual` lookup leve, sem reler xlsx: ✓

## Files Modified
- app/infrastructure/paths.py (exports_dir, processed_output_path; remoção de saida_dir)
- app/api/routes/{atestado,treinamentos,distribuicao,ferias}.py (caminho de saída via helper)
- app/api/routes/config.py (catch AutomacaoError → 422)
- app/api/routes/initial_data.py (nome novo do helper de medição)
- app/api/schemas/execution.py (comentário)
- app/cli/normalizar.py (exports_dir)
- app/infrastructure/relatorio_distribuicao.py (exports_dir)
- app/validar_horas.py (exports_dir)
- app/application/pipeline.py (delega a mes_referencia_unico)
- app/domain/reference_month.py (NEW)
- app/infrastructure/data/bootstrap.py (rename obter_mes_referencia_medicao; novos obter_medicao_atual e obter_mes_referencia_relatorio_treinamento; validação "sem dados")
- app/infrastructure/data/__init__.py (exports atualizados)
- tests/test_reference_month.py (NEW)
- tests/test_paths_exports.py (NEW)
- tests/test_mes_referencia_relatorio_treinamento.py (NEW)
- tests/api/test_routes_config_validacao.py (NEW)

## TODO
- [x] Entrega 1 (V3) — backend: paths, validação, domínio
- [ ] Entrega 2 — testes: isolamento sem hardcode (`isolated_paths` + guard autouse leve)
- [ ] Entrega 3 — UI: navegação, rename, gating, modularização
- [ ] Entrega 4 — Cleanup documental