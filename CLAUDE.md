# CLAUDE.md

## PROJECT
Python automation for workforce measurement (medição) in petrochemical
maintenance. Reads Excel inputs, processes férias/treinamentos/atestados,
applies updates, exports results and inconsistency reports.
Stack: Python, openpyxl, SQLite, PyInstaller. Entry points: `python -m app.main` (CLI), `ui/gui.py` (GUI).

## INVARIANTS

- Inconsistência: registro válido extraído que não pôde ser aplicado na planilha.
- Não são inconsistências: férias sem aprovação; dados fora do critério de aplicação.
- Férias com período totalmente fora do mês de referência são ignoradas silenciosamente (entrada fora do critério — não emitir inconsistência).
- Medição de entrada deve cobrir um único mês de referência; `pipeline._mes_referencia` levanta `PlanilhaInvalidaError` em multi-mês.
- PyInstaller spec: `AutomacaoMedicao.spec` (GUI).
- SSOT estrutural: `PROJECT_STRUCTURE.md` (não manter docs paralelas).

## CONTRACTS

- `Update.desconto_min`: domínio entrega em minutos; writer converte para HH:MM — não pré-converter no domínio.
- `Inconsistencia`: construir exclusivamente via `core.inconsistencia(origem, ...)`.
- `Update` e `Inconsistencia` são dataclasses puras — acesso por atributo; não `.get()` / `[key]` / `in`.
- `gerar_updates_treinamento(dados, tabela_classificacao, observacoes_existentes=None)` → `(list[Update], list[Inconsistencia])` — não alterar assinatura.
- `gerar_updates_ferias(dados, base_cobranca, medicao_por_matricula, md_cobranca_por_chave, sg_funcao_por_chave, mes_referencia, col_map)` → `(list[Update], list[Inconsistencia])` — não alterar assinatura.
- `gerar_updates_atestado(dados)` → `(list[Update], list[Inconsistencia])` — assinatura única; pipeline chama por nome (não `processar_atestados`).
- `pipeline.executar_pipeline(..., conn=None, validar_distribuicao=False)`: DI explícita. `validar_distribuicao=True` exige `conn`; caso contrário levanta `ValueError`.
- `app.application.services.validacao_distribuicao.validar_para_dominio(bd_records, medicao_snapshot) -> list[core.Inconsistencia]` é a única boundary do pipeline; CLI (`app/cli/validar_dist.py`) e GUI (`ui/gui_handlers.py`) usam `app.domain.distribuicao.validar_aderencia_distribuicao` para relatórios — intencional, não consolidar. Formato da mensagem de erro `"<tipo> [<md>] esperado=<f.4> realizado=<f.4> diff=<f.4>"` é contrato congelado (regex coberto em `tests/test_distribuicao_contract_guard.py`).
- Caminho do SQLite é resolvido via `app.paths.db_path()` — não referenciar `Path('data/automacao.db')` diretamente.

## CRITICAL

- Não substituir `salvar_via_zip` por openpyxl write mode — ~4s → ~42s.
- Não reordenar `updates_treinamento + updates_ferias` em `pipeline.executar_pipeline` — quebra `test_ferias_sobrescreve_observacao_de_treinamento_na_mesma_celula`.
- Não alterar formato de desconto de `HH:MM` — testes fixos nesse formato.
- Não alterar passada única em `indexar_e_ler_dados()` — `read_only` não permite acesso aleatório (crash em runtime).
- Não alterar formato de observação de férias sem atualizar `test_ferias_*`.
- Não alterar chave de índice `(matricula, data)` — usada em indexação (`indexar_e_ler_dados`) e aplicação (`aplicar_updates`); mudança quebra ambos.
- Não alterar prefixo `'TREIN. '` em observação de treinamento — `aplicar_updates` usa `'TREIN.' in obs_celula` como marca de idempotência; mudança quebra re-execução.
- Divergência multi-linha (obs/desconto) em `aplicar_updates` é reportada apenas para `tipo='treinamento'` (semântica append); férias/atestado sobrescrevem por contrato — não estender sem rever overwrite.

## SKILLS

Skills em `.claude/skills/`. Claude Code injeta automaticamente as com `paths:` correspondente ao arquivo em edição. As demais devem ser invocadas intencionalmente conforme abaixo.

### brainstorming
**Quando:** ANTES de qualquer implementação não trivial — nova feature, mudança de comportamento, refatoração com impacto em múltiplos módulos.
**Fluxo:** explorar contexto → perguntas (uma por vez) → 2–3 abordagens com trade-offs → design → spec em `docs/specs/YYYY-MM-DD-<topico>.md` → aprovação → implementar.
**Gate:** não escrever código antes de aprovação explícita do design.

### python-patterns
**Quando:** ao escrever ou revisar código Python — aplicar Protocols, dataclasses, context managers, type hints, DI.
**Auto-trigger:** `app/**/*.py`, `ui/**/*.py`, `tests/**/*.py`.
**Restrições do projeto:** ver CONTRACTS e CRITICAL acima — patterns genéricos cedem às regras do projeto.

### python-testing
**Quando:** ao escrever testes novos, revisar cobertura, ou configurar infraestrutura de testes.
**Auto-trigger:** `tests/**/*.py`.
**Projeto:** fakes para ports; SQLite `:memory:` para infra; `test_layer_boundaries.py` é o enforcement de arquitetura — não quebrar.

### react
**Quando:** ao trabalhar em `ui/**/*.tsx` ou quando a migração de GUI para React iniciar.
**Auto-trigger:** `ui/**/*.tsx`, `ui/**/*.ts`, `ui/**/*.jsx`.
**Status:** stack a definir. Skill cobre padrões genéricos React/TypeScript. Atualizar com especificidades (componentes, roteamento, estado global) quando stack for escolhida.

## ARCHITECTURE

Flow: entrada/ → loaders → application/pipeline → [ferias|treinamento|atestado|distribuicao] → aplicar_updates → saida/

**Target layer split** (migrado por módulo, ver `PROJECT_STRUCTURE.md` para estado atual):

- `app/domain/` — funções puras + dataclasses. Imports permitidos: stdlib, `app.domain.*`. Imports proibidos: `sqlite3`, `openpyxl`, `app.application.*`, `app.infrastructure.*`. Arquivos nomeados por **negócio** (treinamento, ferias, atestado, core, errors), nunca por camada.
- `app/application/` — orquestração + ports. `pipeline.py` (orquestração geral, multi-domínio), `services/` (use-cases por módulo de negócio), `ports.py` (Protocols). Regra estrita aplicada apenas a `app/application/services/`: imports permitidos = stdlib + `app.domain.*` + `typing.Protocol`; proibidos = `app.infrastructure.*`, `sqlite3`, `openpyxl`. **Exceção intencional:** `pipeline.py` é o ponto de composição multi-domínio e pode importar `app.infrastructure.*` para construir adapters e injetá-los em services. Aplicar a regra estrita a ele exigiria um port por dependência (ferias, atestado, excel, db), violando o cap "um port por refactor". Justificativa: `tests/test_layer_boundaries.py`.
- `app/infrastructure/` — adapters de I/O. `loaders.py`, `excel.py`, `db.py`, `paths.py`, `logging_config.py`, `adapters/*.py`. Única camada que toca `sqlite3` / `openpyxl` / filesystem.
- `app/main.py`, `app/cli/`, `ui/` — composition root. Único lugar onde adapters são instanciados e injetados em services.

**Rules:**
- Domain modules do not import from each other.
- loaders.py does not contain business logic.
- pipeline.py does not contain business logic; não abre conexões de DB nem executa bootstrap.
- excel.py does not import domain modules.
- Ports vivem em `app/application/ports.py`. Cada port tem nome de negócio (ex.: `TabelaClassificacao`), não nome técnico (`Repository`). Cada port só é introduzido quando há um consumidor concreto **e** um fake em testes que substitui um recurso difícil de testar (DB, Excel I/O). Cap: um port por refactor.
- Adapters vivem em `app/infrastructure/adapters/` e implementam ports por composição estrutural (Protocol), sem herança.
- Forbidden: factories-by-string, dynamic dispatch (`getattr(module, name)()`), service locators, runtime DI containers. Composition root constrói adapters explicitamente.
- Bootstrap de SQLite (`db.popular_bd_se_vazio`) é responsabilidade da composition root (`app/main.py`, `ui/gui.py`), executado ANTES de criar threads worker. Worker thread NUNCA chama `popular_*`.
- Writes em SQLite (`registrar_bd`, `registrar_medicao`) são serializados via `threading.Lock` na GUI app singleton. Worker threads adquirem o lock antes de abrir conexão de escrita.
- Worker thread NUNCA reusa a conexão da composition root (`check_same_thread` violation). Cada worker abre/fecha a sua própria conexão dentro do escopo da tarefa.
- Scripts CLI vivem em `app/cli/` (normalizar, validar_dist, validar_hr, validar_consist); `app/main.py` é o único entry-point. Não criar `.py` soltos na raiz.
- Distribuição contratual é persistida em SQLite (carga única a partir do xlsx empacotado via PyInstaller `datas=`); demais entradas permanecem efêmeras via `loaders.py`.
- Logging de arquivo é setup pela composition root via `logging_config.setup_logging()`; rotating handler em `logs/automacao.log`. Idempotente.

**Migration window:** legacy paths (`app/treinamento.py`, `app/core.py`, `app/loaders.py`, `app/excel.py`, `app/db.py`, `app/paths.py`, `app/errors.py`, `app/logging_config.py`, `app/pipeline.py`) coexistem com a estrutura-alvo até cada um ser movido. Durante a janela de migração:
- Imports legados continuam válidos.
- Novos imports devem usar o caminho-alvo (`app.domain.treinamento`, etc.) quando o arquivo já estiver migrado; senão, o caminho atual.
- `tests/test_layer_boundaries.py` (Step 6) é o enforcement: módulos já em `app/domain/` não podem importar `sqlite3` / `openpyxl`; módulos em `app/application/` não podem importar `app.infrastructure.*`.
- Atestado já migrado para `app/domain/atestado.py`; legacy `app/atestado.py` removido.
- Férias já migrado para `app/domain/ferias.py`; legacy `app/ferias.py` removido.
- Validador de distribuição já migrado: `app/domain/distribuicao.py` (`validar_aderencia_distribuicao`, `gerar_relatorio`, `InconsistenciaDistribuicao`), `app/application/services/validacao_distribuicao.py` (`validar_para_dominio`), `app/infrastructure/adapters/relatorio_distribuicao.py` (`salvar_relatorio`); legacy `app/validar_distribuicao.py` removido. `app/distribuicao_contratual.py` permanece flat (fora de escopo).
