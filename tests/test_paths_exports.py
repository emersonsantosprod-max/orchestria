"""processed_output_path: saída por feature em <db_dir>/exports/."""

from __future__ import annotations

from pathlib import Path

from app.infrastructure import paths


def test_processed_output_path_em_exports_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "db_path", lambda: tmp_path / "automacao.db")
    expected = tmp_path / "exports" / "medicao_treinamentos_processada.xlsx"
    assert paths.processed_output_path("treinamentos") == expected


def test_processed_output_path_cria_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "db_path", lambda: tmp_path / "automacao.db")
    paths.processed_output_path("atestado")
    assert (tmp_path / "exports").is_dir()


def test_processed_output_path_irmao_do_db(monkeypatch, tmp_path):
    db = tmp_path / "subdir" / "automacao.db"
    monkeypatch.setattr(paths, "db_path", lambda: db)
    p = paths.processed_output_path("ferias")
    assert p.parent == Path(tmp_path / "subdir" / "exports")
