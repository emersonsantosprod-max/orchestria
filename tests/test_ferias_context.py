"""FeriasContext: dataclass frozen com defaults sensatos."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.ferias import FeriasContext


def test_minimal_construction():
    ctx = FeriasContext(
        base_cobranca={'X': 'PADRAO'},
        medicao_por_matricula={},
        md_cobranca_por_chave={},
        sg_funcao_por_chave={},
    )
    assert ctx.unidade_por_chave == {}
    assert ctx.base_tags_por_chave == {}
    assert ctx.mes_referencia is None
    assert ctx.col_map == {}


def test_frozen():
    ctx = FeriasContext(
        base_cobranca={}, medicao_por_matricula={},
        md_cobranca_por_chave={}, sg_funcao_por_chave={},
    )
    with pytest.raises(FrozenInstanceError):
        ctx.base_cobranca = {'mut': 1}  # type: ignore
