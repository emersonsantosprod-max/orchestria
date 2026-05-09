from __future__ import annotations

from app.infrastructure import paths


def test_run_grava_em_path_patcheado(isolated_paths):
    output = paths.processed_output_path("atestado")
    assert output.parent == (isolated_paths / "exports")
