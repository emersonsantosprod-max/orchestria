Plan: /home/emersonagi/.claude/plans/ler-session-state-e-claude-sessions-2026-hazy-pelican.md
Active session: .claude/sessions/2026-05-06-quality-gate.tmp (concluído)

## Last Completed Step
Quality Gate `duplication` (Tipo-2, 50 tokens, app/ only) — scripts/quality_gate/duplication.py (novo), scripts/quality_gate/__main__.py, scripts/quality_gate/report.py, tests/test_quality_gate.py, .claude/rules/quality-gate.md, quality_baseline.json
Test count: 248 passed, 0 failed | Gate: exit 0 (duplication=712)

## Next Step
Mover `scripts/quality_gate/` (hoje "scripts perdidos" no projeto) para a área de gestão de contexto em `.claude/` — proposta: `.claude/tools/quality_gate/`. Justificativa: a ferramenta serve à governança de contexto/qualidade do agente, não ao runtime de `app/`. Tarefas previstas:
1. Criar `.claude/tools/quality_gate/` e mover os 5 módulos (`__init__.py`, `__main__.py`, `metrics.py`, `report.py`, `violations.py`, `duplication.py`).
2. Ajustar `Makefile` (`quality-gate`, `quality-gate-update`) para o novo módulo path.
3. Ajustar imports relativos/absolutos e `RAIZ_REPO = Path(__file__).resolve().parents[3]`.
4. Atualizar `tests/test_quality_gate.py` imports.
5. Atualizar `.claude/rules/quality-gate.md` (paths e comando).
6. Atualizar `CLAUDE.md` seção QUALITY GATE.
7. Validar: `make test` + `make quality-gate` exit 0 + baseline inalterado.
8. Tech debt anterior (flag `--verbose`) permanece no backlog.
Blocker (if any): definir se `.claude/tools/` é o subdir correto ou se convém `.claude/quality_gate/` direto — esclarecer com o usuário antes de executar.

## Invariants Exercised This Session
- Quality gate fora de app/: ✓ — boundary.md respeitado (código em scripts/)
- Baseline versionado: ✓ — quality_baseline.json commitado
- Gate exit 0 sobre HEAD: ✓ — sem regressão
- Stdlib only: ✓ — duplication usa tokenize+Counter, sem nova dep

## Files Modified
- scripts/quality_gate/duplication.py (novo, ~45 linhas)
- scripts/quality_gate/__main__.py (RAIZ_APP + wire)
- scripts/quality_gate/report.py (ORDEM + ABSOLUTOS)
- tests/test_quality_gate.py (+6 testes)
- .claude/rules/quality-gate.md (limiar + tech debt)
- quality_baseline.json (snapshot com duplication=712)

## TODO
- [x] MVP: violations + oversized_files + lines + functions
- [x] statements
- [x] branches
- [x] duplication (Opção A — janela de tokens)
- [ ] Mover quality_gate de `scripts/` para `.claude/tools/quality_gate/` (gestão de contexto)
- [ ] Tech debt: flag `--verbose` listando (arquivo, linha) das janelas duplicadas