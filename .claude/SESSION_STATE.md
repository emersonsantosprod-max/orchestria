Plan: /home/emersonagi/.claude/plans/preciso-analisar-a-necessidade-twinkling-sunrise.md
Active session: .claude/sessions/2026-05-08-eliminar-medicao-frequencia.tmp (a criar se necessário)

## Last Completed Step
Eliminada tabela `medicao_frequencia` + storage durável de uploads — Excel da medição é re-lido sob demanda do `data/uploads/medicao.xlsx` apontado por `registro_arquivos`. Helpers extraídos: `_abrir_aba_frequencia` (CM, sem vazamento de handle), `_iter_linhas_dados`, `ler_medicao_do_excel`, `obter_mes_referencia_excel`, `_persistir_upload_permanente` (os.replace atômico). `config.py` valida-antes-de-promover; uploads corrompidos preservam o arquivo durável anterior. `MedicaoRepository` removida; schema faz `DROP TABLE IF EXISTS medicao_frequencia`.
Test count: 250 passed, 0 failed | Lint (app/ tests/): 2 errors pré-existentes (não introduzidos pelo diff) | Quality gate: clean (lines +1.27%, statements +0.62%, sem regressão)

## Next Step
Tech debt: implementar flag `--verbose` em `scripts/quality_gate/__main__.py` listando top-N hashes duplicados com `(arquivo, linha_inicial)`.
Blocker (if any): none

## Invariants Exercised This Session
- Boundary respeitado (app/domain sem sqlite/openpyxl): ✓
- Schema idempotente em conectar() + DROP idempotente de medicao_frequencia: ✓
- Workbook openpyxl sempre via context manager (closing/contextmanager): ✓
- Validação ANTES de promover upload para durável (uploads corrompidos não corrompem registry): ✓
- registro_arquivos['medicao'] passa a apontar para arquivo persistente em data/uploads/medicao.xlsx: ✓
- `validar_distribuicao=True` permanece exclusivamente em /api/run/distribuicao (feature autônoma): ✓

## Files Modified
- app/infrastructure/paths.py (uploads_dir())
- app/infrastructure/data/schema.py (DROP medicao_frequencia + remoção do CREATE)
- app/infrastructure/data/repositories/medicao.py (DELETED)
- app/infrastructure/data/bootstrap.py (primitivas + ler_medicao_do_excel + obter_mes_referencia_excel + registrar_medicao_arquivo + obter_medicao re-read + _persistir_upload_permanente; closing nos demais registrar_*)
- app/infrastructure/data/__init__.py (exports atualizados; sem MedicaoRepository)
- app/api/routes/config.py (4 endpoints: validate-then-os.replace; tmp em uploads_dir)
- app/api/routes/initial_data.py (mes_referencia via Excel + log de erro operacional)
- app/cli/validar_dist.py (registrar_medicao_arquivo)
- tests/test_validar_distribuicao.py (round-trip via novo API + 2 testes de FileNotFoundError)
- tests/api/test_routes_config.py (uploads_dir patched p/ tmp_path; 4 novos testes de durabilidade/corrupção/ausência)

## TODO
- [x] Eliminar medicao_frequencia + storage durável de uploads
- [ ] `scripts/quality_gate` flag `--verbose` para duplication (top-N hashes + paths)

## Resume prompt
Plan: /home/emersonagi/.claude/plans/preciso-analisar-a-necessidade-twinkling-sunrise.md
State: /home/emersonagi/workspace/automacao/.claude/SESSION_STATE.md

Ler ambos. Próximo step pendente: `--verbose` em scripts/quality_gate listando duplicações por (arquivo, linha).