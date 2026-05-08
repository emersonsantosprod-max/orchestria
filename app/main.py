"""
main.py — Entry point CLI. Dispatcher fino para subcomandos especializados.

Cada subcomando vive em app/cli/* com seu próprio parser e resolução de
paths via flags. A GUI usa app/api/main.py (FastAPI) e não passa por aqui.

ARCHITECTURAL RULE (enforced by tests/test_layer_boundaries.py):
  - main.py NUNCA importa app.domain.*
  - Composition root: instancia adapters e injeta nos serviços. Sem
    paths fixos de entrada/saída — o usuário sempre fornece via flags
    de subcomando ou via upload na GUI.
"""

import argparse
import sys

from app.infrastructure.logging_config import setup_logging


def main():
    setup_logging()
    parser = argparse.ArgumentParser(prog='automacao')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('normalizar', help='Normaliza distribuição contratual')

    p_vd = sub.add_parser('validar-dist', help='Valida BD vs Medição')
    from app.cli.validar_dist import build_parser as _build_vd
    _build_vd(p_vd)

    sub.add_parser('validar-consist', help='Compara medição original vs processada')

    p_vh = sub.add_parser('validar-hr', help='Valida horas trabalhadas na Medição')
    from app.cli.validar_hr import build_parser as _build_vh
    _build_vh(p_vh)

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help()
        sys.exit(0)
    if args.cmd == 'normalizar':
        from app.cli.normalizar import main as _m
        sys.exit(_m())
    if args.cmd == 'validar-dist':
        from app.cli.validar_dist import main as _m
        sys.exit(_m([
            *(['--registrar-bd', args.registrar_bd] if args.registrar_bd else []),
            *(['--registrar-medicao', args.registrar_medicao] if args.registrar_medicao else []),
            *(['--db', args.db] if args.db else []),
        ]))
    if args.cmd == 'validar-consist':
        from app.cli.validar_consist import main as _m
        _m()
        sys.exit(0)
    if args.cmd == 'validar-hr':
        from app.cli.validar_hr import main as _m
        sys.exit(_m(
            ['--medicao', args.medicao] if args.medicao else []
        ))


if __name__ == '__main__':
    main()
