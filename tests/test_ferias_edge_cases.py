"""Casos extremos e erros de férias: interseção parcial, período fora do mês, dedup, pre-flight."""

from datetime import date

import pytest

from app import ferias


def _col_map_minimo():
    return {
        'data': 0, 'matricula': 1, 'desconto': 2, 'observacao': 3,
        'situacao': 4, 'md_cobranca': 5, 'sg_funcao': 6, '_header_row': 1,
    }


# ---------------------------------------------------------------------------
# Interseção Parcial: período atravessa mês (março → abril)
# ---------------------------------------------------------------------------

def test_intersecao_parcial_mes_anterior():
    """Período 28/03–02/04: apenas dias de abril são processados."""
    dados = [{
        'linha': 6, 'chapa': '1.095585',
        'p1': '28/03/2026 a 02/04/2026', 's1': 'Aprovado',
        'p2': None, 's2': None,
    }]
    base_cob = {'ELET-IV': 'NORMAL'}
    medicao_por_mat = {
        '95585': [
            (date(2026, 3, 30), '30/03/2026', [10]),
            (date(2026, 4, 1),  '01/04/2026', [20]),
            (date(2026, 4, 2),  '02/04/2026', [21]),
            (date(2026, 4, 3),  '03/04/2026', [22]),
        ],
    }
    md_cob = {('95585', '01/04/2026'): 'CENTRAL',
              ('95585', '02/04/2026'): 'CENTRAL'}
    sg_fun = {('95585', '01/04/2026'): 'ELET-IV',
              ('95585', '02/04/2026'): 'ELET-IV'}

    atus, incs = ferias.processar_ferias(
        dados, base_cob, medicao_por_mat, md_cob, sg_fun,
        date(2026, 4, 1), _col_map_minimo(),
    )
    assert incs == []
    rows = sorted(a['row'] for a in atus)
    assert rows == [20, 21]
    assert all(a['observacao'] == '28/03 a 02/04 - FÉRIAS' for a in atus)
    assert all(a['situacao'] == 'FÉRIAS' for a in atus)


# ---------------------------------------------------------------------------
# Período completamente fora do mês → skip silencioso
# ---------------------------------------------------------------------------

def test_periodo_fora_do_mes_skip_silencioso():
    """Período 01/05–03/05 não intersecta abril → sem atualizações, sem erro."""
    dados = [{
        'linha': 6, 'chapa': '1.000111',
        'p1': '01/05/2026 a 03/05/2026', 's1': 'Aprovado',
        'p2': None, 's2': None,
    }]
    medicao_por_mat = {'111': [(date(2026, 4, 1), '01/04/2026', [10])]}
    atus, incs = ferias.processar_ferias(
        dados, {}, medicao_por_mat, {}, {},
        date(2026, 4, 1), _col_map_minimo()
    )
    assert atus == []
    assert incs == []


# ---------------------------------------------------------------------------
# Férias sem aprovação
# ---------------------------------------------------------------------------

def test_ferias_sem_aprovacao():
    """Nenhuma 1° nem 2° aprovada → skip silenciosamente (nenhuma inconsistência)."""
    dados = [{
        'linha': 6, 'chapa': '1.000111',
        'p1': '01/04/2026 a 03/04/2026', 's1': 'Pendente',
        'p2': '01/05/2026 a 03/05/2026', 's2': 'Negado',
    }]
    atus, incs = ferias.processar_ferias(
        dados, {}, {}, {}, {}, date(2026, 4, 1), _col_map_minimo()
    )
    assert atus == []
    assert incs == []


# ---------------------------------------------------------------------------
# Período inválido
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("periodo", [
    "01/04/2026",           # falta ' a dd/mm/yyyy'
    "01-04-2026 a 03-04-2026",  # formato errado
    "03/04/2026 a 01/04/2026",  # invertido
])
def test_periodo_invalido(periodo):
    """Períodos com formato errado ou invertido → erro 'período inválido'."""
    dados = [{
        'linha': 6, 'chapa': '1.000111',
        'p1': periodo, 's1': 'Aprovado',
        'p2': None, 's2': None,
    }]
    atus, incs = ferias.processar_ferias(
        dados, {}, {}, {}, {}, date(2026, 4, 1), _col_map_minimo()
    )
    assert atus == []
    assert len(incs) == 1
    assert incs[0]['erro'] == 'período inválido'


# ---------------------------------------------------------------------------
# Matrícula não encontrada na medição
# ---------------------------------------------------------------------------

def test_matricula_nao_encontrada_uma_vez():
    """Uma matrícula ausente → exatamente 1 erro (não por dia)."""
    dados = [{
        'linha': 6, 'chapa': '1.999999',
        'p1': '01/04/2026 a 30/04/2026', 's1': 'Aprovado',
        'p2': None, 's2': None,
    }]
    atus, incs = ferias.processar_ferias(
        dados, {}, {}, {}, {}, date(2026, 4, 1), _col_map_minimo()
    )
    assert atus == []
    assert len(incs) == 1
    assert incs[0]['erro'] == 'matrícula não encontrada'


# ---------------------------------------------------------------------------
# Deduplicação: SgFunção ausente para múltiplos dias
# ---------------------------------------------------------------------------

def test_sg_dedup_por_matricula():
    """SgFunção missing em 5 dias: apenas 1 inconsistência por (mat, sg)."""
    dados = [{
        'linha': 6, 'chapa': '1.000111',
        'p1': '01/04/2026 a 30/04/2026', 's1': 'Aprovado',
        'p2': None, 's2': None,
    }]
    medicao_por_mat = {
        '111': [
            (date(2026, 4, d), f'{d:02d}/04/2026', [10 + d])
            for d in range(1, 6)
        ],
    }
    md_cob = {('111', f'{d:02d}/04/2026'): 'CENTRAL' for d in range(1, 6)}
    sg_fun = {('111', f'{d:02d}/04/2026'): 'X-INEXISTENTE' for d in range(1, 6)}
    atus, incs = ferias.processar_ferias(
        dados, {}, medicao_por_mat, md_cob, sg_fun,
        date(2026, 4, 1), _col_map_minimo()
    )
    assert atus == []
    assert len(incs) == 1
    assert incs[0]['erro'] == 'sg função não classificada'


# ---------------------------------------------------------------------------
# Pre-flight: colunas obrigatórias ausentes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("col_ausente", ['situacao', 'md_cobranca', 'sg_funcao'])
def test_pre_flight_colunas_obrigatorias(col_ausente):
    """Coluna obrigatória ausente → RuntimeError."""
    col_map = _col_map_minimo()
    del col_map[col_ausente]

    with pytest.raises(RuntimeError, match='colunas obrigatórias'):
        ferias.processar_ferias([], {}, {}, {}, {}, date(2026, 4, 1), col_map)


# ---------------------------------------------------------------------------
# MD Cobrança especial sem observação obrigatória
# ---------------------------------------------------------------------------

def test_md_cobranca_direto_com_observacao():
    """ADICIONAL/PACOTE/CUSTO MANSERV → Situação FÉRIAS, observação 'DD/MM A DD/MM - FÉRIAS'."""
    dados = [{
        'linha': 6, 'chapa': '1.000111',
        'p1': '01/04/2026 a 03/04/2026', 's1': 'Aprovado',
        'p2': None, 's2': None,
    }]
    medicao_por_mat = {'111': [(date(2026, 4, 1), '01/04/2026', [10])]}
    md_cob = {('111', '01/04/2026'): 'PACOTE'}
    sg_fun = {('111', '01/04/2026'): 'ELET-IV'}

    atus, incs = ferias.processar_ferias(
        dados, {}, medicao_por_mat, md_cob, sg_fun,
        date(2026, 4, 1), _col_map_minimo(),
    )
    assert incs == []
    assert len(atus) == 1
    assert atus[0]['situacao'] == 'FÉRIAS'
    assert atus[0]['observacao'] == '01/04 a 03/04 - FÉRIAS'
    assert atus[0]['sobrescrever_obs'] is True
