"""
atestado.py — Regras de negócio para atestados médicos.

Responsabilidade única: dada a lista de registros (matricula, inicio, fim),
expandir cada período em registros diários e produzir Update objects com
prioridade absoluta (sobrescrever_obs=True, situacao='AUSENTE').

Não produz inconsistências — o writer emite erros de matrícula/data não
encontrada quando necessário.
"""

from __future__ import annotations

from datetime import timedelta

from app.domain.core import Update, normalizar_matricula, parse_data_obj


def gerar_updates_atestado(dados: list) -> tuple:
    """
    Expande períodos de atestado em registros diários.

    dados: lista de {'linha': int, 'matricula': str, 'inicio': any, 'fim': any}

    Retorna (updates, inconsistencias). Inconsistencias sempre vazia —
    input assumido válido; erros de linha são detectados pelo writer.
    """
    updates = []

    for item in dados:
        mat = normalizar_matricula(item['matricula'])
        ini_obj = parse_data_obj(item['inicio'])
        fim_obj = parse_data_obj(item['fim'])

        if ini_obj is None or fim_obj is None:
            continue

        current = ini_obj
        while current <= fim_obj:
            updates.append(Update(
                tipo='atestado',
                matricula=mat,
                data=current.strftime('%d/%m/%Y'),
                observacao='ATESTADO MÉDICO',
                situacao='AUSENTE',
                sobrescrever_obs=True,
                row=None,
            ))
            current += timedelta(days=1)

    return updates, []
