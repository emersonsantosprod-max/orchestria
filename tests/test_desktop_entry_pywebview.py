"""Testes do JsApi exposto para pywebview (sem dep runtime)."""

from __future__ import annotations

import sys
import types

import pytest


def _instalar_webview_mock(monkeypatch, *, windows, dialog_result=None):
    """Cria um stub do módulo `webview` antes do import de JsApi."""
    fake_window = types.SimpleNamespace(
        create_file_dialog=lambda *args, **kw: dialog_result,
    )
    fake_webview = types.SimpleNamespace(
        OPEN_DIALOG='OPEN_DIALOG',
        windows=[fake_window] if windows else [],
    )
    monkeypatch.setitem(sys.modules, 'webview', fake_webview)


def test_escolher_arquivo_retorna_path_selecionado(monkeypatch):
    _instalar_webview_mock(monkeypatch, windows=True, dialog_result=('/abs/path.xlsx',))
    from app.desktop_entry import JsApi
    api = JsApi()
    assert api.escolher_arquivo('Selecionar') == '/abs/path.xlsx'


def test_escolher_arquivo_cancelado_retorna_none(monkeypatch):
    _instalar_webview_mock(monkeypatch, windows=True, dialog_result=None)
    from app.desktop_entry import JsApi
    assert JsApi().escolher_arquivo() is None


def test_escolher_arquivo_lista_vazia_retorna_none(monkeypatch):
    _instalar_webview_mock(monkeypatch, windows=True, dialog_result=())
    from app.desktop_entry import JsApi
    assert JsApi().escolher_arquivo() is None


def test_escolher_arquivo_sem_window_retorna_none(monkeypatch):
    _instalar_webview_mock(monkeypatch, windows=False)
    from app.desktop_entry import JsApi
    assert JsApi().escolher_arquivo() is None


@pytest.mark.skipif('webview' in sys.modules, reason='webview já instalado')
def test_jsapi_independe_de_runtime_webview(monkeypatch):
    """JsApi.escolher_arquivo só importa webview ao ser chamado."""
    monkeypatch.delitem(sys.modules, 'webview', raising=False)
    from app.desktop_entry import JsApi
    api = JsApi()
    assert callable(api.escolher_arquivo)
