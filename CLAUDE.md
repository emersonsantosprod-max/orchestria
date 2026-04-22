# CLAUDE.md

## PROJECT
Python automation for workforce measurement (medição) in petrochemical
maintenance. Reads Excel inputs, processes férias/treinamentos/atestados,
applies updates, exports results and inconsistency reports.
Stack: Python, openpyxl, SQLite, PyInstaller. Entry points: `python -m app.main` (CLI), `ui/gui.py` (GUI).

## INVARIANTS

- Inconsistência: registro válido extraído que não pôde ser aplicado na planilha.
- Não são inconsistências: férias sem aprovação; dados fora do critério de aplicação.
- PyInstaller spec: `AutomacaoMedicao.spec` (GUI).
- SSOT estrutural: `PROJECT_STRUCTURE.md` (não manter docs paralelas).

## CONTRACTS

- `Update.desconto_min`: domínio entrega em minutos; writer converte para HH:MM — não pré-converter no domínio.
- `Inconsistencia`: construir exclusivamente via `core.inconsistencia(origem, ...)`.
- `Update` e `Inconsistencia` são dataclasses puras — acesso por atributo; não `.get()` / `[key]` / `in`.
- `gerar_updates_treinamento(dados, tabela, obs_existentes)` → `(list[Update], list[Inconsistencia])` — não alterar assinatura.
- `gerar_updates_ferias(dados, base_cobranca, medicao_por_matricula, md_cobranca_por_chave, sg_funcao_por_chave, mes_ref, col_map)` → `(list[Update], list[Inconsistencia])` — não alterar assinatura.
- `pipeline.executar_pipeline(..., conn=None, validar_distribuicao=False)`: DI explícita. `validar_distribuicao=True` exige `conn`; caso contrário levanta `ValueError`.
- Caminho do SQLite é resolvido via `app.paths.db_path()` — não referenciar `Path('data/automacao.db')` diretamente.

## CRITICAL

- Não substituir `salvar_via_zip` por openpyxl write mode — ~4s → ~42s.
- Não reordenar `updates_treinamento + updates_ferias` em `pipeline.executar_pipeline` — quebra `test_ferias_sobrescreve_observacao_de_treinamento_na_mesma_celula`.
- Não alterar formato de desconto de `HH:MM` — testes fixos nesse formato.
- Não alterar passada única em `indexar_e_ler_dados()` — `read_only` não permite acesso aleatório (crash em runtime).
- Não alterar formato de observação de férias sem atualizar `test_ferias_*`.
- Não alterar chave de índice `(matricula, data)` — usada em indexação (`indexar_e_ler_dados`) e aplicação (`aplicar_updates`); mudança quebra ambos.

## ARCHITECTURE
Flow: entrada/ → loaders.py → pipeline.py → [ferias|treinamento|atestado|distribuicao] → aplicar_updates → saida/
Layers: loaders (I/O only) → domain modules (logic only) → pipeline (orchestration only) → excel.py (write only)
Rules:
- Domain modules do not import from each other
- loaders.py does not contain business logic
- pipeline.py does not contain business logic; não abre conexões de DB nem executa bootstrap
- excel.py does not import domain modules
- Bootstrap de SQLite (`db.popular_bd_se_vazio`) é responsabilidade da application boundary (`app/main.py`, `ui/gui.py`), executado ANTES de chamar `pipeline.executar_pipeline()`
- Scripts CLI vivem em `app/cli/` (normalizar, validar_dist, validar_consist); `app/main.py` é o único entry-point, com subcomandos argparse. Não criar `.py` soltos na raiz.
- Distribuição contratual é persistida em SQLite (carga única a partir do xlsx empacotado via PyInstaller `datas=`); demais entradas permanecem efêmeras via `loaders.py`.
