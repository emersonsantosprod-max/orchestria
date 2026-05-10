## TAG resolution & domain-wide normalization

### Update.tag — mecanismo único

- `Update.tag: str | None` é o canal único para preencher a coluna TAG
  da Medição. Writer (`app/infrastructure/excel.py`) é genérico: só
  toca a coluna TAG quando `upd.tag is not None`. **Sem branching por
  `tipo`** no writer.
- Atestado seta literal `'ATESTADO'` em `gerar_updates_atestado`.
- Férias resolve via `ctx.base_tags_por_chave.get(normalizar_chave(...))`
  em `gerar_updates_ferias`.

### Base de Tags — feature ativa/inativa por dados

- Mapa `base_tags_por_chave: dict[tuple, str]` indexado por chave
  normalizada `(sg_funcao, unidade, md_cobranca, situacao)`.
- **Mapa vazio = feature inativa**: `Update.tag` fica `None` e nenhuma
  inconsistência de tag é emitida. Preserva fluxo legado enquanto a
  Base de Tags ainda não foi cadastrada na sessão.

### Inconsistência dedupedada por chave normalizada

- Lookup falho em `base_tags` para férias gera **uma única**
  inconsistência por chave normalizada distinta — agrega `matriculas`
  (lista) e `count` no campo `erro`.
- Dedupe acontece no domínio (`gerar_updates_ferias`). Writer nunca
  vê esses casos.

### Normalização canônica

- `app.domain.normalizacao.normalizar(s)` aplica NFKD + accent-fold +
  whitespace-collapse + UPPER. Coerção de `None` → `''`.
- `app.domain.normalizacao.normalizar_chave(*parts) -> tuple[str, ...]`
  é canônico para chaves de lookup **domain-wide**. Usado hoje em
  `base_tags`; bases futuras devem seguir o mesmo padrão.

### CONTRATO de assinatura

```python
gerar_updates_ferias(dados_ferias, ctx: FeriasContext)
    -> (list[Update], list[Inconsistencia])

gerar_updates_atestado(dados)
    -> (list[Update], list[Inconsistencia])
    # cada Update sai com tag='ATESTADO' explícito.
```

`FeriasContext` (frozen dataclass em `app/domain/ferias.py`) reúne
base_cobranca, medicao_por_matricula, md_cobranca/sg_funcao/unidade
por chave, base_tags_por_chave, mes_referencia, col_map. Pipeline é
o composition root que monta o ctx.

### Anti-patterns

- ❌ Branch no writer por `upd.tipo == 'atestado'` para escrever
  `'ATESTADO'`. **Mover para o domínio**: `Update.tag` carrega a
  intenção.
- ❌ Emitir N inconsistências para a mesma chave normalizada.
  Agrupar em uma única com `count` + lista de matrículas.
- ❌ Comparar strings de chave sem passar por `normalizar_chave`.
  Drift de acentos / case / espaço quebra lookup silenciosamente.
