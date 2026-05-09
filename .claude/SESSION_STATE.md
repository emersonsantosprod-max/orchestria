Plan: /home/emersonagi/.claude/plans/ler-session-state-e-claude-sessions-2026-sorted-breeze.md
Active session: .claude/sessions/2026-05-08-reorg-estrutura.tmp (a criar)

## Last Completed Step
Reorg estrutural — ui/→app/ui/, docs/→.claude/, deletados assets/ data/ docs/ dist/ caches egg-info; pipeline emite 'validar_distribuicao=True ignorado: bd_distribuicao vazia' quando bd está vazia; eliminados popular_bd_se_vazio, popular_treinamentos_se_vazio, bundled_distribuicao_xlsx, bundled_treinamentos_xlsx.
Test count: 244 passed, 0 failed | Quality gate: exit 0 | Commit: 66b8d42

## Next Step
Tech debt registrada: implementar flag `--verbose` em `scripts/quality_gate/__main__.py` listando top-N hashes duplicados com `(arquivo, linha_inicial)` para localização de duplicação.
Blocker (if any): none

## Invariants Exercised This Session
- Boundary respeitado (app/domain sem sqlite/openpyxl): ✓
- Schema idempotente em conectar(): ✓ — testes que dependiam de popular_bd_se_vazio agora usam só conectar()
- Pipeline single-pass mês de referência: ✓
- Quality gate exit 0 sobre HEAD: ✓ — métricas absolutas estáveis, AST métricas caíram (delete de funções)

## Files Modified
- ui/ → app/ui/ (git mv, histórico preservado)
- docs/PROJECT_STRUCTURE.md → .claude/PROJECT_STRUCTURE.md
- AutomacaoMedicao.spec, app/api/main.py, app/infrastructure/paths.py, CLAUDE.md, Makefile (paths atualizados)
- app/infrastructure/data/bootstrap.py (eliminados popular_bd/treinamentos_se_vazio + import bundled_*)
- app/infrastructure/data/__init__.py (re-exports limpos)
- app/cli/validar_dist.py, app/api/main.py (chamadas removidas)
- app/application/pipeline.py (emite 'ignorado' em bd vazia)
- tests/test_integration.py, tests/test_db.py (asserts compatíveis; 4 testes obsoletos removidos)
- pyproject.toml (cache_dir/cache-dir → build/)

## TODO
- [x] Reorg estrutural + eliminação de bootstrap-by-xlsx
- [ ] `scripts/quality_gate` flag `--verbose` para duplication (top-N hashes + paths)

## Resume prompt
Plan: /home/emersonagi/.claude/plans/ler-session-state-e-claude-sessions-2026-sorted-breeze.md
State: /home/emersonagi/workspace/automacao/.claude/SESSION_STATE.md

Ler ambos. Próximo step: `--verbose` em scripts/quality_gate listando duplicações por (arquivo, linha).