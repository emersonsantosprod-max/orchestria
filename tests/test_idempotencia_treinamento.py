from app import excel as writer
from app.domain.core import Update


def _col_map_basico():
    return {
        'data': 0,
        'matricula': 1,
        'observacao': 2,
        'desconto': 3,
        '_header_row': 1,
        '_ausentes': (),
    }


def test_desconto_treinamento_em_celula_ja_lancada_emite_warning():
    col_map = _col_map_basico()
    index = {('111', '18/03/2026'): [2]}
    obs_existentes = {('111', '18/03/2026'): 'TREIN. TR-X - 2H'}
    descontos_existentes = {('111', '18/03/2026'): 120}

    upd = Update(
        tipo='treinamento',
        matricula='111',
        data='18/03/2026',
        observacao='TREIN. TR-X - 2H',
        desconto_min=120,
        sobrescrever_obs=True,
        row=None,
    )

    patches, incs = writer.aplicar_updates(
        [upd], col_map, index,
        obs_existentes=obs_existentes,
        descontos_existentes=descontos_existentes,
    )

    assert (2, 4) not in patches  # desconto NÃO foi escrito (não duplicou)
    assert (2, 3) in patches      # observação ainda foi escrita (idempotente por dedup)
    assert len(incs) == 1
    assert 'desconto de treinamento já aplicado' in incs[0].erro


def test_desconto_treinamento_em_celula_limpa_aplica_normal():
    col_map = _col_map_basico()
    index = {('111', '18/03/2026'): [2]}
    obs_existentes = {('111', '18/03/2026'): ''}
    descontos_existentes = {('111', '18/03/2026'): 0}

    upd = Update(
        tipo='treinamento',
        matricula='111',
        data='18/03/2026',
        observacao='TREIN. TR-X - 2H',
        desconto_min=120,
        sobrescrever_obs=True,
        row=None,
    )

    patches, incs = writer.aplicar_updates(
        [upd], col_map, index,
        obs_existentes=obs_existentes,
        descontos_existentes=descontos_existentes,
    )

    assert patches[(2, 4)] == '02:00'
    assert incs == []
