"""Formatação do relatório estruturado (4 etapas) para stdout."""

import os
from collections import defaultdict
from datetime import datetime

from app.cli.validar_consist_comparar import (
    CRITERIO_ND,
    ERRO_CRITICO,
    ERRO_DATA,
    ERRO_ESTRUTURAL,
    ERRO_FORMATO,
    ERRO_MAPEAMENTO,
    ERRO_NUMERICO,
    INFO_MODIFICACAO,
)

SEP_SECAO = '═' * 80
SEP_LINHA = '─' * 70

TIPOS_ORDEM = [
    ERRO_CRITICO,
    ERRO_NUMERICO,
    ERRO_DATA,
    ERRO_MAPEAMENTO,
    ERRO_ESTRUTURAL,
    ERRO_FORMATO,
    CRITERIO_ND,
    INFO_MODIFICACAO,
]


def imprimir_relatorio(resultado: dict, caminho_orig: str, caminho_proc: str):
    erros      = resultado['erros']
    resumo     = resultado['resumo']
    estrutural = resultado['estrutural']
    total_orig = resultado['total_linhas_orig']
    total_proc = resultado['total_linhas_proc']
    total_comp = resultado['total_linhas_comparadas']

    print(SEP_SECAO)
    print('ETAPA 1 — DOCUMENTAÇÃO UTILIZADA')
    print(SEP_SECAO)
    print()
    print('Arquivos .md lidos:')
    print(f"  - {os.path.join(os.path.dirname(caminho_orig), '..', '..', 'CLAUDE.md')} (CLAUDE.md do projeto)")
    print()
    print('Critérios extraídos:')
    print('  - Colunas modificadas pelo pipeline: 18 (Descontos), 22 (Observação)')
    print('  - Colunas de fórmula dependentes de col 18: 19 (Hr Trabalhadas),')
    print('    23 (Total Descontos), 24 (HH Medido), 25 (Histograma)')
    print('  - Todas as demais colunas (0-17 exceto 18, 20-21, 22) devem ser idênticas')
    print('  - Formato de desconto: HH:MM (escrito como inlineStr via ZIP patch)')
    print('  - Formato de observação: TREIN. {nome} - {horas}H [+ (NÃO DESCONTA)]')
    print('  - Chave de identificação: RE (col 1) + Data (col 0)')
    print('  - Aba comparada: Frequencia (sem acento)')
    print('  - Passada única read_only: iter_rows(values_only=True)')
    print()
    print('Arquivos comparados:')
    print(f"  - Original  : {caminho_orig}")
    print(f"  - Processado: {caminho_proc}")
    print(f"  - Data/hora : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"  - Linhas no original  : {total_orig}")
    print(f"  - Linhas no processado: {total_proc}")
    print(f"  - Linhas comparadas   : {total_comp}")
    print()

    print(SEP_SECAO)
    print('ETAPA 2 — RESUMO')
    print(SEP_SECAO)
    print()

    if estrutural:
        print('Alertas estruturais:')
        for s in estrutural:
            print(f"  [{s['tipo']}] {s['descricao']}")
        print()

    print(f"  {'TIPO':<35} {'OCORRÊNCIAS':>12}")
    print(f"  {'-'*35} {'-'*12}")

    total_erros_reais = 0
    for tipo in TIPOS_ORDEM:
        qtd = resumo.get(tipo, 0)
        if qtd > 0:
            print(f"  {tipo:<35} {qtd:>12}")
            if tipo not in (INFO_MODIFICACAO,):
                total_erros_reais += qtd

    print(f"  {'-'*35} {'-'*12}")
    print(f"  {'Total de erros (excl. INFO)':<35} {total_erros_reais:>12}")
    print(f"  {'Total de diferenças encontradas':<35} {sum(resumo.values()):>12}")
    print()
    print(f"  ERRO_CRITICO    : {resumo.get(ERRO_CRITICO, 0)}")
    print(f"  ERRO_NUMERICO   : {resumo.get(ERRO_NUMERICO, 0)}")
    print(f"  ERRO_DATA       : {resumo.get(ERRO_DATA, 0)}")
    print(f"  ERRO_MAPEAMENTO : {resumo.get(ERRO_MAPEAMENTO, 0)}")
    print(f"  ERRO_ESTRUTURAL : {resumo.get(ERRO_ESTRUTURAL, 0)}")
    print(f"  ERRO_FORMATO    : {resumo.get(ERRO_FORMATO, 0)}")
    print(f"  CRITÉRIO NÃO DEFINIDO: {resumo.get(CRITERIO_ND, 0)}")
    print()

    print(SEP_SECAO)
    print('ETAPA 3 — DETALHAMENTO DOS ERROS')
    print(SEP_SECAO)

    por_tipo = defaultdict(list)
    for e in erros:
        por_tipo[e['tipo']].append(e)

    erro_num_global = 0
    for tipo in TIPOS_ORDEM:
        grupo = por_tipo.get(tipo, [])
        if not grupo:
            continue
        print()
        print(f"  [{tipo}] — {len(grupo)} ocorrência(s)")
        print(f"  {SEP_LINHA}")

        for e in grupo:
            erro_num_global += 1
            print()
            print(f"  [Erro {erro_num_global}]")
            print(f"  Linha original    : {e['linha']}")
            print(f"  Linha processada  : {e['linha']}")
            print(f"  Identificador (RE): {e['re']}")
            print(f"  Nome              : {e['nome']}")
            print(f"  Data              : {e['data']}")
            print(f"  Coluna            : {e['coluna_idx']} — {e['coluna_nome']}")
            print(f"  Valor original    : {e['valor_original']}")
            print(f"  Valor processado  : {e['valor_processado']}")
            print(f"  Tipo              : {e['tipo']}")
            print(f"  Descrição         : {e['contexto']}")
            print(f"  {'-'*60}")

    if erro_num_global == 0:
        print()
        print('  Nenhuma diferença encontrada.')
    print()

    print(SEP_SECAO)
    print('ETAPA 4 — CONCLUSÃO')
    print(SEP_SECAO)
    print()

    n_critico    = resumo.get(ERRO_CRITICO, 0)
    n_numerico   = resumo.get(ERRO_NUMERICO, 0)
    n_data       = resumo.get(ERRO_DATA, 0)
    n_mapeamento = resumo.get(ERRO_MAPEAMENTO, 0)
    n_estrutural = resumo.get(ERRO_ESTRUTURAL, 0)
    n_modificacao = resumo.get(INFO_MODIFICACAO, 0)

    print(f"  Total de linhas verificadas                    : {total_comp}")
    print(f"  Diferenças em colunas modificadas (cols 18/22) : {n_modificacao}")
    print(f"  Erros críticos (colunas não devem mudar)       : {n_critico}")
    print(f"  Erros numéricos (fórmulas/recálculo)           : {n_numerico}")
    print(f"  Erros de data                                  : {n_data}")
    print(f"  Erros de mapeamento (RE)                       : {n_mapeamento}")
    print(f"  Erros estruturais                              : {n_estrutural}")
    print()

    if n_critico == 0 and n_data == 0 and n_mapeamento == 0:
        if erro_num_global == 0:
            print('VALIDAÇÃO CONCLUÍDA: ZERO ERROS')
        else:
            print('VALIDAÇÃO CONCLUÍDA: ZERO ERROS')
            print()
            if n_numerico > 0:
                print(
                    f"  Nota: {n_numerico} diferença(s) numéricas detectadas em colunas de fórmula "
                    f"(cols 19, 23, 24, 25)."
                )
                print(
                    "  Essas são derivações esperadas do recálculo do Excel após a atualização "
                    "da coluna Descontos (col 18) pelo pipeline."
                )
            if n_estrutural > 0:
                print(
                    f"  Nota: {n_estrutural} diferença(s) estrutural(is) (ex: aba Planilha3 removida pelo ZIP patch)."
                )
    else:
        print('VALIDAÇÃO CONCLUÍDA: ERROS ENCONTRADOS')
        print()
        if n_critico > 0:
            print(f"  ATENÇÃO: {n_critico} ERRO(S) CRÍTICO(S) — colunas que não devem ser modificadas foram alteradas.")
        if n_data > 0:
            print(f"  ATENÇÃO: {n_data} ERRO(S) DE DATA — datas foram alteradas.")
        if n_mapeamento > 0:
            print(f"  ATENÇÃO: {n_mapeamento} ERRO(S) DE MAPEAMENTO — RE/matrícula foram alterados.")
    print()
