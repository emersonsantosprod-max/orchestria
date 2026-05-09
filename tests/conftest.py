"""
Filesystem isolation for tests.

Parallel-safe rules:
- no assertions against repo-global filesystem state
- no shared temp directories
- every filesystem test uses isolated tmp_path
- compatible with pytest-xdist

WARNING — local-binding caveat:
Patching app.infrastructure.paths only affects dynamic lookups.
Modules importing symbols via:

    from app.infrastructure.paths import uploads_dir

create local bindings. Tests exercising those modules MUST additionally
patch the consumer-module symbol directly:

    monkeypatch.setattr(
        "app.api.routes.config.uploads_dir",
        lambda: uploads,
    )
"""

from __future__ import annotations

import pytest

from app.infrastructure import paths


@pytest.fixture
def isolated_paths(monkeypatch, tmp_path):
    """Explicit filesystem isolation fixture.

    Only tests that touch filesystem should request this fixture.

    Patches only source-module symbols. Consumer-module local bindings
    still require explicit patching per test.
    """
    uploads = tmp_path / "uploads"
    exports = tmp_path / "exports"
    logs = tmp_path / "logs"
    for directory in (uploads, exports, logs):
        directory.mkdir(exist_ok=True)
    monkeypatch.setattr(paths, "db_path", lambda: tmp_path / "automacao.db")
    monkeypatch.setattr(paths, "uploads_dir", lambda: uploads)
    monkeypatch.setattr(paths, "exports_dir", lambda: exports)
    monkeypatch.setattr(paths, "logs_dir", lambda: logs)
    return tmp_path
