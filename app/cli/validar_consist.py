#!/usr/bin/env python3
"""Entry-point da validação de consistência: original × processado."""

import os
import sys

from app.cli.validar_consist_comparar import comparar_arquivos
from app.cli.validar_consist_relatorio import SEP_SECAO, imprimir_relatorio
from app.paths import _project_root

_BASE_DIR = str(_project_root())

ARQUIVO_ORIGINAL   = os.path.join(_BASE_DIR, 'data', 'entrada', 'Medição Geral Março.xlsx')
ARQUIVO_PROCESSADO = os.path.join(_BASE_DIR, 'data', 'entrada', 'medicao_processada.xlsx')


def main():
    print()
    print(SEP_SECAO)
    print('VALIDAÇÃO DE CONSISTÊNCIA — MEDIÇÃO PROCESSADA')
    print(SEP_SECAO)
    print()

    for caminho, label in [(ARQUIVO_ORIGINAL, 'original'), (ARQUIVO_PROCESSADO, 'processado')]:
        if not os.path.exists(caminho):
            print(f"[ERRO] Arquivo {label} não encontrado: {caminho}")
            sys.exit(1)

    try:
        resultado = comparar_arquivos(ARQUIVO_ORIGINAL, ARQUIVO_PROCESSADO)
    except Exception as e:
        print(f"[ERRO INESPERADO] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    imprimir_relatorio(resultado, ARQUIVO_ORIGINAL, ARQUIVO_PROCESSADO)


if __name__ == '__main__':
    main()
