"""Wrapper sobre `ruff check --output-format=json`."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def contar_violacoes_ruff(paths: list[Path]) -> int:
    cmd = ['ruff', 'check', '--output-format=json', *(str(p) for p in paths)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if not proc.stdout.strip():
        return 0
    try:
        items = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return 0
    return len(items)
