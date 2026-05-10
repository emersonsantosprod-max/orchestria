# PROJECT_STRUCTURE.md

SSOT estrutural. Layered architecture: `domain` (puro) → `application`
(orquestração) → `infrastructure` (I/O) → composition root (CLI/desktop).
Janela de migração flat→layered encerrada em Entrega 4a/4b; resta
`app/validar_horas.py` como único módulo flat (sem target path).

## Layers

### `app/domain/` — funções puras + dataclasses

Imports permitidos: stdlib, `app.domain.*`. Proibidos: `sqlite3`,
`openpyxl`, `app.application.*`, `app.infrastructure.*`.

- `core.py` — `Update`, `Inconsistencia`, factories (`inconsistencia`),
  normalizadores (`normalizar_matricula`, `deduplicar_observacao`),
  `LIMITE_HORAS_TRABALHADAS`.
- `errors.py` — `AutomacaoError`, `PlanilhaInvalidaError`.
- `normalizacao.py` — `normalizar`, `normalizar_chave` (NFKD + accent-fold
  + UPPER + whitespace-collapse). Canônico domain-wide para chaves de
  lookup. Ver `.claude/rules/tag-and-normalization.md`.
- `column_aliases.py` — `COLUMN_ALIASES` + `OBRIGATORIAS`. Fonte única
  de aliases de header da Medição. Ver `.claude/rules/column-mapping.md`.
- `reference_month.py` — `obter_mes_referencia_medicao_lite` (register-time
  lite) + `mes_referencia_unico` (Execute-time estrito).
- `treinamento.py` — `gerar_updates_treinamento`.
- `ferias.py` — `gerar_updates_ferias` + `FeriasContext` (frozen
  dataclass com 8 campos: base_cobranca, medicao_por_matricula,
  md_cobranca/sg_funcao/unidade por chave, base_tags_por_chave,
  mes_referencia, col_map).
- `atestado.py` — `gerar_updates_atestado` (seta `tag='ATESTADO'` explícito).
- `distribuicao.py` — `validar_aderencia_distribuicao`, `gerar_relatorio`,
  `InconsistenciaDistribuicao`.
- `distribuicao_contratual.py` — normalização de distribuição contratual.

### `app/application/` — orquestração + ports

Imports permitidos: stdlib, `app.domain.*`, `typing.Protocol`. Proibidos:
`app.infrastructure.*`, `sqlite3`, `openpyxl`. Exceção: `pipeline.py` é o
multi-domain composition point — pode importar `app.infrastructure.*`.

- `pipeline.py` — `executar_pipeline`. Recebe `conn` via DI; monta
  `FeriasContext` (incluindo `BaseTagsRepository(conn).todos()`); não
  abre conexão; não executa bootstrap.
- `ports.py` — Protocols por negócio (ex.: `TabelaClassificacao`).
- `services/lancar_treinamentos.py` — `LancarTreinamentosService`.
- `services/validacao_distribuicao.py` — `validar_para_dominio` (boundary
  do pipeline para validação BD vs Medição).

### `app/infrastructure/` — adapters de I/O

Única camada que toca `sqlite3` / `openpyxl` / filesystem. Sem regra de
import — pode importar tudo.

- `loaders.py` — extrai `entrada/*.xlsx`; sem lógica de negócio.
- `excel.py` — escrita em `saida/` via `salvar_via_zip`; consome
  `domain.column_aliases` em `mapear_colunas`; writer é genérico para
  TAG (via `upd.tag`).
- `excel_distribuicao.py` — leitura/normalização do xlsx de distribuição.
- `relatorio_distribuicao.py` — `salvar_relatorio` (txt em `saida_dir()`).
- `paths.py` — `db_path()`, `exports_dir()`, `logs_dir()`,
  `validar_arquivo_referenciado` (fonte canônica de validação de path).
  Resolução determinística dev × frozen.
- `logging_config.py` — `setup_logging()` idempotente; rotating handler
  em `logs/automacao.log`.

#### `app/infrastructure/data/` — SQLite layer

- `connection.py` — abre conexão SQLite por request.
- `schema.py` — DDL idempotente (`create_schema`); inclui `base_tags`,
  `registro_arquivos`, `catalogo`, `cobranca`, `distribuicao`.
- `bootstrap.py` — `popular_bd_se_vazio`, `registrar_*`, `obter_*`.
- `registry.py` — `registrar_arquivo(tipo, caminho)`, `obter_*_atual`.
- `repositories/base_tags.py` — `BaseTagsRepository` (lookup
  normalizado por chave composta).
- `repositories/ferias.py` — `FeriasRepository` (regras de cobrança).
- `repositories/treinamentos.py` — `TreinamentosRepository` (catálogo).
- `repositories/distribuicao.py` — `DistribuicaoRepository`.

### `app/api/` — FastAPI HTTP layer

- `main.py` — app factory; monta `ui/web/dist/` como StaticFiles.
- `dependencies.py` — DI helpers (conn, logger).
- `routes/registry.py` — `POST /api/registry/<tipo>` (JSON `{caminho}`).
- `routes/{atestado,ferias,treinamentos,distribuicao}.py` —
  `POST /api/run/<modulo>`. Lê filepath da medição via
  `obter_medicao_atual(conn).caminho`.
- `routes/initial_data.py` — `GET /api/initial-data`.
- `schemas/{execution,initial_data}.py` — Pydantic response models.

### `app/main.py` + `app/cli/` — composition root (CLI)

Único entry-point CLI: `python -m app.main`. Constrói adapters, executa
bootstrap, injeta no service / pipeline.

- `main.py` — argparse com subcomandos: `executar` (default) |
  `normalizar` | `validar-dist` | `validar-hr` | `validar-consist`.
- `cli/normalizar.py` — normaliza distribuição contratual; produz
  `data/saida/distribuicao_contratual_normalizada.xlsx`.
- `cli/validar_dist.py` — registra BD/Medição no SQLite e gera relatório.
- `cli/validar_hr.py` — chama `validar_horas`; relatório em `data/saida/`.
- `cli/validar_consist.py` + `validar_consist_comparar.py` +
  `validar_consist_relatorio.py` — comparador planilha original × processada.

### `app/desktop_entry.py` — composition root (desktop)

Sobe uvicorn em 127.0.0.1:8000 e abre janela pywebview com a SPA. Expõe
`JsApi.escolher_arquivo` (dialog nativo do SO) via `webview` JS bridge.
Empacotado por `AutomacaoMedicao.spec`. Smoke procedure em
`.claude/rules/build-smoke.md`.

### `app/ui/web/` — frontend SPA (servido pelo FastAPI)

- `src/App.jsx` — composition root JSX (Sidebar + Main + LogPanel).
- `src/main.jsx` — Vite entry.
- `src/components/` — presentational components (ConfigCard, ConfigView,
  ExecucaoView, LogPanel, ModuleRow, SessionBlock, Sidebar, primitives,
  skeletons, format).
- `src/modules/registry/index.js` — fetch wrappers para `/api/registry/*`.
- `src/modules/gating/index.js` — `getRunBlockReason` (decide se Executar
  está bloqueado por falta de configuração).
- `src/modules/formatters/index.js` — `fmtMes`, `fmtRelative`.
- `src/modules/lifecycle/reducer.js` — reducer + initialState.
- Build: `npm run build` → `app/ui/web/dist/` (gitignored, empacotado
  pelo `.spec` como StaticFiles).

### Flat (não migrado)

- `app/validar_horas.py` — validação de Hr Trabalhadas (col 19); limites
  0 ≤ valor ≤ `LIMITE_HH` (9h10min); sem DB.

## Resources

- `logs/automacao.log` — log rotativo (1 MiB × 5 backups); via
  `paths.logs_dir()`.
- `data/automacao.db` — SQLite (`paths.db_path()`).
- `data/exports/` — relatórios e Medição processada (`paths.exports_dir()`).
- `assets/distribuicao_contratual_normalizada.xlsx` e
  `assets/base_treinamentos.xlsx` — SSOTs versionados, bundleados pelo
  `.spec`.

## Tests

- `tests/` — pytest discovery em raiz (configurado em `pyproject.toml`).
- `tests/conftest.py` — `isolated_paths` fixture (monkeypatch + tmp_path).
- `tests/fixtures/ferias_factories.py` — builders + `build_ferias_context`.
- `tests/fixtures/*` — builders por domínio.
- `tests/test_layer_boundaries.py` — enforcement: módulos em `app/domain/`
  não importam `sqlite3` / `openpyxl`; módulos em `app/application/services/`
  não importam `app.infrastructure.*`.

## Tooling

- `pyproject.toml` — `[tool.setuptools] packages` enumera todos os pacotes.
  Runtime dep crítica: `pywebview==5.4`.
- `Makefile` — `make test` (pytest), `make lint` (ruff), `make dev`
  (`python -m app.main`), `make quality-gate`.
- `quality_baseline.json` — baseline versionado do quality gate.
- `AutomacaoMedicao.spec` — PyInstaller spec; falha cedo se pywebview
  ausente; hiddenimports para WebView2 (EdgeChromium) default.
- `scripts/quality_gate/` — measurement + gate.
- `scripts/diff_medicao.py` — comparação célula a célula via openpyxl
  read-only (Layer 2 da validação).
