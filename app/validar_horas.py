"""
validar_horas.py — validação de Hr Trabalhadas (col 19) na Medição.

Regras:
  - Universo: todas as linhas de dados da Medição
  - ERRO_HORAS_NEGATIVAS: valor < 0
  - ERRO_HORAS_EXCESSO: valor > LIMITE_HH (9h10min = 9 + 10/60)
  - Linhas com valor None (célula vazia) são ignoradas
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

LIMITE_HH = 9 + 10 / 60

ERRO_HORAS_NEGATIVAS = 'ERRO_HORAS_NEGATIVAS'
ERRO_HORAS_EXCESSO   = 'ERRO_HORAS_EXCESSO'

TIPOS_ORDEM = [ERRO_HORAS_NEGATIVAS, ERRO_HORAS_EXCESSO]


@dataclass
class InconsistenciaHr:
    matricula: str
    data: str
    valor: float
    tipo_inconsistencia: str


def validar(registros: list[dict]) -> list[InconsistenciaHr]:
    result: list[InconsistenciaHr] = []
    for r in registros:
        v = r['hr_trabalhadas']
        if v is None:
            continue
        if v < 0:
            tipo = ERRO_HORAS_NEGATIVAS
        elif v > LIMITE_HH:
            tipo = ERRO_HORAS_EXCESSO
        else:
            continue
        result.append(InconsistenciaHr(
            matricula=r['matricula'],
            data=r['data'],
            valor=v,
            tipo_inconsistencia=tipo,
        ))
    return sorted(result, key=lambda x: (x.data, x.matricula))


# ---------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------

_DIR_SAIDA = Path('data/saida')

SEP_SECAO = '═' * 80
SEP_LINHA  = '─' * 70

_W_MAT   = 14
_W_DATA  = 14
_W_VALOR = 12
_W_TIPO  = 26


def _linha_tabela(matricula: str, data: str, valor: float, tipo: str) -> str:
    return (
        f"{matricula:<{_W_MAT}}"
        f"{data:<{_W_DATA}}"
        f"{valor:>{_W_VALOR}.4f}  "
        f"{tipo}"
    )


def _cabecalho_tabela() -> str:
    return (
        f"{'MATRICULA':<{_W_MAT}}"
        f"{'DATA':<{_W_DATA}}"
        f"{'HR_TRAB':>{_W_VALOR}}  "
        f"{'TIPO'}"
    )


def gerar_relatorio(
    inconsistencias: list[InconsistenciaHr],
    caminho_medicao: str,
    n_linhas: int,
) -> str:
    lines: list[str] = []
    add = lines.append
    resumo = Counter(i.tipo_inconsistencia for i in inconsistencias)

    add(SEP_SECAO)
    add('ETAPA 1 — DOCUMENTAÇÃO')
    add(SEP_SECAO)
    add('')
    add(f"  Arquivo de medição : {caminho_medicao}")
    add(f"  Linhas de dados    : {n_linhas}")
    add(f"  Limite configurado : 9h10min ({LIMITE_HH:.4f}h)")
    add(f"  Coluna analisada   : col 19 (Hr Trabalhadas)")
    add(f"  Chave de linha     : col 1 (RE/Matrícula) + col 0 (Data)")
    add(f"  Gerado em          : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    add('')
    add('  Modelo de validação:')
    add('    Para cada linha de dados:')
    add(f"      valor < 0            → {ERRO_HORAS_NEGATIVAS}")
    add(f"      valor > {LIMITE_HH:.4f}  → {ERRO_HORAS_EXCESSO}")
    add(f"      0 ≤ valor ≤ {LIMITE_HH:.4f}  → válido")
    add(f"      valor = None (vazio) → ignorado")
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
            add('  ' + _linha_tabela(inc.matricula, inc.data, inc.valor, inc.tipo_inconsistencia))
    add('')

    add(SEP_SECAO)
    add('ETAPA 4 — CONCLUSÃO')
    add(SEP_SECAO)
    add('')
    add(f"  {ERRO_HORAS_NEGATIVAS:<35} : {resumo.get(ERRO_HORAS_NEGATIVAS, 0)}")
    add(f"  {ERRO_HORAS_EXCESSO:<35} : {resumo.get(ERRO_HORAS_EXCESSO, 0)}")
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
    caminho = _DIR_SAIDA / f'relatorio_validacao_horas_{ts}.txt'
    caminho.write_text(conteudo, encoding='utf-8')
    return caminho
