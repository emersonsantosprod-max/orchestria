"""Funções puras de férias: parsing, seleção, formatação, classificação."""

from datetime import date

import pytest

from app import ferias
from app.infrastructure import excel as writer


@pytest.mark.parametrize("entrada,esperado", [
    ("00012345", "12345"),
    ("1.095585", "95585"),
    ("1.193974", "193974"),
    ("  123  ", "123"),
    (None, ""),
])
def test_normalizar_matricula(entrada, esperado):
    assert writer._normalizar_matricula(entrada) == esperado


def test_parse_periodo_valido():
    ini, fim = ferias.parse_periodo("24/11/2026 a 23/12/2026")
    assert ini == date(2026, 11, 24)
    assert fim == date(2026, 12, 23)


@pytest.mark.parametrize("entrada", [
    None,
    "",
    "24/11/2026",
    "24-11-2026 a 23-12-2026",
    "24/11/2026 a 23/12/2026 ",  # OK: strip aplicado
])
def test_parse_periodo_formato_invalido(entrada):
    if entrada == "24/11/2026 a 23/12/2026 ":
        # caso válido após strip
        ini, fim = ferias.parse_periodo(entrada)
        assert (ini, fim) == (date(2026, 11, 24), date(2026, 12, 23))
        return
    with pytest.raises(ValueError):
        ferias.parse_periodo(entrada)


def test_parse_periodo_invertido():
    with pytest.raises(ValueError):
        ferias.parse_periodo("23/12/2026 a 24/11/2026")


def test_selecionar_ferias_prefere_primeira():
    sel = ferias.selecionar_ferias(
        "01/04/2026 a 30/04/2026", "Aprovado",
        "01/05/2026 a 30/05/2026", "Aprovado",
    )
    assert sel == ("01/04/2026 a 30/04/2026", "1")


def test_selecionar_ferias_fallback_segunda():
    sel = ferias.selecionar_ferias(
        "01/04/2026 a 30/04/2026", "Pendente",
        "01/05/2026 a 30/05/2026", "Aprovado",
    )
    assert sel == ("01/05/2026 a 30/05/2026", "2")


@pytest.mark.parametrize("p1,s1,p2,s2", [
    ("p1", "Pendente", "p2", "Negado"),
    (None, None, None, None),
    ("p1", None, "p2", None),
    ("p1", "Aprovado ", "p2", None),  # 'Aprovado ' com espaço — case sensitive ao trim
])
def test_selecionar_ferias_nenhuma(p1, s1, p2, s2):
    # 'Aprovado ' funciona via strip().lower()
    if s1 == "Aprovado ":
        assert ferias.selecionar_ferias(p1, s1, p2, s2) == ("p1", "1")
        return
    assert ferias.selecionar_ferias(p1, s1, p2, s2) is None


def test_formatar_observacao_sem_sufixo():
    ini, fim = date(2026, 4, 5), date(2026, 4, 25)
    assert ferias.formatar_observacao(ini, fim, com_sufixo=False) == "05/04 a 25/04 - FÉRIAS"


def test_formatar_observacao_com_sufixo():
    ini, fim = date(2026, 4, 5), date(2026, 4, 25)
    assert ferias.formatar_observacao(ini, fim, com_sufixo=True) == "05/04 a 25/04 - FÉRIAS (NÃO DESCONTA)"


@pytest.mark.parametrize("md", ['ADICIONAL', 'PACOTE', 'CUSTO MANSERV'])
def test_classificar_md_cobranca_direto(md):
    tipo, sufixo, erro = ferias._classificar(md, 'QUALQUER', {})
    assert (tipo, sufixo, erro) == ('FERIAS_DIRETO', False, None)


def test_classificar_ferias_sem_desconto():
    base = {'ELET-IV': 'FÉRIAS S/ DESC'}
    tipo, sufixo, erro = ferias._classificar('CENTRAL', 'ELET-IV', base)
    assert (tipo, sufixo, erro) == ('FERIAS_SD', True, None)


def test_classificar_ferias_normal():
    base = {'ELET-IV': 'NORMAL'}
    tipo, sufixo, erro = ferias._classificar('CENTRAL', 'ELET-IV', base)
    assert (tipo, sufixo, erro) == ('FERIAS', False, None)


def test_classificar_sg_funcao_ausente():
    tipo, _, erro = ferias._classificar('CENTRAL', 'INEXISTENTE', {})
    assert tipo == 'SKIP'
    assert erro == 'sg função não classificada'


def test_classificar_sg_funcao_vazio():
    tipo, _, erro = ferias._classificar('CENTRAL', '', {})
    assert tipo == 'SKIP'
    assert erro == 'sg função não classificada'
