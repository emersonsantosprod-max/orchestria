"""
logging_config.py — bootstrap único de logging em arquivo.

Resolve o destino via app.paths.logs_dir() (frozen-aware). RotatingFileHandler
mantém histórico compacto (5 arquivos × 1 MiB). Idempotente: chamadas
repetidas não duplicam handlers.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.paths import logs_dir

_FORMAT = '%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s'
_HANDLER_TAG = '_automacao_file_handler'


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    root = logging.getLogger()
    root.setLevel(level)

    for h in root.handlers:
        if getattr(h, _HANDLER_TAG, False):
            return root

    destino = logs_dir()
    destino.mkdir(parents=True, exist_ok=True)
    arquivo = destino / 'automacao.log'

    handler = RotatingFileHandler(
        arquivo, maxBytes=1024 * 1024, backupCount=5, encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter(_FORMAT))
    setattr(handler, _HANDLER_TAG, True)
    root.addHandler(handler)
    return root
