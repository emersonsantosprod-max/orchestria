"""Regression tests for ui.gui_handlers: worker thread error recovery."""

import logging
import sqlite3

import pytest

from ui import gui_handlers


class _FakeContext:
    def __init__(self):
        self.logs: list[str] = []
        self.desabilitados = 0
        self.habilitados = 0
        self.marshal_calls: list = []

    def imprimir_log(self, texto: str) -> None:
        self.logs.append(texto)

    def limpar_log(self) -> None:
        self.logs.clear()

    def desabilitar_botoes(self) -> None:
        self.desabilitados += 1

    def habilitar_botoes(self) -> None:
        self.habilitados += 1

    def marshal_to_main(self, fn) -> None:
        self.marshal_calls.append(fn)


class _SyncThread:
    """Drop-in para threading.Thread que executa target() inline."""

    def __init__(self, target, daemon=None):
        self._target = target

    def start(self) -> None:
        self._target()


def _ctx() -> gui_handlers.GuiContext:
    fake = _FakeContext()
    return gui_handlers.GuiContext(
        imprimir_log=fake.imprimir_log,
        limpar_log=fake.limpar_log,
        desabilitar_botoes=fake.desabilitar_botoes,
        habilitar_botoes=fake.habilitar_botoes,
        marshal_to_main=fake.marshal_to_main,
    ), fake


def _stub_selecionar_arquivo(monkeypatch, ret: str = '/tmp/fake.xlsx') -> None:
    monkeypatch.setattr(gui_handlers, 'selecionar_arquivo', lambda _titulo: ret)


def _stub_thread_sync(monkeypatch) -> None:
    monkeypatch.setattr(gui_handlers.threading, 'Thread', _SyncThread)


def test_executar_fluxo_reabilita_botoes_quando_conectar_falha(monkeypatch):
    """Se db.conectar() levanta, GUI não pode wedge: habilitar_botoes precisa rodar."""
    _stub_selecionar_arquivo(monkeypatch)
    _stub_thread_sync(monkeypatch)

    def _raise(*_a, **_kw):
        raise sqlite3.OperationalError('database is locked')

    monkeypatch.setattr(gui_handlers.db, 'conectar', _raise)

    ctx, fake = _ctx()
    gui_handlers.iniciar_lancamento(ctx)

    assert fake.habilitados == 1, 'buttons must be re-enabled even when conectar() raises'
    assert any('[ERRO]' in line for line in fake.logs), 'erro deve aparecer no log'
    assert fake.marshal_calls == [], 'mostrar_resultado não deve ser marshalled em falha'


def test_executar_fluxo_reabilita_botoes_quando_popular_falha(monkeypatch):
    """Se popular_treinamentos_se_vazio levanta, finally precisa fechar conn e re-armar botões."""
    _stub_selecionar_arquivo(monkeypatch)
    _stub_thread_sync(monkeypatch)

    closed = []

    class _FakeConn:
        def close(self):
            closed.append(True)

    monkeypatch.setattr(gui_handlers.db, 'conectar', lambda: _FakeConn())
    monkeypatch.setattr(gui_handlers.db, 'popular_bd_se_vazio', lambda _c: False)

    def _raise(_c):
        raise RuntimeError('boom no bootstrap de treinamentos')

    monkeypatch.setattr(gui_handlers.db, 'popular_treinamentos_se_vazio', _raise)

    ctx, fake = _ctx()
    gui_handlers.iniciar_lancamento(ctx)

    assert fake.habilitados == 1
    assert closed == [True], 'conn.close() precisa ser chamado mesmo após falha'
    assert any('[ERRO]' in line for line in fake.logs)


def test_executar_fluxo_logs_checkpoints_em_ordem(monkeypatch, caplog):
    """Sequência de checkpoints permite localizar o ponto exato de freeze."""
    _stub_selecionar_arquivo(monkeypatch)
    _stub_thread_sync(monkeypatch)

    class _FakeConn:
        def close(self):
            pass

    monkeypatch.setattr(gui_handlers.db, 'conectar', lambda: _FakeConn())
    monkeypatch.setattr(gui_handlers.db, 'popular_bd_se_vazio', lambda _c: False)
    monkeypatch.setattr(gui_handlers.db, 'popular_treinamentos_se_vazio', lambda _c: False)

    class _FakeResultado:
        processados = 0
        atualizados = 0
        ferias_processadas = 0
        ferias_atualizadas = 0
        atestados_processados = 0
        atestados_atualizados = 0
        inconsistencias: list = []
        caminho_saida = '/tmp/medicao_processada.xlsx'

    monkeypatch.setattr(
        gui_handlers, 'executar_pipeline', lambda **_kw: _FakeResultado()
    )

    ctx, fake = _ctx()
    with caplog.at_level(logging.INFO, logger=gui_handlers.logger.name):
        gui_handlers.iniciar_lancamento(ctx)

    msgs = [r.getMessage() for r in caplog.records]
    seq = [
        'iniciando worker thread',
        'abrindo conexão SQLite',
        'popular_bd_se_vazio',
        'popular_treinamentos_se_vazio',
        'executar_pipeline',
        'concluído',
    ]
    pos = -1
    for needle in seq:
        nxt = next((i for i, m in enumerate(msgs) if i > pos and needle in m), None)
        assert nxt is not None, f'checkpoint ausente ou fora de ordem: {needle!r} em {msgs}'
        pos = nxt

    assert fake.habilitados == 1
    assert len(fake.marshal_calls) == 1, 'mostrar_resultado deve ter sido marshalled'


@pytest.mark.parametrize('iniciar', [
    gui_handlers.iniciar_lancamento,
    gui_handlers.iniciar_ferias,
    gui_handlers.iniciar_atestado,
])
def test_executar_fluxo_cancela_se_arquivo_nao_selecionado(monkeypatch, iniciar):
    """Se o usuário cancela o filedialog, fluxo deve abortar sem spawnar worker."""
    monkeypatch.setattr(gui_handlers, 'selecionar_arquivo', lambda _titulo: '')
    _stub_thread_sync(monkeypatch)

    spawned = []
    monkeypatch.setattr(
        gui_handlers.db, 'conectar',
        lambda: spawned.append('NÃO DEVERIA SER CHAMADO') or None,
    )

    ctx, fake = _ctx()
    iniciar(ctx)

    assert spawned == []
    assert fake.habilitados == 1
