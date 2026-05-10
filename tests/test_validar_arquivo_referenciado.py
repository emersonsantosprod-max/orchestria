"""Testes de paths.validar_arquivo_referenciado — fonte canônica de validação."""

from __future__ import annotations

import os
import stat

import pytest

from app.infrastructure.paths import validar_arquivo_referenciado


def test_arquivo_existente_xlsx_retorna_path(tmp_path):
    p = tmp_path / 'medicao.xlsx'
    p.write_bytes(b'PK\x03\x04')  # zip header — basta existir
    out = validar_arquivo_referenciado(str(p))
    assert out == p


def test_arquivo_inexistente_levanta_filenotfounderror(tmp_path):
    p = tmp_path / 'no.xlsx'
    with pytest.raises(FileNotFoundError, match='não encontrado'):
        validar_arquivo_referenciado(str(p))


def test_extensao_nao_suportada_levanta_valueerror(tmp_path):
    p = tmp_path / 'arquivo.txt'
    p.write_text('x')
    with pytest.raises(ValueError, match='Extensão não suportada'):
        validar_arquivo_referenciado(str(p))


def test_extensao_aceita_via_parametro_exts(tmp_path):
    p = tmp_path / 'bd.sqlite'
    p.write_bytes(b'SQLite')
    out = validar_arquivo_referenciado(str(p), exts=('.sqlite', '.db'))
    assert out == p


def test_arquivo_sem_permissao_levanta_permissionerror(tmp_path):
    p = tmp_path / 'medicao.xlsx'
    p.write_bytes(b'PK\x03\x04')
    os.chmod(p, 0)
    try:
        with pytest.raises(PermissionError, match='Sem permissão'):
            validar_arquivo_referenciado(str(p))
    finally:
        os.chmod(p, stat.S_IREAD | stat.S_IWRITE)
