---
paths:
  - "app/**/*.py"
  - "tests/**/*.py"
  - "scripts/**/*.py"
---

## Quality Gate — workflow de revisão automática

Comando: `python -m scripts.quality_gate` (ou `make quality-gate`).
Baseline: `quality_baseline.json` na raiz, versionado no git.
Atualização do baseline (`--update-baseline`) é manual — nunca rodar no
meio de um step.

### Quando rodar
Ao concluir cada step de TODO ou bloco de implementação que modifique
`app/`, `tests/` ou `scripts/`.

### Quando pular (diff trivial)
- Diff líquido ≤ 3 linhas adicionadas/removidas no total.
- OU diff afeta apenas 1 arquivo com ≤ 5 linhas alteradas.
- Edição apenas de docs (`*.md`), `Makefile` ou `quality_baseline.json`.

### Limiares de regressão
| métrica         | falha quando                     |
|-----------------|----------------------------------|
| violations      | qualquer aumento sobre baseline  |
| oversized_files | qualquer aumento sobre baseline  |
| lines           | aumento > +10% sobre baseline    |
| functions       | aumento > +10% sobre baseline    |

(O CLI default é +5% para lines/functions; o gate de step usa +10%
para tolerar refactors que adicionam testes. Para gate de step,
chamar com tolerâncias customizadas se necessário.)

### Procedimento em caso de falha
1. Revisar o código produzido no step.
2. Aplicar uma das ações: extrair função, deduplicar, dividir arquivo
   oversized, remover código morto, simplificar.
3. Rodar o gate novamente.
4. Repetir até passar **OU** até atingir 3 tentativas.
5. Após 3 falhas: parar, reportar ao usuário a tabela de deltas e pedir
   decisão (aceitar como está, reverter o step, ou alongar o teto).

### Não-objetivos
- Não tentar consertar violations preexistentes (apenas as introduzidas
  no diff atual).
- Não rodar em alterações fora de `app/`, `tests/`, `scripts/`.
- Não atualizar baseline automaticamente para "fazer o gate passar".