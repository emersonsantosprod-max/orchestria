"""Detecção de clones Tipo-2 via janela deslizante de tokens (stdlib only)."""

from __future__ import annotations

import io
import token as _token
import tokenize
from collections import Counter
from pathlib import Path

WINDOW = 50
_IGNORADOS = {
    _token.COMMENT, _token.NL, _token.NEWLINE, _token.INDENT,
    _token.DEDENT, _token.ENCODING, _token.ENDMARKER,
}


def _tokens_normalizados(source: str) -> list[tuple[int, str]]:
    saida: list[tuple[int, str]] = []
    try:
        for tok in tokenize.tokenize(io.BytesIO(source.encode('utf-8')).readline):
            if tok.type in _IGNORADOS:
                continue
            if tok.type == _token.NAME:
                saida.append((_token.NAME, ''))
            else:
                saida.append((tok.type, tok.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return []
    return saida


def contar_duplicacoes(paths: list[Path], janela: int = WINDOW) -> int:
    contagem: Counter[tuple] = Counter()
    for raiz in paths:
        for arquivo in raiz.rglob('*.py'):
            if any(p.startswith(('.', '__pycache__', 'venv')) for p in arquivo.parts):
                continue
            source = arquivo.read_text(encoding='utf-8', errors='replace')
            tokens = _tokens_normalizados(source)
            if len(tokens) < janela:
                continue
            for i in range(len(tokens) - janela + 1):
                contagem[tuple(tokens[i:i + janela])] += 1
    return sum(c - 1 for c in contagem.values() if c > 1)
