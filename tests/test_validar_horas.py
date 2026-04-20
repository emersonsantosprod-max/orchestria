"""tests/test_validar_horas.py — unit tests for app.validar_horas."""

import pytest
from app.validar_horas import (
    LIMITE_HH,
    ERRO_HORAS_NEGATIVAS,
    ERRO_HORAS_EXCESSO,
    InconsistenciaHr,
    validar,
    gerar_relatorio,
)


def _reg(matricula='123', data='01/04/2026', hr=8.0):
    return {'matricula': matricula, 'data': data, 'hr_trabalhadas': hr}


# ---------------------------------------------------------------------------
# validar()
# ---------------------------------------------------------------------------

def test_validar_sem_inconsistencias():
    regs = [_reg(hr=0.0), _reg(hr=4.5), _reg(hr=LIMITE_HH)]
    assert validar(regs) == []


def test_validar_horas_negativas():
    result = validar([_reg(hr=-0.083)])
    assert len(result) == 1
    assert result[0].tipo_inconsistencia == ERRO_HORAS_NEGATIVAS
    assert result[0].valor == pytest.approx(-0.083)


def test_validar_horas_excesso():
    result = validar([_reg(hr=9.5)])
    assert len(result) == 1
    assert result[0].tipo_inconsistencia == ERRO_HORAS_EXCESSO
    assert result[0].valor == pytest.approx(9.5)


def test_validar_limite_exato_nao_erro():
    result = validar([_reg(hr=LIMITE_HH)])
    assert result == []


def test_validar_zero_nao_erro():
    result = validar([_reg(hr=0.0)])
    assert result == []


def test_validar_none_ignorado():
    result = validar([_reg(hr=None)])
    assert result == []


def test_validar_multiplos_erros():
    regs = [
        _reg(matricula='001', hr=-1.0),
        _reg(matricula='002', hr=10.0),
        _reg(matricula='003', hr=5.0),
    ]
    result = validar(regs)
    assert len(result) == 2
    tipos = {r.tipo_inconsistencia for r in result}
    assert tipos == {ERRO_HORAS_NEGATIVAS, ERRO_HORAS_EXCESSO}


def test_validar_ordenacao():
    regs = [
        _reg(matricula='999', data='03/04/2026', hr=-1.0),
        _reg(matricula='001', data='01/04/2026', hr=10.0),
        _reg(matricula='555', data='01/04/2026', hr=-0.5),
    ]
    result = validar(regs)
    assert [(r.data, r.matricula) for r in result] == [
        ('01/04/2026', '001'),
        ('01/04/2026', '555'),
        ('03/04/2026', '999'),
    ]


# ---------------------------------------------------------------------------
# gerar_relatorio()
# ---------------------------------------------------------------------------

def test_relatorio_aprovada():
    conteudo = gerar_relatorio([], caminho_medicao='/path/to/file.xlsx', n_linhas=10)
    assert 'VALIDAÇÃO CONCLUÍDA: APROVADA' in conteudo


def test_relatorio_com_inconsistencias():
    incs = [
        InconsistenciaHr(matricula='123', data='01/04/2026', valor=9.5, tipo_inconsistencia=ERRO_HORAS_EXCESSO),
        InconsistenciaHr(matricula='456', data='02/04/2026', valor=-0.1, tipo_inconsistencia=ERRO_HORAS_NEGATIVAS),
    ]
    conteudo = gerar_relatorio(incs, caminho_medicao='/path/to/file.xlsx', n_linhas=50)
    assert 'INCONSISTÊNCIAS ENCONTRADAS' in conteudo
    assert ERRO_HORAS_EXCESSO in conteudo
    assert ERRO_HORAS_NEGATIVAS in conteudo


def test_relatorio_4_secoes():
    conteudo = gerar_relatorio([], caminho_medicao='file.xlsx', n_linhas=5)
    for i in range(1, 5):
        assert f'ETAPA {i}' in conteudo


def test_relatorio_limite_documentado():
    conteudo = gerar_relatorio([], caminho_medicao='file.xlsx', n_linhas=5)
    assert '9h10min' in conteudo
