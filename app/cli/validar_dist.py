#!/usr/bin/env python3
"""
app.cli.validar_dist — Valida distribuição contratual (BD) contra Medição.
"""

import argparse
import sys
from pathlib import Path

from app.infrastructure.db import (
    conectar,
    obter_bd,
    obter_medicao,
    obter_registro_arquivos,
    popular_bd_se_vazio,
    registrar_bd,
    registrar_medicao,
)
from app.domain.distribuicao import gerar_relatorio, validar_aderencia_distribuicao
from app.infrastructure.adapters.relatorio_distribuicao import salvar_relatorio
from app.infrastructure.paths import db_path


def cmd_registrar_bd(path_str: str, conn) -> int:
    path = Path(path_str)
    if not path.exists():
        print(f"[ERRO] Arquivo não encontrado: {path}", file=sys.stderr)
        return 1
    print(f"Registrando BD: {path} …")
    registrar_bd(path, conn)
    print('BD registrado com sucesso.')
    return 0

def cmd_registrar_medicao(path_str: str, conn) -> int:
    path = Path(path_str)
    if not path.exists():
        print(f"[ERRO] Arquivo não encontrado: {path}", file=sys.stderr)
        return 1
    print(f"Registrando Medição: {path} …")
    avisos = registrar_medicao(path, conn)
    for av in avisos:
        print(f"  [AVISO] {av}")
    print('Medição registrada com sucesso.')
    return 0


def cmd_validar(conn) -> int:
    popular_bd_se_vazio(conn)
    registros = obter_registro_arquivos(conn)
    if 'bd' not in registros:
        print('[ERRO] BD não registrado.', file=sys.stderr)
        return 1
    if 'medicao' not in registros:
        print('[ERRO] Medição não registrada. Execute: --registrar-medicao <caminho>', file=sys.stderr)
        return 1

    bd_records = obter_bd(conn)
    medicao_records = obter_medicao(conn)
    inconsistencias = validar_aderencia_distribuicao(bd_records, medicao_records)

    bd_pares = {(r['funcao'], r['md_cobranca']) for r in bd_records}
    datas = {r['data'] for r in medicao_records}

    conteudo = gerar_relatorio(
        inconsistencias, registros,
        n_pares_bd=len(bd_pares), n_datas=len(datas), avisos_import=[],
    )
    caminho = salvar_relatorio(conteudo)
    print(f"Relatório gravado em: {caminho}")
    print(f"Total de inconsistências: {len(inconsistencias)}")
    return 1 if inconsistencias else 0


def build_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--registrar-bd', metavar='CAMINHO')
    group.add_argument('--registrar-medicao', metavar='CAMINHO')
    parser.add_argument('--db', default=None, metavar='CAMINHO')
    return parser


def main(argv=None) -> int:
    parser = build_parser(argparse.ArgumentParser(description='Valida BD vs Medição.'))
    args = parser.parse_args(argv)
    conn = conectar(Path(args.db) if args.db else db_path())
    try:
        if args.registrar_bd:
            return cmd_registrar_bd(args.registrar_bd, conn)
        if args.registrar_medicao:
            return cmd_registrar_medicao(args.registrar_medicao, conn)
        return cmd_validar(conn)
    finally:
        conn.close()

if __name__ == '__main__':
    sys.exit(main())
