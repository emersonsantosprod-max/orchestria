# PROJECT_STRUCTURE.md

SSOT estrutural. Quando um caminho-alvo difere do caminho-atual, o atual está marcado **(legacy)** e o alvo **(target)**. Durante a janela de migração os dois coexistem; ver CLAUDE.md → ARCHITECTURE → Migration window.

## Layers

### `app/domain/` — funções puras + dataclasses
Imports permitidos: stdlib, `app.domain.*`. Proibidos: `sqlite3`, `openpyxl`, `app.application.*`, `app.infrastructure.*`.

- `app/domain/core.py` (target) ← `app/core.py` (legacy) — `Update`, `Inconsistencia`, factories (`inconsistencia`), normalizadores (`normalizar_matricula`, `deduplicar_observacao`), `LIMITE_HORAS_TRABALHADAS`.
- `app/domain/errors.py` (target) ← `app/errors.py` (legacy) — `AutomacaoError`, `PlanilhaInvalidaError`.
- `app/domain/treinamento.py` (target) ← `app/treinamento.py` (legacy) — `gerar_updates_treinamento`.
- `app/domain/ferias.py` — `gerar_updates_ferias`.
- `app/domain/atestado.py` (target) ← `app/atestado.py` (removido) — `gerar_updates_atestado`.
- `app/distribuicao_contratual.py` — normalização de distribuição contratual (não migrado nesta janela).
- `app/validar_distribuicao.py` — validação BD vs Medição + `validar_para_dominio` (boundary do pipeline).
- `app/validar_horas.py` — validação de Hr Trabalhadas (col 19); limites 0 ≤ valor ≤ `LIMITE_HH` (9h10min); sem DB.

### `app/application/` — orquestração + ports
Imports permitidos: stdlib, `app.domain.*`, `typing.Protocol`. Proibidos: `app.infrastructure.*`, `sqlite3`, `openpyxl`.

- `app/application/pipeline.py` (target) ← `app/pipeline.py` (legacy) — `executar_pipeline`. Recebe `conn` via DI; não abre conexão; não executa bootstrap.
- `app/application/ports.py` (target, vazio até Step 3) — Protocols por negócio (ex.: `TabelaClassificacao`).
- `app/application/services/lancar_treinamentos.py` (target, criado em Step 3) — `LancarTreinamentosService`.

### `app/infrastructure/` — adapters de I/O
Única camada que toca `sqlite3` / `openpyxl` / filesystem. Sem regra de import — pode importar tudo.

- `app/infrastructure/loaders.py` (target) ← `app/loaders.py` (legacy) — extrai `entrada/*.xlsx`; sem lógica de negócio.
- `app/infrastructure/excel.py` (target) ← `app/excel.py` (legacy) — escrita em `saida/` via `salvar_via_zip`; não importa `app.domain.*`.
- `app/infrastructure/db.py` (target) ← `app/db.py` (legacy) — SQLite: `registrar_*`, `obter_*`, `popular_*` (bootstrap idempotente).
- `app/infrastructure/paths.py` (target) ← `app/paths.py` (legacy) — `db_path()`, `saida_dir()`, `logs_dir()`, xlsx empacotado. Resolução determinística dev × frozen.
- `app/infrastructure/logging_config.py` (target) ← `app/logging_config.py` (legacy) — `setup_logging()` idempotente; rotating handler em `logs/automacao.log`.
- `app/infrastructure/adapters/sqlite_tabela_classificacao.py` (target, criado em Step 3) — adapter de `TabelaClassificacao`.

### `app/main.py` + `app/cli/` — composition root (CLI)
Único entry-point: `python -m app.main`. Constrói adapters, executa bootstrap, injeta no service / pipeline.

- `app/main.py` — argparse com subcomandos: `executar` (default) | `normalizar` | `validar-dist` | `validar-hr` | `validar-consist`.
- `app/cli/normalizar.py` — normaliza distribuição contratual; produz `data/saida/distribuicao_contratual_normalizada.xlsx`.
- `app/cli/validar_dist.py` — registra BD/Medição no SQLite e gera relatório.
- `app/cli/validar_hr.py` — chama `validar_horas`; relatório em `data/saida/`.
- `app/cli/validar_consist.py` — comparador planilha original × processada.
- `app/cli/validar_consist_comparar.py`, `app/cli/validar_consist_relatorio.py` — helpers.

### `ui/` — composition root (GUI)
- `ui/gui.py` — desktop GUI (tkinter). Bootstrap de SQLite na main thread, exatamente uma vez, ANTES de qualquer thread worker. PyInstaller `AutomacaoMedicao.spec`.
- `ui/gui_handlers.py` — handlers; worker threads abrem suas próprias conexões; `registrar_*` adquire `threading.Lock` da app singleton.

### Recursos
- `assets/distribuicao_contratual_normalizada.xlsx` — SSOT versionado; empacotada via PyInstaller `datas=`; source do bootstrap inicial do SQLite.
- `assets/base_treinamentos.xlsx` — base de classificação de treinamentos; empacotada; source de `popular_treinamentos_se_vazio`.
- `data/automacao.db` — SQLite gravável em `<exe_dir>/data/` (frozen) ou raiz do projeto (dev); resolvido via `paths.db_path()`.
- `data/entrada/`, `data/saida/` — runtime; gitignored.
- `logs/automacao.log` — log rotativo (1 MiB × 5 backups); via `paths.logs_dir()`.

### Tests
- `tests/` — pytest discovery em raiz (configurado em `pyproject.toml`).
- `tests/application/` — testes de services (com fakes de ports).
- `tests/infrastructure/` — testes de adapters (`:memory:` SQLite, sem fixture files).
- `tests/test_layer_boundaries.py` — enforcement: módulos em `app/domain/` não importam `sqlite3` / `openpyxl`; módulos em `app/application/` não importam `app.infrastructure.*`.

### Tooling
- `pyproject.toml` — `[tool.setuptools] packages` enumera todos os pacotes (incluindo `app.domain`, `app.application`, `app.application.services`, `app.infrastructure`, `app.infrastructure.adapters`).
- `Makefile` — `make test` (pytest), `make lint` (ruff em `app/ tests/ ui/`), `make dev` (`python -m app.main`).
- `baseline/` — gitignored; `baseline_treinamento.xlsx` (golden output de Step 1) + `baseline_pytest.txt`. Regerado sob demanda.
- `scripts/diff_medicao.py` — Layer 2 da validação; comparação célula a célula via openpyxl read-only.
