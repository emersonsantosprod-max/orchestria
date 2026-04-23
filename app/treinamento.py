"""
treinamento.py — Regras de negócio para processamento de treinamentos.

Responsabilidades:
  - Validar e converter carga (ex: '2H' → horas)
  - Expandir datas multi-dia (replicação integral da carga)
  - Agrupar registros por (matrícula, data)
  - Calcular desconto respeitando o limite de 9h10 (9 + 10/60 horas)
  - Montar texto de observação (delega deduplicação ao core)
  - Retornar lista de Update (tipo='treinamento') e Inconsistencia (origem='treinamento')

Erros detectados aqui:
  - 'erro de carga'
  - 'erro de data'
  - 'treinamento não classificado'

Erros detectados em writer.py (fora do escopo):
  - 'matrícula não encontrada'
  - 'data não encontrada'
"""

import re
from collections import defaultdict

from app.core import (
    Update,
    deduplicar_observacao,
    inconsistencia,
    normalizar_matricula,
)

_RE_CARGA = re.compile(r'(\d+)H')
_RE_INTERVALO = re.compile(r'(\d{1,2})\s+À\s+(\d{1,2})/(\d{2})/(\d{4})')
_RE_DATA_SIMPLES = re.compile(r'\d{2}/\d{2}/\d{4}')


def converter_carga_para_horas(carga_str: str) -> int:
    match = _RE_CARGA.fullmatch(carga_str.strip())
    if not match:
        raise ValueError(f"Formato de carga inválido: '{carga_str}'")
    horas = int(match.group(1))
    if horas == 0:
        raise ValueError(f"Carga zero inválida: '{carga_str}'")
    return horas


def expandir_datas(data_val) -> list:
    """
    Retorna lista de datas individuais ('dd/mm/aaaa').

    Aceita datetime, 'dd/mm/aaaa', 'DD À DD/mm/aaaa'.
    Lança ValueError em formato inválido ou intervalo incoerente.
    """
    if hasattr(data_val, 'strftime'):
        return [data_val.strftime('%d/%m/%Y')]

    s = str(data_val).strip()

    intervalo = _RE_INTERVALO.fullmatch(s)
    if intervalo:
        dia_ini = int(intervalo.group(1))
        dia_fim = int(intervalo.group(2))
        mes, ano = intervalo.group(3), intervalo.group(4)
        if dia_ini > dia_fim:
            raise ValueError(f"Intervalo de datas inválido (início > fim): '{s}'")
        return [f"{d:02d}/{mes}/{ano}" for d in range(dia_ini, dia_fim + 1)]

    if _RE_DATA_SIMPLES.fullmatch(s):
        return [s]

    raise ValueError(f"Formato de data inválido: '{s}'")


def classificar_treinamento(nome: str, tabela: dict) -> str:
    chave = nome.strip().upper()
    if chave not in tabela:
        raise KeyError(nome)
    return tabela[chave]


def agrupar_por_matricula_data(registros: list) -> dict:
    """
    Agrupa registros já expandidos por (matrícula, data).
    IMPORTANTE: expansão multi-dia ocorre ANTES desta etapa.
    """
    grupos = defaultdict(list)
    for r in registros:
        grupos[(r['matricula'], r['data'])].append(r)
    return dict(grupos)


LIMITE_HH = 9 + 10/60   # 9h10 exatos (= 9.16666..., igual ao Excel)


def calcular_desconto(horas_nao_rem: int, horas_total: int) -> float:
    """
    Desconto em horas. Limite 9h10. Remunerado nunca desconta.
    """
    if horas_total <= LIMITE_HH:
        return horas_nao_rem
    excesso = horas_total - LIMITE_HH
    return max(0, horas_nao_rem - excesso)


def _texto_treinamento(nome: str, horas: int, remunerado: bool) -> str:
    sufixo = " (NÃO DESCONTA)" if remunerado else ""
    return f"TREIN. {nome.upper()} - {horas}H{sufixo}"


def montar_observacao(lista_treinamentos: list, observacao_existente) -> str:
    """
    Monta texto final da observação para um grupo, reaproveitando conteúdo
    já presente na célula e evitando duplicação.
    """
    novas_entradas = [
        _texto_treinamento(t['nome'], t['horas'], t['remunerado'])
        for t in lista_treinamentos
    ]
    return deduplicar_observacao(observacao_existente, novas_entradas)


def gerar_updates_treinamento(
    dados: list,
    tabela_classificacao: dict,
    observacoes_existentes: dict = None,
) -> tuple:
    """
    Retorna (atualizacoes, inconsistencias).

      atualizacoes: list[Update] (tipo='treinamento')
        - row=None ⇒ writer aplica em todas as linhas do índice (matricula, data)
        - desconto_min em minutos
        - sobrescrever_obs=False (append com dedup)

      inconsistencias: list[Inconsistencia] (origem='treinamento')
    """
    if observacoes_existentes is None:
        observacoes_existentes = {}

    inconsistencias = []
    registros_expandidos = []

    for r in dados:
        matricula_norm = normalizar_matricula(r.get('matricula'))

        try:
            horas_total = converter_carga_para_horas(r['carga'])
        except ValueError:
            inconsistencias.append(inconsistencia(
                'treinamento',
                linha=r['linha'], matricula=matricula_norm,
                data=str(r.get('data', '')), erro='erro de carga',
            ))
            continue

        try:
            datas = expandir_datas(r['data'])
        except ValueError:
            inconsistencias.append(inconsistencia(
                'treinamento',
                linha=r['linha'], matricula=matricula_norm,
                data=str(r.get('data', '')), erro='erro de data',
            ))
            continue

        try:
            tipo = classificar_treinamento(r['treinamento'], tabela_classificacao)
        except KeyError:
            inconsistencias.append(inconsistencia(
                'treinamento',
                linha=r['linha'], matricula=matricula_norm,
                data=str(r.get('data', '')), erro='treinamento não classificado',
            ))
            continue

        for data in datas:
            registros_expandidos.append({
                'linha':       r['linha'],
                'matricula':   matricula_norm,
                'nome':        r['nome'],
                'treinamento': r['treinamento'],
                'horas':       horas_total,
                'tipo':        tipo,
                'data':        data,
            })

    grupos = agrupar_por_matricula_data(registros_expandidos)

    atualizacoes = []

    for (matricula, data), grupo in grupos.items():
        horas_nao_rem = sum(r['horas'] for r in grupo if r['tipo'] == 'nao_remunerado')
        horas_rem     = sum(r['horas'] for r in grupo if r['tipo'] == 'remunerado')
        horas_total   = horas_nao_rem + horas_rem

        desconto_minutos = round(calcular_desconto(horas_nao_rem, horas_total) * 60)

        lista_trein = [
            {
                'nome':       r['treinamento'],
                'horas':      r['horas'],
                'remunerado': r['tipo'] == 'remunerado',
            }
            for r in grupo
        ]

        obs_existente = observacoes_existentes.get((matricula, data), '')
        observacao = montar_observacao(lista_trein, obs_existente)

        atualizacoes.append(Update(
            tipo='treinamento',
            matricula=matricula,
            data=data,
            observacao=observacao,
            desconto_min=desconto_minutos,
            sobrescrever_obs=True,   # observação já dedup'd por montar_observacao
            row=None,
        ))

    return atualizacoes, inconsistencias
