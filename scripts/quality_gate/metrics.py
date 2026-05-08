"""Coleta de métricas estáticas (lines, functions, oversized) via AST."""

from __future__ import annotations

import ast
from pathlib import Path


def contar_metricas_arquivo(source: str) -> tuple[int, int, int]:
    linhas = sum(
        1 for raw in source.splitlines()
        if (s := raw.strip()) and not s.startswith('#')
    )
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return linhas, 0, 0
    funcoes = sum(
        1 for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    statements = sum(
        1 for node in ast.walk(tree)
        if isinstance(node, ast.stmt)
    )
    return linhas, funcoes, statements


def contar_branches_arquivo(source: str) -> int:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0
    branches = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While,
                             ast.Try, ast.ExceptHandler, ast.IfExp,
                             ast.match_case)):
            branches += 1
        elif isinstance(node, ast.BoolOp):
            branches += 1
        elif isinstance(node, ast.comprehension):
            branches += len(node.ifs)
    return branches


def coletar_metricas_codigo(paths: list[Path], limite_linhas: int = 500) -> dict:
    total_linhas = 0
    total_funcoes = 0
    total_statements = 0
    total_branches = 0
    oversized = 0
    for raiz in paths:
        for arquivo in raiz.rglob('*.py'):
            if any(part.startswith(('.', '__pycache__', 'venv')) for part in arquivo.parts):
                continue
            source = arquivo.read_text(encoding='utf-8')
            linhas, funcoes, statements = contar_metricas_arquivo(source)
            total_linhas += linhas
            total_funcoes += funcoes
            total_statements += statements
            total_branches += contar_branches_arquivo(source)
            if sum(1 for _ in source.splitlines()) > limite_linhas:
                oversized += 1
    return {
        'lines': total_linhas,
        'functions': total_funcoes,
        'statements': total_statements,
        'branches': total_branches,
        'oversized_files': oversized,
    }
