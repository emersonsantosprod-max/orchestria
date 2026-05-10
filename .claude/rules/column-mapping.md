## Column mapping — Medição header resolution

### Single source of truth

- `app.domain.column_aliases.COLUMN_ALIASES` é a **fonte única** de
  aliases de colunas da Medição. Layer `domain` (sem imports de
  infra/openpyxl).
- `app.domain.column_aliases.OBRIGATORIAS` enumera as colunas que
  precisam estar presentes para qualquer pipeline rodar.

### Quem consome

- `app.infrastructure.excel.mapear_colunas(ws_header_row)` é o único
  caller. Recebe a linha de cabeçalho do worksheet e retorna
  `dict[chave_lógica, índice_zero_based]` + `_header_row`.

### Match logic

- Cada célula do header é normalizada via `app.domain.normalizacao.normalizar`
  (NFKD + accent-fold + UPPER + whitespace-collapse).
- Para cada chave em `COLUMN_ALIASES`, percorre `aliases` na ordem
  declarada — **primeiro match vence**. Por isso, aliases são ordenados
  por especificidade (mais específico primeiro).
- Chaves sem match na header ficam ausentes do mapa. `OBRIGATORIAS`
  ausentes → `mapear_colunas` levanta `RuntimeError` no pré-flight
  do domínio (não no infra).

### Chaves canônicas suportadas

`data`, `matricula`, `desconto`, `observacao`, `situacao`, `md_cobranca`,
`sg_funcao`, `unidade`, `tag`, `pct_cobranca`. Adicionar nova chave
implica:
1. Entrada em `COLUMN_ALIASES`.
2. Decidir se entra em `OBRIGATORIAS`.
3. Atualizar callers do domínio que dependem dela.

### Anti-patterns

- ❌ Hardcode de header literal (`if cell.value == 'Sg Função'`).
  Drift de Excel (acentos, espaço, caso) quebra. Sempre via
  `COLUMN_ALIASES` + `normalizar`.
- ❌ Manter aliases fora de `domain/column_aliases.py` (em loaders,
  em pipeline, em testes). Single source.
- ❌ Adicionar alias na infra. Aliases são vocabulário de domínio.
