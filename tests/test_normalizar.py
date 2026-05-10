"""Testes do helper canônico de normalização."""

from app.domain.normalizacao import normalizar, normalizar_chave


def test_none_returns_empty():
    assert normalizar(None) == ''


def test_strip_and_collapse_whitespace():
    assert normalizar('  foo   bar  ') == 'FOO BAR'


def test_accent_fold_nfkd():
    assert normalizar('Função') == 'FUNCAO'
    assert normalizar('férias') == 'FERIAS'


def test_uppercase():
    assert normalizar('abc') == 'ABC'


def test_compatibility_decomposition():
    # NFKD: ﬁ (U+FB01) -> 'fi'
    assert normalizar('oﬁcina') == 'OFICINA'


def test_int_coerced_to_string():
    assert normalizar(42) == '42'


def test_chave_tupla():
    assert normalizar_chave('mecanico', 'unidade a', 'pacote', 'férias') == (
        'MECANICO', 'UNIDADE A', 'PACOTE', 'FERIAS',
    )


def test_chave_com_none_e_int():
    assert normalizar_chave(None, 1, ' x ') == ('', '1', 'X')


def test_chave_idempotente():
    a = normalizar_chave('Mecânico', 'Unidade-A')
    b = normalizar_chave(*a)
    assert a == b
