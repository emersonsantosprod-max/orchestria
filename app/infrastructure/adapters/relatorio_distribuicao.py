"""salvar_relatorio_distribuicao: escreve relatório txt em saida_dir()."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.infrastructure.paths import saida_dir


def salvar_relatorio(conteudo: str) -> Path:
    destino = saida_dir()
    destino.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    caminho = destino / f'relatorio_validacao_distribuicao_{ts}.txt'
    caminho.write_text(conteudo, encoding='utf-8')
    return caminho
