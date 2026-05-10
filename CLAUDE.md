# CLAUDE.md

## PROJECT
Python automation for workforce measurement (medição) in petrochemical maintenance.
Stack: Python, openpyxl, SQLite, PyInstaller. CLI: `python -m app.main`; API: `app/api/main.py`; UI: `app/ui/web/`.
Structure: `.claude/PROJECT_STRUCTURE.md`.

## INVARIANTS

- Inconsistência: registro válido extraído que não pôde ser aplicado na planilha.
- Não são inconsistências: férias sem aprovação; dados fora do critério de aplicação.
- Férias com período fora do mês de referência são ignoradas silenciosamente.
- Medição cobre único mês — premissa do domínio. Register-time extrai
  `(year, month)` da primeira data via `obter_mes_referencia_medicao_lite`;
  `pipeline._mes_referencia` mantém validação estrita (`mes_referencia_unico`)
  no Execute como defesa em profundidade.
- `registro_arquivos` guarda **caminho original** do arquivo no host — fonte
  de verdade de ownership. SQLite (catalogo, cobranca, distribuicao, tags)
  é materialização eager para lookup; re-import é explícito (re-registrar
  via UI). Sem `data/uploads/` (descontinuado em Entrega 4a).
- PyInstaller spec: `AutomacaoMedicao.spec`. Desktop wrapper via pywebview;
  build empacotado **exige** webview do SO (sem fallback silencioso).

## CONTRACTS

- `Update.desconto_min`: domínio em minutos; writer converte para HH:MM — não pré-converter.
- `Inconsistencia`: construir via `core.inconsistencia(origem, ...)` — nunca instanciar diretamente.
- `Update`/`Inconsistencia`: dataclasses puras — acesso por atributo, nunca `.get()`/`[key]`/`in`.
- `gerar_updates_treinamento(dados, tabela_classificacao, observacoes_existentes=None)` → `(list[Update], list[Inconsistencia])`.
- `gerar_updates_ferias(dados_ferias, base_cobranca, medicao_por_matricula, md_cobranca_por_chave, sg_funcao_por_chave, mes_referencia, col_map)` → `(list[Update], list[Inconsistencia])`.
- `gerar_updates_atestado(dados)` → `(list[Update], list[Inconsistencia])`.
- `pipeline.executar_pipeline(..., conn=None, validar_distribuicao=False)`: `validar_distribuicao=True` exige `conn`.
- `app.paths.db_path()` resolve o caminho do SQLite — nunca `Path('data/automacao.db')`.
- `validar_arquivo_referenciado(path, exts)` em `app.infrastructure.paths` é
  a fonte canônica de validação de path (existência, extensão, leitura).
  Usar em register-time E Execute-time.
- Rotas `POST /api/registry/<tipo>` recebem JSON `{"caminho": str}` com path
  absoluto do arquivo no host. `<tipo>` ∈ {medicao, treinamentos, cobranca,
  distribuicao, tags}. Substituem as antigas `POST /api/config/<tipo>` (UploadFile).
- Rotas `POST /api/run/<modulo>` leem o filepath da medição via
  `obter_medicao_atual(conn).caminho` (registro_arquivos). Apenas o
  relatório do módulo vem por multipart (`relatorio` ou `catalogo`).

## CRITICAL

- Não substituir `salvar_via_zip` por openpyxl write mode — ~4s → ~42s.
- Não reordenar `updates_treinamento + updates_ferias` em `pipeline.executar_pipeline` — quebra `test_ferias_sobrescreve_observacao_de_treinamento_na_mesma_celula`.
- Não alterar formato de desconto `HH:MM` — testes fixos.
- Não alterar passada única em `indexar_e_ler_dados()` — `read_only` proíbe acesso aleatório.
- Não alterar chave de índice `(matricula, data)` — quebra indexação e aplicação.
- Não alterar prefixo `'TREIN. '` — `'TREIN.' in obs_celula` é marca de idempotência.
- Divergência multi-linha reportada apenas para `tipo='treinamento'`; férias/atestado sobrescrevem.

## QUALITY GATE

Após cada step de TODO que toca `app/`, `tests/` ou `scripts/`, rodar
`python -m scripts.quality_gate`. Limiares e procedimento de revisão (3
tentativas) em `.claude/rules/quality-gate.md`. Pular em diff trivial
(≤3 linhas líquidas). Baseline em `quality_baseline.json` — atualizar
apenas manualmente via `--update-baseline`.

## ARCHITECTURE

Flow: `entrada/` → `loaders` → `pipeline` → `[ferias|treinamento|atestado|distribuicao]` → `aplicar_updates` → `saida/`

Layer rules: `.claude/rules/boundary.md` | SQLite rules: `.claude/rules/sqlite.md` | Migration state: `.claude/skills/migration-window/SKILL.md`

## SKILLS & RULES

Skills (auto via `description`/`paths`): `.claude/skills/` — brainstorming, react, python-testing, repository-pattern, migration-window, strategic-compact
Rules (sempre carregadas): `.claude/rules/` — boundary, sqlite, testing, coding-standards, data-loading, quality-gate
Agents (delegáveis): `.claude/agents/` — architect, code-reviewer, tdd-guide
Sessions: estado vivo em `.claude/sessions/<data>-<topico>.tmp`; `SESSION_STATE.md` aponta para o `.tmp` ativo.
