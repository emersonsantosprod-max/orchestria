"""Coleta de métricas estáticas (lines, functions, oversized) via AST."""

from __future__ import annotations

import ast
from pathlib import Path


def contar_metricas_arquivo(source: str) -> tuple[int, int]:
    linhas = sum(
        1 for raw in source.splitlines()
        if (s := raw.strip()) and not s.startswith('#')
    )
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return linhas, 0
    funcoes = sum(
        1 for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    return linhas, funcoes


def coletar_metricas_codigo(paths: list[Path], limite_linhas: int = 500) -> dict:
    total_linhas = 0
    total_funcoes = 0
    oversized = 0
    for raiz in paths:
        for arquivo in raiz.rglob('*.py'):
            if any(part.startswith(('.', '__pycache__', 'venv')) for part in arquivo.parts):
                continue
            source = arquivo.read_text(encoding='utf-8')
            linhas, funcoes = contar_metricas_arquivo(source)
            total_linhas += linhas
            total_funcoes += funcoes
            if sum(1 for _ in source.splitlines()) > limite_linhas:
                oversized += 1
    return {
        'lines': total_linhas,
        'functions': total_funcoes,
        'oversized_files': oversized,
    }
