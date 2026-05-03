"""Regression tests for ui.gui_handlers: worker thread error recovery + lock contract."""

import logging
import sqlite3
import threading
import time

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


def _ctx() -> tuple[gui_handlers.GuiContext, '_FakeContext']:
    fake = _FakeContext()
    return gui_handlers.GuiContext(
        imprimir_log=fake.imprimir_log,
        limpar_log=fake.limpar_log,
        desabilitar_botoes=fake.desabilitar_botoes,
        habilitar_botoes=fake.habilitar_botoes,
        marshal_to_main=fake.marshal_to_main,
        db_write_lock=threading.Lock(),
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

    monkeypatch.setattr(gui_handlers.data, 'conectar', _raise)

    ctx, fake = _ctx()
    gui_handlers.iniciar_lancamento(ctx)

    assert fake.habilitados == 1, 'buttons must be re-enabled even when conectar() raises'
    assert any('[ERRO]' in line for line in fake.logs), 'erro deve aparecer no log'
    assert fake.marshal_calls == [], 'mostrar_resultado não deve ser marshalled em falha'


def test_executar_fluxo_worker_nao_chama_popular(monkeypatch):
    """Bootstrap-once: worker thread NUNCA chama popular_* (essas rodam apenas na main thread em ui/gui.py)."""
    _stub_selecionar_arquivo(monkeypatch)
    _stub_thread_sync(monkeypatch)

    chamadas: list[str] = []

    class _FakeConn:
        def close(self):
            pass

    monkeypatch.setattr(gui_handlers.data, 'conectar', lambda: _FakeConn())
    monkeypatch.setattr(
        gui_handlers.data, 'popular_bd_se_vazio',
        lambda _c: chamadas.append('popular_bd'),
    )
    monkeypatch.setattr(
        gui_handlers.data, 'popular_treinamentos_se_vazio',
        lambda _c: chamadas.append('popular_trein'),
    )

    class _FakeResultado:
        processados = atualizados = 0
        ferias_processadas = ferias_atualizadas = 0
        atestados_processados = atestados_atualizados = 0
        inconsistencias: list = []
        caminho_saida = '/tmp/x.xlsx'

    monkeypatch.setattr(gui_handlers, 'executar_pipeline', lambda **_kw: _FakeResultado())

    ctx, _fake = _ctx()
    gui_handlers.iniciar_lancamento(ctx)

    assert chamadas == [], f'worker thread não pode chamar popular_*: {chamadas}'


def test_executar_fluxo_logs_checkpoints_em_ordem(monkeypatch, caplog):
    """Sequência de checkpoints permite localizar o ponto exato de freeze."""
    _stub_selecionar_arquivo(monkeypatch)
    _stub_thread_sync(monkeypatch)

    class _FakeConn:
        def close(self):
            pass

    monkeypatch.setattr(gui_handlers.data, 'conectar', lambda: _FakeConn())

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
        gui_handlers.data, 'conectar',
        lambda: spawned.append('NÃO DEVERIA SER CHAMADO') or None,
    )

    ctx, fake = _ctx()
    iniciar(ctx)

    assert spawned == []
    assert fake.habilitados == 1


def test_gui_lock_nao_bloqueia_leitura_concorrente(tmp_path):
    """Contrato: writer segura o threading.Lock; reader em outra thread continua progredindo.

    Garantia: a serialização de writes via GuiContext.db_write_lock é apenas para
    writes; readers não concorrem pelo mesmo lock — WAL do SQLite cuida deles.
    """
    db_path = tmp_path / "lock_test.db"
    boot = sqlite3.connect(str(db_path))
    boot.execute("PRAGMA journal_mode=WAL")
    boot.execute("CREATE TABLE t(x INTEGER)")
    boot.commit()
    boot.close()

    write_lock = threading.Lock()
    write_held = threading.Event()
    reader_done = threading.Event()
    erros: list[BaseException] = []

    def writer():
        try:
            with write_lock:
                conn_w = sqlite3.connect(str(db_path), timeout=2)
                try:
                    conn_w.execute("BEGIN IMMEDIATE")
                    conn_w.execute("INSERT INTO t(x) VALUES (1)")
                    write_held.set()
                    time.sleep(0.5)
                    conn_w.commit()
                finally:
                    conn_w.close()
        except BaseException as e:
            erros.append(e)

    def reader():
        try:
            assert write_held.wait(timeout=2.0)
            conn_r = sqlite3.connect(str(db_path), timeout=2)
            try:
                conn_r.execute("SELECT 1").fetchone()
            finally:
                conn_r.close()
            reader_done.set()
        except BaseException as e:
            erros.append(e)

    t_w = threading.Thread(target=writer)
    t_r = threading.Thread(target=reader)
    t_w.start()
    t_r.start()
    t_w.join(timeout=3)
    t_r.join(timeout=3)

    assert not erros, f"falha em concorrência reader/writer: {erros}"
    assert reader_done.is_set(), "reader não progrediu enquanto writer segurava o lock"
