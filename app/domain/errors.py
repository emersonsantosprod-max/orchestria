"""
errors.py — Hierarquia de exceções do domínio.

Boundary entre pipeline/loaders (levantam) e UI/CLI (traduzem para
mensagens legíveis ao usuário não-técnico).
"""

from __future__ import annotations


class AutomacaoError(Exception):
    """Base para toda exceção esperada do domínio."""


class ArquivoNaoEncontradoError(AutomacaoError):
    """Caminho de entrada não existe no filesystem."""


class ArquivoAbertoError(AutomacaoError):
    """Arquivo está em uso por outro processo (Excel aberto, lock, etc.)."""


class PlanilhaInvalidaError(AutomacaoError):
    """Planilha não tem a estrutura esperada (sheet ausente, coluna faltando,
    cabeçalho inválido)."""


class ConversaoArquivoError(AutomacaoError):
    """Falha ao converter .xls → .xlsx ou similar."""
