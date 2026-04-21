"""
validar_distribuicao.py — lógica de validação BD vs Medição.

Regras:
  - Universo temporal: datas presentes na Medição apenas (BD não gera datas)
  - ERRO_LINHA_AUSENTE: funcao presente na Medição no dia, mas md_cobranca
    esperado pelo BD está ausente
  - Sem join sintético sobre datas × BD; sem exceções por ausência total de funcao
  - round(value, 10) apenas na etapa de comparação; sem int() ou truncamento
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app import core

ERRO_LINHA_AUSENTE       = 'ERRO_LINHA_AUSENTE'
ERRO_INSUFICIENCIA_RATEIO = 'ERRO_INSUFICIENCIA_RATEIO'
ERRO_EXCESSO_RATEIO      = 'ERRO_EXCESSO_RATEIO'

TIPOS_ORDEM = [ERRO_LINHA_AUSENTE, ERRO_INSUFICIENCIA_RATEIO, ERRO_EXCESSO_RATEIO]


@dataclass
class InconsistenciaDistribuicao:
    data: str
    funcao: str
    md_cobranca: str
    esperado: float
    realizado: float
    diff: float
    tipo_inconsistencia: str


def validar_aderencia_distribuicao(
    bd_records: list[dict],
    medicao_records: list[dict],
) -> list[InconsistenciaDistribuicao]:
    # Step 1 — Agregar BD por (funcao, md_cobranca), ignorando area
    bd_expected: dict[tuple[str, str], float] = defaultdict(float)
    for r in bd_records:
        bd_expected[(r['funcao'], r['md_cobranca'])] += r['quantidade']

    # Índice BD: funcao → conjunto de md_cobranças esperadas
    bd_md_por_funcao: dict[str, set[str]] = defaultdict(set)
    for funcao, md_cobranca in bd_expected:
        bd_md_por_funcao[funcao].add(md_cobranca)

    # Step 2 — Agregar Medição por (data, sg_funcao, md_cobranca)
    medicao_grouped: dict[tuple[str, str, str], float] = defaultdict(float)
    for r in medicao_records:
        medicao_grouped[(r['data'], r['sg_funcao'], r['md_cobranca'])] += r['pct_cobranca']

    # Step 3 — Funcoes presentes por data (universo temporal vem da Medição)
    funcoes_por_data: dict[str, set[str]] = defaultdict(set)
    for data, sg_funcao, _ in medicao_grouped:
        funcoes_por_data[data].add(sg_funcao)

    # Step 4 — Validação em dois níveis
    result: list[InconsistenciaDistribuicao] = []
    for data in sorted(funcoes_por_data):
        for funcao in funcoes_por_data[data]:                    # Nível 1: funcao presente na Medição
            if funcao not in bd_md_por_funcao:
                continue                                          # sem contrato BD para esta funcao
            for md_cobranca in bd_md_por_funcao[funcao]:        # Nível 2: md_cobranças do BD
                esperado  = bd_expected[(funcao, md_cobranca)]
                realizado = medicao_grouped.get((data, funcao, md_cobranca), 0.0)
                diff      = round(realizado - esperado, 10)

                if realizado == 0.0:
                    tipo = ERRO_LINHA_AUSENTE
                elif diff < 0:
                    tipo = ERRO_INSUFICIENCIA_RATEIO
                elif diff > 0:
                    tipo = ERRO_EXCESSO_RATEIO
                else:
                    continue

                result.append(InconsistenciaDistribuicao(
                    data=data,
                    funcao=funcao,
                    md_cobranca=md_cobranca,
                    esperado=esperado,
                    realizado=realizado,
                    diff=diff,
                    tipo_inconsistencia=tipo,
                ))

    return sorted(result, key=lambda x: (x.data, x.funcao, x.md_cobranca))


def validar_para_dominio(
    bd_records: list[dict],
    medicao_snapshot: list[dict],
) -> list[core.Inconsistencia]:
    """Boundary pública para consumidores do pipeline.

    Executa `validar_aderencia_distribuicao()` e converte cada `InconsistenciaDistribuicao` em
    `core.Inconsistencia(origem='writer', ...)`. Isola a forma interna
    do validador do contrato estável do pipeline.
    """
    return [
        core.inconsistencia(
            origem='writer',
            linha='-',
            matricula=inc.funcao,
            data=inc.data,
            erro=(
                f"{inc.tipo_inconsistencia} [{inc.md_cobranca}] "
                f"esperado={inc.esperado:.4f} realizado={inc.realizado:.4f} "
                f"diff={inc.diff:.4f}"
            ),
        )
        for inc in validar_aderencia_distribuicao(bd_records, medicao_snapshot)
    ]


# ---------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------

from collections import Counter  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402

_DIR_SAIDA = Path('data/saida')

SEP_SECAO = '═' * 80
SEP_LINHA  = '─' * 70

_W_DATA   = 12
_W_FUNCAO = 18
_W_MD     = 14
_W_NUM    = 10
_W_TIPO   = 26


def _linha_tabela(data, funcao, md_cobranca, esperado, realizado, diff, tipo) -> str:
    return (
        f"{data:<{_W_DATA}}"
        f"{funcao:<{_W_FUNCAO}}"
        f"{md_cobranca:<{_W_MD}}"
        f"{esperado:>{_W_NUM}.4f}  "
        f"{realizado:>{_W_NUM}.4f}  "
        f"{diff:>{_W_NUM}.4f}  "
        f"{tipo}"
    )


def _cabecalho_tabela() -> str:
    return (
        f"{'DATA':<{_W_DATA}}"
        f"{'FUNCAO':<{_W_FUNCAO}}"
        f"{'MD_COBRANCA':<{_W_MD}}"
        f"{'ESPERADO':>{_W_NUM}}  "
        f"{'REALIZADO':>{_W_NUM}}  "
        f"{'DIFF':>{_W_NUM}}  "
        f"{'TIPO'}"
    )


def gerar_relatorio(
    inconsistencias: list[InconsistenciaDistribuicao],
    registros: dict,
    n_pares_bd: int,
    n_datas: int,
    avisos_import: list[str],
) -> str:
    lines: list[str] = []
    add = lines.append
    resumo = Counter(i.tipo_inconsistencia for i in inconsistencias)

    add(SEP_SECAO)
    add('ETAPA 1 — DOCUMENTAÇÃO')
    add(SEP_SECAO)
    add('')
    reg_bd  = registros.get('bd',      {'caminho': '(não registrado)', 'importado_em': '-'})
    reg_med = registros.get('medicao', {'caminho': '(não registrado)', 'importado_em': '-'})
    add(f"  BD registrado      : {reg_bd['caminho']}")
    add(f"  Importado em       : {reg_bd['importado_em']}")
    add(f"  Medição registrada : {reg_med['caminho']}")
    add(f"  Importado em       : {reg_med['importado_em']}")
    add(f"  Gerado em          : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    add('')
    add(f"  Pares BD (funcao × md_cobranca) : {n_pares_bd}")
    add(f"  Datas em Medição                 : {n_datas}")
    add('')
    add('  Modelo de validação:')
    add('    Para cada data em Medição × pares BD onde funcao está presente:')
    add('      realizado = SUM(% Cobrança) por (data, funcao, md_cobranca)')
    add('      esperado  = SUM(BD.quantidade) por (funcao, md_cobranca)')
    add('      diff      = round(realizado − esperado, 10)')
    add('')
    if avisos_import:
        add('  Avisos de importação:')
        for av in avisos_import:
            add(f"    {av}")
        add('')

    add(SEP_SECAO)
    add('ETAPA 2 — RESUMO')
    add(SEP_SECAO)
    add('')
    add(f"  {'TIPO':<35} {'OCORRÊNCIAS':>12}")
    add(f"  {'-'*35} {'-'*12}")
    for tipo in TIPOS_ORDEM:
        qtd = resumo.get(tipo, 0)
        if qtd:
            add(f"  {tipo:<35} {qtd:>12}")
    add(f"  {'-'*35} {'-'*12}")
    add(f"  {'TOTAL':<35} {sum(resumo.values()):>12}")
    add('')

    add(SEP_SECAO)
    add('ETAPA 3 — DETALHES')
    add(SEP_SECAO)
    add('')
    if not inconsistencias:
        add('  Nenhuma inconsistência encontrada.')
    else:
        cab = _cabecalho_tabela()
        sep = '  ' + '─' * len(cab)
        add('  ' + cab)
        add(sep)
        for inc in inconsistencias:
            add('  ' + _linha_tabela(
                inc.data, inc.funcao, inc.md_cobranca,
                inc.esperado, inc.realizado, inc.diff,
                inc.tipo_inconsistencia,
            ))
    add('')

    add(SEP_SECAO)
    add('ETAPA 4 — CONCLUSÃO')
    add(SEP_SECAO)
    add('')
    add(f"  {ERRO_LINHA_AUSENTE:<35} : {resumo.get(ERRO_LINHA_AUSENTE, 0)}")
    add(f"  {ERRO_INSUFICIENCIA_RATEIO:<35} : {resumo.get(ERRO_INSUFICIENCIA_RATEIO, 0)}")
    add(f"  {ERRO_EXCESSO_RATEIO:<35} : {resumo.get(ERRO_EXCESSO_RATEIO, 0)}")
    add('')
    if inconsistencias:
        add('VALIDAÇÃO CONCLUÍDA: INCONSISTÊNCIAS ENCONTRADAS')
    else:
        add('VALIDAÇÃO CONCLUÍDA: APROVADA')
    add('')

    return '\n'.join(lines)


def _salvar_relatorio(conteudo: str) -> Path:
    _DIR_SAIDA.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    caminho = _DIR_SAIDA / f'relatorio_validacao_distribuicao_{ts}.txt'
    caminho.write_text(conteudo, encoding='utf-8')
    return caminho
