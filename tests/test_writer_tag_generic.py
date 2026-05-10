"""Writer aplica tag de Update.tag (sem branching por tipo='atestado')."""

from app.domain.core import Update
from app.infrastructure.excel import aplicar_updates


def _col_map_completo() -> dict:
    return {
        '_header_row': 1,
        'data': 0,
        'matricula': 1,
        'desconto': 2,
        'observacao': 3,
        'situacao': 4,
        'tag': 5,
    }


def test_atestado_escreve_tag_via_update_tag():
    """tipo='atestado' não escreve TAG implicitamente — só via Update.tag."""
    col_map = _col_map_completo()
    index = {('123', '01/05/2026'): [10]}
    upd = Update(
        tipo='atestado',
        matricula='123',
        data='01/05/2026',
        observacao='ATESTADO MÉDICO',
        situacao='AUSENTE',
        sobrescrever_obs=True,
        tag='ATESTADO',
        row=10,
    )
    patches, inc = aplicar_updates([upd], col_map, index)
    assert (10, col_map['tag'] + 1) in patches
    assert patches[(10, col_map['tag'] + 1)] == 'ATESTADO'
    assert inc == []


def test_ferias_escreve_tag_arbitraria():
    """Writer é genérico: férias com tag setada escreve a tag."""
    col_map = _col_map_completo()
    index = {('123', '01/05/2026'): [10]}
    upd = Update(
        tipo='ferias',
        matricula='123',
        data='01/05/2026',
        observacao='01/05 a 10/05 - FÉRIAS',
        situacao='FÉRIAS',
        sobrescrever_obs=True,
        tag='M-PACO-FE',
        row=10,
    )
    patches, _ = aplicar_updates([upd], col_map, index)
    assert patches[(10, col_map['tag'] + 1)] == 'M-PACO-FE'


def test_sem_tag_nao_toca_coluna():
    col_map = _col_map_completo()
    index = {('123', '01/05/2026'): [10]}
    upd = Update(
        tipo='ferias',
        matricula='123',
        data='01/05/2026',
        observacao='X',
        situacao='FÉRIAS',
        sobrescrever_obs=True,
        row=10,
    )
    patches, _ = aplicar_updates([upd], col_map, index)
    assert (10, col_map['tag'] + 1) not in patches


def test_sem_coluna_tag_no_col_map_nao_falha():
    col_map = {
        '_header_row': 1,
        'data': 0, 'matricula': 1, 'desconto': 2, 'observacao': 3,
    }
    index = {('123', '01/05/2026'): [10]}
    upd = Update(
        tipo='atestado',
        matricula='123',
        data='01/05/2026',
        observacao='ATESTADO MÉDICO',
        situacao='AUSENTE',
        sobrescrever_obs=True,
        tag='ATESTADO',
        row=10,
    )
    patches, inc = aplicar_updates([upd], col_map, index)
    assert inc == []
