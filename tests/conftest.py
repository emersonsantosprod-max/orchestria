"""
Filesystem isolation for tests.

Parallel-safe rules:
- no assertions against repo-global filesystem state
- no shared temp directories
- every filesystem test uses isolated tmp_path
- compatible with pytest-xdist

WARNING — local-binding caveat:
Patching `app.infrastructure.paths` afeta apenas lookups dinâmicos.
Módulos que importam símbolos via `from app.infrastructure.paths import X`
criam binding local — testes precisam patchear o símbolo do consumer
explicitamente quando relevante.
"""

from __future__ import annotations

import pytest

from app.infrastructure import paths


@pytest.fixture
def isolated_paths(monkeypatch, tmp_path):
    """Explicit filesystem isolation fixture.

    Patches só symbols source-module. Consumer-module local bindings
    ainda precisam patch per-test.
    """
    exports = tmp_path / "exports"
    logs = tmp_path / "logs"
    for directory in (exports, logs):
        directory.mkdir(exist_ok=True)
    monkeypatch.setattr(paths, "db_path", lambda: tmp_path / "automacao.db")
    monkeypatch.setattr(paths, "exports_dir", lambda: exports)
    monkeypatch.setattr(paths, "logs_dir", lambda: logs)
    return tmp_path
