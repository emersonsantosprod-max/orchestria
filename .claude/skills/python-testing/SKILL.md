---
name: python-testing
description: Python testing strategies using pytest, TDD methodology, fixtures, mocking, parametrization, and coverage requirements.
---

# Python Testing — codebase-specific

Padrões reais do projeto Automação Medição. Para regras normativas
(sempre carregadas), ver `.claude/rules/testing.md`. Este skill cobre
como-fazer; o rule cobre o-que-respeitar.

## Quando ativar

- Escrever um novo teste para `app/`.
- Refatorar fixtures ou helpers em `tests/`.
- Migrar testes legados para nova assinatura de contrato.
- Adicionar fakes para Protocol ports.

## TDD ciclo

Red → Green → Refactor. Pequenos passos:
1. Escrever teste falhando que captura o requisito.
2. Mínimo código de domínio que passa.
3. Refatorar mantendo verde.

Sem gate de coverage % no projeto. Foco: cobrir caminhos de domínio e
contratos públicos.

## Estrutura

```
tests/
├── conftest.py             # fixture global: isolated_paths
├── fixtures/               # builders por domínio
│   ├── ferias_factories.py # build_dado_ferias_*, build_ferias_context, …
│   └── …
├── api/                    # rotas FastAPI
├── application/            # services (com fakes de ports)
├── infrastructure/         # adapters (:memory: SQLite)
└── test_*.py               # testes por domínio em raiz
```

## Fixture `isolated_paths`

Definida em `tests/conftest.py`. Monkeypatcha `app.infrastructure.paths`:
`db_path`, `exports_dir`, `logs_dir` → todos sob `tmp_path`. Use sempre
que o teste tocar filesystem ou DB.

**Caveat de binding local**: módulos que importam via
`from app.infrastructure.paths import db_path` criam binding no consumer.
Patchear `paths.db_path` em `conftest` **não** atualiza o consumer.
Solução: patchear o símbolo do consumer no próprio teste:
```python
monkeypatch.setattr('app.infrastructure.data.bootstrap.db_path', ...)
```

## Builders em `tests/fixtures/`

Padrão: `build_<dominio>_<entidade>(**overrides) -> obj`. Defaults
sensatos; overrides para o que o teste varia. Exemplo crítico:
`build_ferias_context(**overrides) -> FeriasContext` em
`ferias_factories.py` — aceita os 8 campos do `FeriasContext`, com
defaults vazios ou `mes_referencia_padrao()` / `build_col_map()`.

**Não** centralizar fakes em um único módulo `tests/fakes.py`. Fakes
ad-hoc por teste OU classe Protocol-implementing inline.

## Fakes via Protocol

Quando o domínio consome um Port (Protocol em `app/application/ports.py`),
o teste injeta um fake — não `unittest.mock.Mock()`. Razão: tipo-checking
estático funciona; comportamento é explícito.

```python
class FakeTabelaClassificacao:
    def __init__(self, mapa):
        self._mapa = mapa
    def classificar(self, codigo: str) -> str | None:
        return self._mapa.get(codigo)

def test_lancar_treinamentos_classifica():
    fake = FakeTabelaClassificacao({'X-100': 'NR-35'})
    service = LancarTreinamentosService(tabela=fake)
    ...
```

Para Repositories, ver `.claude/skills/repository-pattern/SKILL.md`.

## SQLite em testes

- **Infrastructure tests** (`tests/infrastructure/`): use
  `sqlite3.connect(':memory:')` + `create_schema(conn)` no setup.
  Nunca DB file.
- **Domain tests**: zero SQLite. Use fakes / inline dicts.
- **Application tests**: depende — services podem receber `conn` ou
  fakes de Repository, conforme o port.

```python
from app.infrastructure.data.schema import create_schema

def test_base_tags_lookup():
    conn = sqlite3.connect(':memory:')
    create_schema(conn)
    BaseTagsRepository(conn).salvar([...])
    assert BaseTagsRepository(conn).todos() == {...}
```

## Parametrize

Use `@pytest.mark.parametrize` para variar dimensões de input. IDs
explícitos quando os parâmetros não têm `repr` legível:

```python
@pytest.mark.parametrize("periodo", [
    "01/04/2026",
    "01-04-2026 a 03-04-2026",
    "03/04/2026 a 01/04/2026",
], ids=["sem-a", "formato-errado", "invertido"])
def test_periodo_invalido(periodo):
    ...
```

## Estilo

- **Funções, não classes**. Sem `class TestX`. O projeto não usa.
- **arrange / act / assert** curto. Sem aninhamento profundo.
- **Sem prints** ou comentários "what". Nome do teste descreve a intenção.
- **Sem mocks excessivos**. Fakes diretos > Mock() com side_effect.

## Comandos

```bash
make test                          # toda suite
make lint                          # ruff
make quality-gate                  # gate de regressão
pytest tests/test_<X>.py -v        # arquivo isolado
pytest tests/test_<X>.py::<name>   # teste único
pytest -k "ferias and lookup"      # busca por substring
```

## Enforcement automático

`tests/test_layer_boundaries.py` garante que:
- `app/domain/` não importa `sqlite3` / `openpyxl` / camadas superiores.
- `app/application/services/` não importa `app.infrastructure.*`.
- Quebrar isso = teste falha. Não bypassar.

## Frozen contracts

Mensagens de erro com formato fixo (ex.: distribuição contratual) são
cobertas por regex em `tests/test_*_contract_guard.py`. **Não alterar**
o formato sem atualizar o regex.

## Anti-patterns

- ❌ `class TestX`: o projeto usa funções top-level.
- ❌ `unittest.mock.Mock()` para Ports: usa fake Protocol-impl.
- ❌ `tmp_path` direto sem `isolated_paths`: deixa o módulo lookup
  apontar para `data/` real.
- ❌ DB file em `tests/`: sempre `:memory:`.
- ❌ Coverage gate (`--cov=app`): não usado no projeto.
- ❌ Centralizar fakes em `tests/fakes.py`: prefere fakes per-test ou
  builders em `tests/fixtures/<dominio>_factories.py`.
