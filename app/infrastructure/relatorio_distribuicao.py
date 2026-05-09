"""salvar_relatorio: escreve relatório txt em exports_dir()."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.infrastructure.paths import exports_dir


def salvar_relatorio(conteudo: str) -> Path:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    caminho = exports_dir() / f'relatorio_validacao_distribuicao_{ts}.txt'
    caminho.write_text(conteudo, encoding='utf-8')
    return caminho
