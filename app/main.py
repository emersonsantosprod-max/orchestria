"""
main.py — Entry point CLI. Wrapper fino sobre app.service.processar.

Toda a orquestração (loaders + pipeline 3 fases) vive em app/pipeline.py.
Este módulo só resolve caminhos default, interpreta flags opt-in e formata
saída terminal.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import pipeline as service

# Re-exports mantidos para consumidores existentes (GUI, testes).
salvar_relatorio_inconsistencias = service.salvar_relatorio_inconsistencias


# ---------------------------------------------------------------------------
# Caminhos default
# ---------------------------------------------------------------------------

def definir_caminhos():
    base_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    entrada   = os.path.join(base_dir, 'data', 'entrada')
    saida     = os.path.join(base_dir, 'data', 'saida')
    return (
        os.path.join(entrada, 'medicao_base.xlsx'),
        os.path.join(entrada, 'treinamentos.xlsx'),
        os.path.join(entrada, 'base_treinamentos.xlsx'),
        os.path.join(saida,   'medicao_processada.xlsx'),
        os.path.join(entrada, 'ferias.xlsx'),
        os.path.join(entrada, 'base_cobranca.xlsx'),
    )


# ---------------------------------------------------------------------------
# Entry point (mantém assinatura legada para GUI + testes)
# ---------------------------------------------------------------------------

def run(
    c_medicao_custom=None,
    c_trein_custom=None,
    c_class_custom=None,
    c_ferias_custom=None,
    c_base_cob_custom=None,
):
    """
    Wrapper legado: resolve caminhos default e delega a service.processar.

    Opt-in:
      - Treinamento: ativo se c_trein_custom + c_class_custom ou, na ausência
        de qualquer custom (CLI default), mantém comportamento tradicional.
      - Férias: ativo se c_ferias_custom + c_base_cob_custom forem fornecidos.
    """
    (c_med_pad, c_trein_pad, c_class_pad, c_saida_pad,
     c_ferias_pad, c_base_cob_pad) = definir_caminhos()

    c_medicao = c_medicao_custom or c_med_pad

    ferias_ativo = bool(c_ferias_custom and c_base_cob_custom)
    treinamento_ativo = (
        bool(c_trein_custom and c_class_custom)
        or (not ferias_ativo and not c_medicao_custom)
    )

    c_treinamentos  = c_trein_custom    if treinamento_ativo else ''
    c_classificacao = c_class_custom    if treinamento_ativo else ''
    c_ferias_in     = c_ferias_custom   if ferias_ativo      else ''
    c_base_cob_in   = c_base_cob_custom if ferias_ativo      else ''

    if treinamento_ativo and not (c_trein_custom and c_class_custom):
        c_treinamentos  = c_trein_pad
        c_classificacao = c_class_pad

    qualquer_custom = any([
        c_medicao_custom, c_trein_custom, c_class_custom,
        c_ferias_custom, c_base_cob_custom,
    ])
    c_saida = '' if qualquer_custom else c_saida_pad

    resultado = service.processar(
        caminho_medicao=c_medicao,
        caminho_treinamentos=c_treinamentos,
        caminho_classificacao=c_classificacao,
        caminho_ferias=c_ferias_in,
        caminho_base_cobranca=c_base_cob_in,
        caminho_saida=c_saida,
    )

    # Retorno dict-like (preserva compat com GUI atual, que usa .get()).
    return resultado


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def exibir_resumo(resultado):
    print('\nProcessamento concluído\n')
    print(f"Registros processados: {resultado.get('processados', 0)}")
    print(f"Atualizações aplicadas: {resultado.get('atualizados', 0)}")
    inc = resultado.get('inconsistencias', [])
    print(f"Inconsistências: {len(inc)}\n")
    if inc:
        print('--- Inconsistências ---')
        for i in inc:
            print(
                f"  [Linha {i.get('linha','-')}] "
                f"RE:{i.get('matricula','-')} | "
                f"Data:{i.get('data','-')} | "
                f"{i.get('erro','?')}"
            )


def main():
    print('Iniciando Automação de Treinamentos...\n')
    try:
        resultado = run()
        exibir_resumo(resultado)
    except RuntimeError as e:
        print(f'\n[FALHA] {e}')
    except Exception as e:
        print(f'\n[ERRO INESPERADO] {e}')


if __name__ == '__main__':
    main()
