Plan: /home/emersonagi/.claude/plans/ler-home-emersonagi-workspace-automacao-jazzy-trinket.md
Active session: Entrega 4b — Férias TAG feature

## Last Completed Step
Entrega 4b concluída — Férias TAG feature (10 commits + baseline update):
- `app/domain/normalizacao.py` (NEW): `normalizar`/`normalizar_chave` (NFKD + accent-fold + UPPER + whitespace-collapse) — canônicos para lookups domain-wide.
- `app/domain/column_aliases.py` (NEW): `COLUMN_ALIASES` único + `OBRIGATORIAS`. `mapear_colunas` consome via fachada; alias `unidade` adicionado.
- `app/infrastructure/data/repositories/base_tags.py` (NEW) + tabela `base_tags(sg_funcao, unidade, md_cobranca, situacao, tag)` PK composta.
- `bootstrap.registrar_base_tags`: 5 colunas, normalize keys+tag, header opcional, dedup por chave, PlanilhaInvalidaError em vazia.
- `Update.tag: str | None`; writer genérico (`upd.tag` substitui branch `tipo='atestado'`); `gerar_updates_atestado` seta `tag='ATESTADO'` explicitamente.
- `FeriasContext` (frozen dataclass) + nova assinatura `gerar_updates_ferias(dados, ctx)` com shim retro-compat para forma posicional legada (migration aditiva).
- Lookup de tag por chave normalizada `(funcao, unidade, md, situacao)`; misses agregados em UMA inconsistência por chave (count + lista de matrículas).
- `pipeline.executar_pipeline` carrega `BaseTagsRepository(conn).todos()` e constroi FeriasContext.
- `excel.indexar_e_ler_dados` retorna `unidade_por_chave` (10-tupla); callers explicitos atualizados.
- `POST /api/registry/tags` + `initial_data.config.{base_tags, base_cobranca}`.
- UI: CONFIG_KEYS adiciona `base_tags`; gating `ferias` exige `needsBaseTags`.
- CLAUDE.md: novos INVARIANTS (Update.tag, dedupe por chave, base_tags vazio = inativo) + CONTRACTS (FeriasContext, normalizar/normalizar_chave, COLUMN_ALIASES).
- Baseline atualizado pós-feature: lines 7227→8335, functions 450→533, duplication 712→906.

Test count: 304 passed, 0 failed | npm build: clean (176.72 KB JS) | Lint: 1 erro pré-existente (não introduzido) | Quality gate: clean (baseline atualizado).

⚠️ Smoke do build empacotado pendente (PyInstaller + WebView2 só rodam no host Windows): validar dialog nativo + Execute + restart + 4 cards em Configurações + Executar Férias bloqueado sem base_tags.

## Next Step
Entrega 5 — Cleanup documental (futura). Ou consumidor define próxima janela.
Blocker: none.

## Invariants Exercised This Session
- `normalizar_chave` como canônico domain-wide: ✓
- `Update.tag` como mecanismo único de TAG (writer genérico): ✓
- Inconsistências de tag deduplicadas por chave normalizada: ✓
- `base_tags` vazio = feature inativa (compat aditiva): ✓
- `FeriasContext` montado pelo pipeline (composition root): ✓
- `registro_arquivos` é SoT de ownership; SQLite materialização eager: ✓

## Files Modified (Entrega 4b)
Backend:
- app/domain/normalizacao.py (NEW)
- app/domain/column_aliases.py (NEW)
- app/domain/core.py (Update.tag)
- app/domain/ferias.py (FeriasContext + nova assinatura + dedupe + lookup)
- app/domain/atestado.py (tag='ATESTADO' explicit)
- app/infrastructure/excel.py (writer genérico via upd.tag; aliases via domain; unidade_por_chave; mapear_colunas refactor)
- app/infrastructure/data/schema.py (+base_tags)
- app/infrastructure/data/repositories/base_tags.py (NEW)
- app/infrastructure/data/bootstrap.py (registrar_base_tags + import normalizar)
- app/infrastructure/data/__init__.py (BaseTagsRepository + registrar_base_tags)
- app/application/pipeline.py (FeriasContext build + 10-tupla unpack)
- app/api/routes/registry.py (POST /tags)
- app/api/routes/initial_data.py (config.base_tags + base_cobranca via registry)
- CLAUDE.md (INVARIANTS + CONTRACTS)
- quality_baseline.json (atualizado)

Frontend:
- app/ui/web/src/App.jsx (CONFIG_KEYS + base_tags)
- app/ui/web/src/modules/gating/index.js (ferias.needsBaseTags=true)

Tests:
- tests/test_normalizar.py (NEW — 9 cases)
- tests/test_column_aliases.py (NEW — 4 cases)
- tests/test_base_tags_repository.py (NEW — 4 cases)
- tests/test_registrar_base_tags.py (NEW — 5 cases)
- tests/test_writer_tag_generic.py (NEW — 4 cases)
- tests/test_ferias_context.py (NEW — 2 cases)
- tests/test_ferias_tag_lookup.py (NEW — 5 cases)
- tests/api/test_routes_registry.py (+3 cases tags)
- tests/test_multi_row_divergente.py (10-tupla unpack)
- tests/test_derivar_mes_referencia_ssot.py (10-tupla unpack)

## TODO
- [x] Entrega 1 (V3) — backend: paths, validação, domínio
- [x] Entrega 2 (V3) — testes: isolamento explícito
- [x] Entrega 3 (V3) — UI: navegação, rename, gating, modularização
- [x] Entrega 4a (V3+) — lifecycle: path-based registry + dialog nativo + LogPanel toggle
- [x] Entrega 4b — Férias TAG feature (normalizacao + base_tags + Update.tag + FeriasContext)
- [ ] Entrega 5 — Cleanup documental (futura)