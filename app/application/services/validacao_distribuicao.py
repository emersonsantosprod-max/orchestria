"""validar_para_dominio: boundary do pipeline para validação BD vs Medição."""

from __future__ import annotations

from app.domain import core
from app.domain.distribuicao import validar_aderencia_distribuicao


def validar_para_dominio(
    bd_records: list[dict],
    medicao_snapshot: list[dict],
) -> list[core.Inconsistencia]:
    """Executa validação e converte cada InconsistenciaDistribuicao em
    core.Inconsistencia(origem='writer', ...). Isola a forma interna do
    validador do contrato estável do pipeline.
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
