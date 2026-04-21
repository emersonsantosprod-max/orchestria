#!/usr/bin/env python3
"""
app.cli.validar_hr — Valida horas trabalhadas (col 19) na Medição.
"""

import argparse
import sys
from pathlib import Path

from app.loaders import carregar_medicao_hr
from app.validar_horas import _salvar_relatorio, gerar_relatorio, validar_horas_trabalhadas

DEFAULT_MEDICAO = 'data/entrada/medicao_base.xlsx'


def cmd_validar(path: Path) -> int:
    if not path.exists():
        print(f"[ERRO] Arquivo não encontrado: {path}", file=sys.stderr)
        return 1

    registros, n_linhas = carregar_medicao_hr(str(path))
    inconsistencias = validar_horas_trabalhadas(registros)

    conteudo = gerar_relatorio(inconsistencias, str(path.resolve()), n_linhas)
    caminho = _salvar_relatorio(conteudo)
    print(f"Relatório gravado em: {caminho}")
    print(f"Total de inconsistências: {len(inconsistencias)}")
    return 1 if inconsistencias else 0


def build_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        '--medicao',
        default=DEFAULT_MEDICAO,
        metavar='CAMINHO',
        help=f'Planilha de medição (default: {DEFAULT_MEDICAO})',
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser(argparse.ArgumentParser(
        description='Valida horas trabalhadas (Hr Trabalhadas, col 19) na Medição.',
    ))
    args = parser.parse_args(argv)
    return cmd_validar(Path(args.medicao))


if __name__ == '__main__':
    sys.exit(main())
