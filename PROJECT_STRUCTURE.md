# PROJECT_STRUCTURE.md

app/core.py → shared types (Update, Inconsistencia) + factories; dataclasses puras
app/loaders.py → extract data from entrada/ xlsx; no business logic → feeds pipeline
app/ferias.py → férias processing: validations, calculations, inconsistencies
app/treinamento.py → treinamentos processing: validations, calculations
app/atestado.py → atestados médicos processing
app/distribuicao_contratual.py → normalização da distribuição contratual (xlsx → registros)
app/validar_distribuicao.py → validação BD vs Medição + mapeamento `validar_para_dominio` (boundary pública para o pipeline)
app/validar_horas.py → validação de Hr Trabalhadas (col 19): limites 0 ≤ valor ≤ LIMITE_HH (9h10min); sem DB.
app/db.py → SQLite: registrar_bd/medicao, obter_*, popular_bd_se_vazio (bootstrap idempotente)
app/paths.py → resolução determinística de caminhos (dev vs PyInstaller frozen). SSOT para `db_path()` e xlsx empacotado.
app/excel.py → Excel I/O: read entrada/, write saida/ via `salvar_via_zip`; não importa módulos de domínio
app/pipeline.py → orquestração pura: load → process → apply → (opcional) validar_distribuicao. Recebe `conn` via DI; não executa bootstrap.
app/main.py → CLI entry-point; argparse com subcomandos: `run` (default) | `normalizar` | `validar-dist` | `validar-consist`. Executa bootstrap antes de `pipeline.processar()`.
app/cli/normalizar.py → normaliza distribuição contratual; produz `data/saida/distribuicao_contratual_normalizada.xlsx`.
app/cli/validar_dist.py → registra BD/Medição no SQLite e gera relatório de validação.
app/cli/validar_hr.py → lê medicao_base.xlsx, chama validar_horas, grava relatório em data/saida/.
app/cli/validar_consist.py → compara planilha original × processada (auditor autônomo).
ui/gui.py → desktop GUI (tkinter); PyInstaller `AutomacaoMedicao.spec`. Executa bootstrap antes de chamar `pipeline.processar()`.
data/entrada/distribuicao_contratual_normalizada.xlsx → empacotada no bundle (PyInstaller `datas=`); source do bootstrap inicial.
data/automacao.db → SQLite gravável em `<exe_dir>/data/` (frozen) ou raiz do projeto (dev); resolvido via `app.paths.db_path()`.
