Plan: /home/emersonagi/.claude/plans/scope-entrega-5-cozy-crystal.md
Active session: Entrega 5 — Cleanup documental + harness + smoke 4b fix

## Last Completed Step
Entrega 5 concluída (parte editável) — 5 frentes + smoke fix:
- **A (smoke 4b)**: AutomacaoMedicao.spec endurecida — `try: import webview`
  falha cedo com mensagem clara se pywebview ausente do venv de build.
  Hiddenimports adicionais: `webview.platforms.edgechromium` + `proxy_tools`
  (default Win10+). PRE detectou pywebview ausente em ambos venvs — fix
  raiz é `pip install -e .` no venv_win antes do build. Procedimento
  completo em `.claude/rules/build-smoke.md`.
- **B (migration cleanup)**: shim posicional removido de
  `gerar_updates_ferias` (ferias.py:112-154 simplificado para
  `(dados, ctx: FeriasContext)`). 15 callers de teste migrados em 3
  arquivos (test_ferias_rules.py, test_ferias_edge_cases.py,
  test_ferias_contract_guard.py) via helper `build_ferias_context`
  novo em fixtures. Teste dedicado `test_assinatura_legacy_posicional_compativel`
  deletado. Schemas órfãos `app/api/schemas/config.py` (UploadResponse)
  removidos. UI README atualizado para `/api/registry/<tipo>`.
- **C (rules + CLAUDE.md)**: 3 novos rule files:
  `.claude/rules/tag-and-normalization.md`,
  `.claude/rules/column-mapping.md`,
  `.claude/rules/build-smoke.md`. CLAUDE.md 98→78 linhas com
  referências explícitas; INVARIANTS/CONTRACTS de TAG/normalização
  movidos para o rule dedicado.
- **D (PROJECT_STRUCTURE.md)**: rewrite end-to-end (165 linhas).
  Removidas todas as referências a `(legacy)` exceto `validar_horas.py`.
  Adicionados: `domain/{normalizacao,column_aliases,reference_month}.py`,
  `infrastructure/data/` subtree completa (schema, bootstrap, registry,
  4 repositories), `api/` subtree (main, dependencies, routes/, schemas/),
  `desktop_entry.py` como composition root, `ui/web/src/modules/`
  (4 modules).
- **E (skills)**: `migration-window/SKILL.md` condensada 50→34 linhas
  marcando janela como encerrada; `python-testing/SKILL.md` reescrita
  816→163 linhas codebase-specific (isolated_paths, build_*_context,
  fakes Protocol, :memory: SQLite, sem coverage gate, sem class TestX).

Test count: 303 passed, 0 failed (era 304; -1 do legacy_posicional deletado)
| Lint: 1 erro pré-existente (não introduzido) | Quality gate: clean
(lines 8335→8311, statements 5299→5282, branches 808→802, violations/
duplication/oversized/functions estáveis).

⚠️ Smoke do build empacotado pendente — usuário precisa rodar no host
Windows: (1) `pip install -e .` no venv_win, (2) `pyinstaller
AutomacaoMedicao.spec`, (3) checklist em `.claude/rules/build-smoke.md`.

## Next Step
Smoke do build empacotado (Frente A validation) no Windows.
Blocker: nenhum bloqueante de código; aguarda execução do usuário.

## Invariants Exercised This Session
- Shim aditivo é dívida e deve ser removido quando janela consolidar: ✓
- Helper `build_ferias_context` expõe os 8 campos do FeriasContext via overrides: ✓
- CLAUDE.md como índice; rules/ como detalhe referenciado: ✓
- PROJECT_STRUCTURE.md como SSOT estrutural (rewrite, não append): ✓
- migration-window skill encerrada explicitamente quando 100% migrado: ✓
- python-testing skill reflete padrões reais (não genéricos): ✓

## Files Modified (Entrega 5)

Backend / spec:
- AutomacaoMedicao.spec (fail-early on missing pywebview + EdgeChromium hiddenimports)
- app/domain/ferias.py (remove shim posicional)
- app/api/schemas/config.py (DELETED — schemas UploadResponse órfãos)

Tests:
- tests/fixtures/ferias_factories.py (+build_ferias_context)
- tests/test_ferias_rules.py (5 calls migrated)
- tests/test_ferias_edge_cases.py (8 calls migrated)
- tests/test_ferias_contract_guard.py (helper + 1 test migrated)
- tests/test_ferias_tag_lookup.py (legacy_posicional test deleted)

Harness / docs:
- CLAUDE.md (98→78, INVARIANTS/CONTRACTS densificados, rules linkados)
- .claude/PROJECT_STRUCTURE.md (rewrite end-to-end)
- .claude/rules/tag-and-normalization.md (NEW)
- .claude/rules/column-mapping.md (NEW)
- .claude/rules/build-smoke.md (NEW)
- .claude/skills/migration-window/SKILL.md (50→34, "encerrada")
- .claude/skills/python-testing/SKILL.md (816→163, codebase-specific)
- app/ui/web/README.md (endpoints atualizados para /api/registry)

## TODO
- [x] Entrega 1 (V3) — backend: paths, validação, domínio
- [x] Entrega 2 (V3) — testes: isolamento explícito
- [x] Entrega 3 (V3) — UI: navegação, rename, gating, modularização
- [x] Entrega 4a (V3+) — lifecycle: path-based registry + dialog nativo + LogPanel toggle
- [x] Entrega 4b — Férias TAG feature (normalizacao + base_tags + Update.tag + FeriasContext)
- [x] Entrega 5 — Cleanup documental + harness + smoke 4b fix
- [ ] Smoke 4b execution (Windows host)
