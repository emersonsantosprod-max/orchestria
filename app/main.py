"""
main.py — Entry point CLI. Wrapper fino sobre app.pipeline.executar_pipeline.

Toda a orquestração (loaders + pipeline 3 fases) vive em app/pipeline.py.
Este módulo só resolve caminhos default, interpreta flags opt-in e formata
saída terminal.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db
from app import pipeline as service

salvar_relatorio_inconsistencias = service.salvar_relatorio_inconsistencias


def definir_caminhos():
    base_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    entrada   = os.path.join(base_dir, 'data', 'entrada')
    saida     = os.path.join(base_dir, 'data', 'saida')
    return (
        os.path.join(entrada, 'medicao_base.xlsx'),
        os.path.join(entrada, 'treinamentos.xlsx'),
        os.path.join(saida,   'medicao_processada.xlsx'),
        os.path.join(entrada, 'ferias.xlsx'),
        os.path.join(entrada, 'base_cobranca.xlsx'),
    )


def executar_medicao(
    c_medicao_custom=None,
    c_trein_custom=None,
    c_ferias_custom=None,
    c_base_cob_custom=None,
):
    """Resolve caminhos default e delega para pipeline.executar_pipeline (entrada da GUI/tests)."""
    (c_med_pad, c_trein_pad, c_saida_pad,
     c_ferias_pad, c_base_cob_pad) = definir_caminhos()

    c_medicao = c_medicao_custom or c_med_pad

    ferias_ativo = bool(c_ferias_custom and c_base_cob_custom)
    treinamento_ativo = (
        bool(c_trein_custom)
        or (not ferias_ativo and not c_medicao_custom)
    )

    c_treinamentos = c_trein_custom if treinamento_ativo and c_trein_custom else ''
    c_ferias_in    = c_ferias_custom   if ferias_ativo else ''
    c_base_cob_in  = c_base_cob_custom if ferias_ativo else ''

    if treinamento_ativo and not c_trein_custom:
        c_treinamentos = c_trein_pad

    qualquer_custom = any([
        c_medicao_custom, c_trein_custom,
        c_ferias_custom, c_base_cob_custom,
    ])
    c_saida = '' if qualquer_custom else c_saida_pad

    conn = db.conectar()
    try:
        db.popular_bd_se_vazio(conn)
        db.popular_treinamentos_se_vazio(conn)
        resultado = service.executar_pipeline(
            caminho_medicao=c_medicao,
            caminho_treinamentos=c_treinamentos,
            caminho_ferias=c_ferias_in,
            caminho_base_cobranca=c_base_cob_in,
            caminho_saida=c_saida,
            conn=conn,
            validar_distribuicao=True,
        )
    finally:
        conn.close()
    return resultado


def exibir_resumo(resultado):
    print('\nProcessamento concluído\n')
    print(f"Registros processados: {resultado.processados}")
    print(f"Atualizações aplicadas: {resultado.atualizados}")
    inc = resultado.inconsistencias
    print(f"Inconsistências: {len(inc)}\n")
    if inc:
        print('--- Inconsistências ---')
        for i in inc:
            print(
                f"  [Linha {i.linha or '-'}] "
                f"RE:{i.matricula or '-'} | "
                f"Data:{i.data or '-'} | "
                f"{i.erro or '?'}"
            )


def _comando_executar_medicao() -> int:
    print('Iniciando Automação de Treinamentos...\n')
    try:
        resultado = executar_medicao()
        exibir_resumo(resultado)
        return 0
    except RuntimeError as e:
        print(f'\n[FALHA] {e}')
        return 1
    except Exception as e:
        print(f'\n[ERRO INESPERADO] {e}')
        return 1


def main():
    import argparse
    parser = argparse.ArgumentParser(prog='automacao')
    sub = parser.add_subparsers(dest='cmd')
    sub.add_parser('executar', help='Pipeline completo (default)')
    sub.add_parser('normalizar', help='Normaliza distribuição contratual')
    p_vd = sub.add_parser('validar-dist', help='Valida BD vs Medição')
    from app.cli.validar_dist import build_parser as _build_vd
    _build_vd(p_vd)
    sub.add_parser('validar-consist', help='Compara medição original vs processada')
    p_vh = sub.add_parser('validar-hr', help='Valida horas trabalhadas na Medição')
    from app.cli.validar_hr import build_parser as _build_vh
    _build_vh(p_vh)

    args = parser.parse_args()
    cmd = args.cmd or 'executar'
    if cmd == 'executar':
        sys.exit(_comando_executar_medicao())
    if cmd == 'normalizar':
        from app.cli.normalizar import main as _m
        sys.exit(_m())
    if cmd == 'validar-dist':
        from app.cli.validar_dist import main as _m
        sys.exit(_m([
            *(['--registrar-bd', args.registrar_bd] if args.registrar_bd else []),
            *(['--registrar-medicao', args.registrar_medicao] if args.registrar_medicao else []),
            *(['--db', args.db] if args.db else []),
        ]))
    if cmd == 'validar-consist':
        from app.cli.validar_consist import main as _m
        _m()
        sys.exit(0)
    if cmd == 'validar-hr':
        from app.cli.validar_hr import main as _m
        sys.exit(_m(
            ['--medicao', args.medicao] if args.medicao else []
        ))


if __name__ == '__main__':
    main()
