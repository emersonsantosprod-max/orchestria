# CLAUDE.md

## INVARIANTS

- Inconsistência: registro válido extraído que não pôde ser aplicado na planilha.
- Não são inconsistências: férias sem aprovação; dados fora do critério de aplicação.
- PyInstaller specs: `automacao.spec` (CLI), `AutomacaoMedicao.spec` (GUI).

## CONTRACTS

- `Update.desconto_min`: domínio entrega em minutos; writer converte para HH:MM — não pré-converter no domínio.
- `Inconsistencia`: construir exclusivamente via `core.inconsistencia(origem, ...)`.
- `processar_treinamentos(dados, tabela, obs_existentes)` → `(list[Update], list[Inconsistencia])` — não alterar assinatura.
- `processar_ferias(dados, base_cobranca, medicao_por_matricula, md_cobranca_por_chave, sg_funcao_por_chave, mes_ref, col_map)` → `(list[Update], list[Inconsistencia])` — não alterar assinatura.

## RULES

- Carregar workbooks com `openpyxl.load_workbook(read_only=True, data_only=True)`.
- `indexar_e_ler_dados()`: passada única `iter_rows(values_only=True)` — não usar acesso aleatório.
- `base_treinamentos.xlsx`: col 0 = nome UPPER, col 1 = tipo — sem mapeamento dinâmico; sem fallback.
- Carga multi-dia: replicar integralmente por dia — não dividir carga entre os dias.
- Observação: aplicar `core.deduplicar_observacao` antes de concatenar — não concatenar diretamente.
- Relatório de inconsistências: exportar todas, sem truncamento.

## CRITICAL

- Não substituir `salvar_via_zip` por openpyxl write mode — ~4s → ~42s.
- Não reordenar `updates_treinamento + updates_ferias` em `pipeline.processar` — quebra `test_ferias_sobrescreve_observacao_de_treinamento_na_mesma_celula`.
- Não alterar formato de desconto de `HH:MM` — testes fixos nesse formato.
- Não alterar passada única em `indexar_e_ler_dados()` — `read_only` não permite acesso aleatório (crash em runtime).
- Não alterar formato de observação de férias sem atualizar `test_ferias_*`.
- Não alterar chave de índice `(matricula, data)` — usada em indexação (`indexar_e_ler_dados`) e aplicação (`aplicar_updates`); mudança quebra ambos.
