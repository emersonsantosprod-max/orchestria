"""Regras de negócio de férias: sobrescrita de observação, classificação por linha, rateio."""

from datetime import date

from app.domain import ferias
from app.domain.core import Update
from app.infrastructure import excel as writer


def _col_map_minimo():
    return {
        'data': 0, 'matricula': 1, 'desconto': 2, 'observacao': 3,
        'situacao': 4, 'md_cobranca': 5, 'sg_funcao': 6, '_header_row': 1,
    }


# REGRESSÃO: caso real VALDIVANDO FELIPE DE ALMEIDA — observação prévia
# "COB. FÉRIAS DE MARCELO SILVA" devia ser limpa ao aplicar FERIAS_DIRETO.

def test_regressao_ferias_direto_com_observacao():
    """FERIAS_DIRETO produz observacao com período e sobrescrever_obs=True."""
    dados = [{
        'linha': 6, 'chapa': '1.248649',
        'p1': '06/04/2026 a 05/05/2026', 's1': 'Aprovado',
        'p2': None, 's2': None,
    }]
    medicao_por_mat = {
        '248649': [(date(2026, 4, 6), '06/04/2026', [2282])],
    }
    md_cob = {('248649', '06/04/2026'): 'ADICIONAL'}
    sg_fun = {('248649', '06/04/2026'): 'SOLD-I'}

    atus, incs = ferias.gerar_updates_ferias(
        dados, {}, medicao_por_mat, md_cob, sg_fun,
        date(2026, 4, 1), _col_map_minimo(),
    )

    assert incs == []
    assert len(atus) == 1
    a = atus[0]
    assert a.situacao == 'FÉRIAS'
    assert a.observacao == '06/04 a 05/05 - FÉRIAS'
    assert a.sobrescrever_obs is True   # SEMPRE True em férias


def test_regressao_writer_emite_patch_com_observacao():
    """Verifica que writer.aplicar_updates emite observação com período quando férias sobrescreve obs."""
    col_map = _col_map_minimo()
    updates = [Update(
        tipo='ferias',
        matricula='248649',
        data='06/04/2026',
        row=2282,
        situacao='FÉRIAS',
        observacao='06/04 a 05/05 - FÉRIAS',
        sobrescrever_obs=True,
    )]
    patches, _ = writer.aplicar_updates(updates, col_map, index={})
    col_obs_1 = col_map['observacao'] + 1
    col_sit_1 = col_map['situacao'] + 1
    assert patches[(2282, col_obs_1)] == '06/04 a 05/05 - FÉRIAS'
    assert patches[(2282, col_sit_1)] == 'FÉRIAS'


def test_ferias_sd_emite_observacao_com_sufixo():
    dados = [{
        'linha': 6, 'chapa': '1.000111',
        'p1': '01/04/2026 a 03/04/2026', 's1': 'Aprovado',
        'p2': None, 's2': None,
    }]
    medicao_por_mat = {'111': [(date(2026, 4, 1), '01/04/2026', [10])]}
    md_cob = {('111', '01/04/2026'): 'CENTRAL'}
    sg_fun = {('111', '01/04/2026'): 'AJUD-CIVIL'}
    base_cob = {'AJUD-CIVIL': 'FÉRIAS S/ DESC'}

    atus, incs = ferias.gerar_updates_ferias(
        dados, base_cob, medicao_por_mat, md_cob, sg_fun,
        date(2026, 4, 1), _col_map_minimo(),
    )
    assert incs == []
    assert atus[0].situacao == 'FÉRIAS S/ DESC'
    assert atus[0].observacao == '01/04 a 03/04 - FÉRIAS (NÃO DESCONTA)'
    assert atus[0].sobrescrever_obs is True


def test_ferias_normal_emite_observacao_sem_sufixo():
    dados = [{
        'linha': 6, 'chapa': '1.000111',
        'p1': '01/04/2026 a 03/04/2026', 's1': 'Aprovado',
        'p2': None, 's2': None,
    }]
    medicao_por_mat = {'111': [(date(2026, 4, 1), '01/04/2026', [10])]}
    md_cob = {('111', '01/04/2026'): 'CENTRAL'}
    sg_fun = {('111', '01/04/2026'): 'ARTIF'}
    base_cob = {'ARTIF': 'FÉRIAS'}

    atus, _ = ferias.gerar_updates_ferias(
        dados, base_cob, medicao_por_mat, md_cob, sg_fun,
        date(2026, 4, 1), _col_map_minimo(),
    )
    assert atus[0].situacao == 'FÉRIAS'
    assert atus[0].observacao == '01/04 a 03/04 - FÉRIAS'
    assert atus[0].sobrescrever_obs is True


def test_rateio_uma_data_multiplas_linhas_atualizadas():
    """Mesmo (mat, data) com 3 rows na medição → 3 atualizações idênticas."""
    dados = [{
        'linha': 6, 'chapa': '1.000111',
        'p1': '01/04/2026 a 01/04/2026', 's1': 'Aprovado',
        'p2': None, 's2': None,
    }]
    medicao_por_mat = {
        '111': [(date(2026, 4, 1), '01/04/2026', [100, 200, 300])],
    }
    md_cob = {('111', '01/04/2026'): 'ADICIONAL'}
    sg_fun = {('111', '01/04/2026'): 'X'}

    atus, incs = ferias.gerar_updates_ferias(
        dados, {}, medicao_por_mat, md_cob, sg_fun,
        date(2026, 4, 1), _col_map_minimo(),
    )
    assert incs == []
    assert sorted(a.row for a in atus) == [100, 200, 300]
    assert all(a.situacao == 'FÉRIAS' for a in atus)
    assert all(a.observacao == '01/04 a 01/04 - FÉRIAS' for a in atus)
    assert all(a.sobrescrever_obs is True for a in atus)


def test_observacao_usa_periodo_original_nao_clipped():
    dados = [{
        'linha': 6, 'chapa': '1.000111',
        'p1': '28/03/2026 a 02/04/2026', 's1': 'Aprovado',
        'p2': None, 's2': None,
    }]
    medicao_por_mat = {
        '111': [
            (date(2026, 4, 1), '01/04/2026', [10]),
            (date(2026, 4, 2), '02/04/2026', [11]),
        ],
    }
    md_cob = {('111', '01/04/2026'): 'CENTRAL', ('111', '02/04/2026'): 'CENTRAL'}
    sg_fun = {('111', '01/04/2026'): 'X', ('111', '02/04/2026'): 'X'}
    base_cob = {'X': 'FÉRIAS'}

    atus, _ = ferias.gerar_updates_ferias(
        dados, base_cob, medicao_por_mat, md_cob, sg_fun,
        date(2026, 4, 1), _col_map_minimo(),
    )
    assert all(a.observacao == '28/03 a 02/04 - FÉRIAS' for a in atus)


# Ordenação invariante (CLAUDE.md): writer.aplicar_updates aplica férias
# DEPOIS de treinamento, sobrescrevendo a observação na mesma célula.

def test_ferias_sobrescreve_observacao_de_treinamento_na_mesma_celula():
    col_map = _col_map_minimo()
    index = {('111', '01/04/2026'): [50]}

    updates = [
        Update(
            tipo='treinamento',
            matricula='111',
            data='01/04/2026',
            observacao='TREIN. NR-35 - 8H',
            desconto_min=0,
            sobrescrever_obs=True,
        ),
        Update(
            tipo='ferias',
            matricula='111',
            data='01/04/2026',
            row=50,
            situacao='FÉRIAS',
            observacao='01/04 a 01/04 - FÉRIAS',
            sobrescrever_obs=True,
        ),
    ]
    patches, _ = writer.aplicar_updates(updates, col_map, index)
    col_obs_1 = col_map['observacao'] + 1
    col_sit_1 = col_map['situacao'] + 1
    assert patches[(50, col_obs_1)] == '01/04 a 01/04 - FÉRIAS'
    assert patches[(50, col_sit_1)] == 'FÉRIAS'
