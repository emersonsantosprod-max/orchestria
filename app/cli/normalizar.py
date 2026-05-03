#!/usr/bin/env python3
"""
app.cli.normalizar — Normaliza a distribuição contratual do BD.

Saída:
    - data/saida/distribuicao_contratual_normalizada.xlsx
    - Relatório de validação no stdout (4 etapas)
"""

import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

from app.domain.distribuicao_contratual import (
    AVISO_COLUNA_DESCONHECIDA,
    AVISO_COLUNA_DUPLICADA,
    AVISO_DECIMAL,
    AVISO_DISCREPANCIA_ATUAL,
    AVISO_HEADER_DUPLICADO,
    AVISO_SIGLA_DUPLICADA,
    AVISO_VALOR_NAO_NUMERICO,
    ERRO_SIGLA,
    ERRO_TOTAL,
    localizar_colunas_chave,
    normalizar_linhas,
    parse_distribuicao_cols,
    validar_distribuicao_cobranca,
)
from app.infrastructure.excel_distribuicao import (
    DistribuicaoContratualMalformadaError,
    escrever_xlsx_normalizado,
    ler_xlsx_contratual,
)
from app.infrastructure.paths import _project_root  # type: ignore

_BASE_DIR = str(_project_root())

ARQUIVO_ENTRADA = os.path.join(
    _BASE_DIR, 'data', 'entrada', 'Dstribuição Contratual do BD  - 2026.xlsx'
)
ARQUIVO_SAIDA = os.path.join(
    _BASE_DIR, 'data', 'saida', 'distribuicao_contratual_normalizada.xlsx'
)

SEP_SECAO = '═' * 80
SEP_LINHA = '─' * 70

TIPOS_ORDEM = [
    ERRO_SIGLA,
    ERRO_TOTAL,
    AVISO_DECIMAL,
    AVISO_SIGLA_DUPLICADA,
    AVISO_COLUNA_DESCONHECIDA,
    AVISO_COLUNA_DUPLICADA,
    AVISO_VALOR_NAO_NUMERICO,
    AVISO_DISCREPANCIA_ATUAL,
    AVISO_HEADER_DUPLICADO,
]

TIPOS_ERRO = {ERRO_SIGLA, ERRO_TOTAL}


def imprimir_relatorio(inconsistencias, arquivo_entrada, arquivo_saida, n_registros):
    resumo = Counter(i['tipo'] for i in inconsistencias)

    print(SEP_SECAO)
    print('ETAPA 1 — DOCUMENTAÇÃO E CRITÉRIOS')
    print(SEP_SECAO)
    print()
    print(f"Arquivo de entrada:\n  {arquivo_entrada}\n")
    print(f"Arquivo de saída:\n  {arquivo_saida}\n")
    print(f"Data/hora : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    print(f"Registros normalizados produzidos: {n_registros}\n")

    print(SEP_SECAO)
    print('ETAPA 2 — RESUMO')
    print(SEP_SECAO)
    print()
    print(f"  {'TIPO':<35} {'OCORRÊNCIAS':>12}")
    print(f"  {'-'*35} {'-'*12}")
    total_erros = 0
    for tipo in TIPOS_ORDEM:
        qtd = resumo.get(tipo, 0)
        if qtd:
            print(f"  {tipo:<35} {qtd:>12}")
            if tipo in TIPOS_ERRO:
                total_erros += qtd
    print(f"  {'-'*35} {'-'*12}")
    print(f"  {'Total de erros':<35} {total_erros:>12}")
    print(f"  {'Total de inconsistências':<35} {sum(resumo.values()):>12}\n")

    print(SEP_SECAO)
    print('ETAPA 3 — DETALHAMENTO')
    print(SEP_SECAO)
    por_tipo = defaultdict(list)
    for inc in inconsistencias:
        por_tipo[inc['tipo']].append(inc)
    num = 0
    for tipo in TIPOS_ORDEM:
        grupo = por_tipo.get(tipo, [])
        if not grupo:
            continue
        print(f"\n  [{tipo}] — {len(grupo)} ocorrência(s)\n  {SEP_LINHA}")
        for inc in grupo:
            num += 1
            print(f"\n  [{num}] {inc.get('erro', '')}")
            for k, v in inc.items():
                if k not in ('tipo', 'erro'):
                    print(f"       {k}: {v}")
            print(f"  {'-'*60}")
    if num == 0:
        print('\n  Nenhuma inconsistência encontrada.')
    print()

    print(SEP_SECAO)
    print('ETAPA 4 — CONCLUSÃO')
    print(SEP_SECAO)
    print()
    total_avisos = sum(resumo.values()) - total_erros
    print(f"  Registros normalizados : {n_registros}")
    print(f"  Erros                  : {total_erros}")
    print(f"  Avisos                 : {total_avisos}\n")
    if total_erros == 0:
        print('NORMALIZAÇÃO CONCLUÍDA: ZERO ERROS')
    else:
        print('NORMALIZAÇÃO CONCLUÍDA: ERROS ENCONTRADOS')


def main() -> int:
    print(f"\n{SEP_SECAO}\nNORMALIZAÇÃO DA DISTRIBUIÇÃO CONTRATUAL DO BD\n{SEP_SECAO}\n")
    if not os.path.exists(ARQUIVO_ENTRADA):
        print(f"[ERRO] Arquivo de entrada não encontrado: {ARQUIVO_ENTRADA}")
        return 1
    os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)
    try:
        headers, data_rows, w_hdr = ler_xlsx_contratual(ARQUIVO_ENTRADA)
        col_map, w_cols = parse_distribuicao_cols(headers)
        sigla_col, funcao_col, atual_col = localizar_colunas_chave(headers)
        normalized, raw_sums, atual, w_norm = normalizar_linhas(
            data_rows, col_map, sigla_col, funcao_col, atual_col)
        w_val = validar_distribuicao_cobranca(normalized, raw_sums, atual)
        escrever_xlsx_normalizado(normalized, ARQUIVO_SAIDA)
    except DistribuicaoContratualMalformadaError as e:
        print(f"[ERRO ESTRUTURAL] {e}")
        return 1
    except (ValueError, OSError) as e:
        print(f"[ERRO CRÍTICO] {e}")
        return 1
    all_inc = w_hdr + w_cols + w_norm + w_val
    imprimir_relatorio(all_inc, ARQUIVO_ENTRADA, ARQUIVO_SAIDA, len(normalized))
    return 1 if any(i['tipo'] in TIPOS_ERRO for i in all_inc) else 0


if __name__ == '__main__':
    sys.exit(main())
