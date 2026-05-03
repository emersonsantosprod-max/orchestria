# CLAUDE.md

## PROJECT
Python automation for workforce measurement (medição) in petrochemical maintenance.
Stack: Python, openpyxl, SQLite, PyInstaller. CLI: `python -m app.main`; GUI: `ui/gui.py`.
Structure: `PROJECT_STRUCTURE.md`.

## INVARIANTS

- Inconsistência: registro válido extraído que não pôde ser aplicado na planilha.
- Não são inconsistências: férias sem aprovação; dados fora do critério de aplicação.
- Férias com período fora do mês de referência são ignoradas silenciosamente.
- Medição cobre único mês; `pipeline._mes_referencia` levanta `PlanilhaInvalidaError` em multi-mês.
- PyInstaller spec: `AutomacaoMedicao.spec`.

## CONTRACTS

- `Update.desconto_min`: domínio em minutos; writer converte para HH:MM — não pré-converter.
- `Inconsistencia`: construir via `core.inconsistencia(origem, ...)` — nunca instanciar diretamente.
- `Update`/`Inconsistencia`: dataclasses puras — acesso por atributo, nunca `.get()`/`[key]`/`in`.
- `gerar_updates_treinamento(dados, tabela_classificacao, observacoes_existentes=None)` → `(list[Update], list[Inconsistencia])`.
- `gerar_updates_ferias(dados, base_cobranca, medicao_por_matricula, md_cobranca_por_chave, sg_funcao_por_chave, mes_referencia, col_map)` → `(list[Update], list[Inconsistencia])`.
- `gerar_updates_atestado(dados)` → `(list[Update], list[Inconsistencia])`.
- `pipeline.executar_pipeline(..., conn=None, validar_distribuicao=False)`: `validar_distribuicao=True` exige `conn`.
- `app.paths.db_path()` resolve o caminho do SQLite — nunca `Path('data/automacao.db')`.

## CRITICAL

- Não substituir `salvar_via_zip` por openpyxl write mode — ~4s → ~42s.
- Não reordenar `updates_treinamento + updates_ferias` em `pipeline.executar_pipeline` — quebra `test_ferias_sobrescreve_observacao_de_treinamento_na_mesma_celula`.
- Não alterar formato de desconto `HH:MM` — testes fixos.
- Não alterar passada única em `indexar_e_ler_dados()` — `read_only` proíbe acesso aleatório.
- Não alterar chave de índice `(matricula, data)` — quebra indexação e aplicação.
- Não alterar prefixo `'TREIN. '` — `'TREIN.' in obs_celula` é marca de idempotência.
- Divergência multi-linha reportada apenas para `tipo='treinamento'`; férias/atestado sobrescrevem.

## ARCHITECTURE

Flow: `entrada/` → `loaders` → `pipeline` → `[ferias|treinamento|atestado|distribuicao]` → `aplicar_updates` → `saida/`

Layer rules: `.claude/rules/boundary.md` | SQLite rules: `.claude/rules/sqlite.md` | Migration state: `.claude/skills/migration-window/SKILL.md`

## SKILLS & RULES

Skills index: `.claude/skills/INDEX.md`
Rules (sempre carregadas): `.claude/rules/` — boundary, sqlite, testing, coding-standards, data-loading
Sessions: estado vivo em `.claude/sessions/<data>-<topico>.tmp`; `SESSION_STATE.md` aponta para o `.tmp` ativo.
