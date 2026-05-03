"""CLI boundary tests for `app.cli.normalizar` (fail-fast on bad input)."""

from __future__ import annotations

from unittest.mock import patch

import openpyxl

from app.cli import normalizar as cli
from app.infrastructure.excel_distribuicao import (
    DistribuicaoContratualMalformadaError,
)


def _run_main(capsys, entrada: str, saida: str) -> tuple[int, str]:
    with patch.object(cli, 'ARQUIVO_ENTRADA', entrada), \
         patch.object(cli, 'ARQUIVO_SAIDA', saida):
        rc = cli.main()
    out = capsys.readouterr().out
    return rc, out


def test_arquivo_inexistente_retorna_1_sem_traceback(tmp_path, capsys):
    rc, out = _run_main(capsys, str(tmp_path / 'no.xlsx'), str(tmp_path / 'out.xlsx'))
    assert rc == 1
    assert '[ERRO]' in out
    assert 'não encontrado' in out
    assert 'Traceback' not in out


def test_xlsx_sem_sigla_retorna_1_erro_estrutural(tmp_path, capsys):
    entrada = tmp_path / 'in.xlsx'
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['FUNÇÃO', 'CENTRAL'])
    ws.append(['ELET-I', 5])
    wb.save(entrada)
    wb.close()

    rc, out = _run_main(capsys, str(entrada), str(tmp_path / 'out.xlsx'))
    assert rc == 1
    assert '[ERRO ESTRUTURAL]' in out
    assert 'Traceback' not in out


def test_dominio_nao_propaga_excecao_no_caminho_feliz(tmp_path, capsys):
    entrada = tmp_path / 'in.xlsx'
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['FUNÇÃO', 'SIGLA', 'CENTRAL'])
    ws.append(['ELETRICISTA I', None, 3])
    wb.save(entrada)
    wb.close()

    rc, out = _run_main(capsys, str(entrada), str(tmp_path / 'out.xlsx'))
    assert rc == 1
    assert 'ERRO_SIGLA' in out
    assert 'Traceback' not in out


def test_erro_estrutural_e_subclasse_de_value_error():
    assert issubclass(DistribuicaoContratualMalformadaError, ValueError)
