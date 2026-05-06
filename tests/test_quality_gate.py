"""Testes unitários do quality gate (metrics + report)."""

from __future__ import annotations

from pathlib import Path

from scripts.quality_gate.metrics import (
    coletar_metricas_codigo,
    contar_metricas_arquivo,
)
from scripts.quality_gate.report import avaliar_regressao, formatar_tabela


def test_contar_metricas_arquivo_ignora_vazio_e_comentario():
    src = (
        '# comentario\n'
        '\n'
        'def soma(a, b):\n'
        '    return a + b\n'
        '\n'
        'async def grava():\n'
        '    pass\n'
    )
    linhas, funcoes = contar_metricas_arquivo(src)
    assert linhas == 4
    assert funcoes == 2


def test_contar_metricas_arquivo_syntax_error_devolve_zero_funcoes():
    linhas, funcoes = contar_metricas_arquivo('def quebrado(:\n')
    assert funcoes == 0
    assert linhas == 1


def test_coletar_metricas_codigo_oversized(tmp_path: Path):
    pequeno = tmp_path / 'a.py'
    pequeno.write_text('def f():\n    return 1\n')
    grande = tmp_path / 'b.py'
    grande.write_text('x = 1\n' * 600)
    metricas = coletar_metricas_codigo([tmp_path], limite_linhas=500)
    assert metricas['oversized_files'] == 1
    assert metricas['functions'] == 1
    assert metricas['lines'] == 2 + 600


def test_avaliar_regressao_violations_aumenta_falha():
    base = {'violations': 0, 'oversized_files': 0, 'lines': 100, 'functions': 10}
    cur = {'violations': 1, 'oversized_files': 0, 'lines': 100, 'functions': 10}
    assert avaliar_regressao(base, cur) is True


def test_avaliar_regressao_lines_dentro_da_tolerancia_passa():
    base = {'violations': 0, 'oversized_files': 0, 'lines': 1000, 'functions': 100}
    cur = {'violations': 0, 'oversized_files': 0, 'lines': 1040, 'functions': 100}
    assert avaliar_regressao(base, cur) is False


def test_avaliar_regressao_lines_acima_da_tolerancia_falha():
    base = {'violations': 0, 'oversized_files': 0, 'lines': 1000, 'functions': 100}
    cur = {'violations': 0, 'oversized_files': 0, 'lines': 1100, 'functions': 100}
    assert avaliar_regressao(base, cur) is True


def test_formatar_tabela_inclui_todas_metricas():
    base = {'violations': 0, 'oversized_files': 0, 'lines': 100, 'functions': 5}
    cur = {'violations': 2, 'oversized_files': 1, 'lines': 110, 'functions': 5}
    saida = formatar_tabela(base, cur)
    for item in ('violations', 'oversized_files', 'lines', 'functions'):
        assert item in saida
    assert '+2' in saida
    assert '+10.00%' in saida
