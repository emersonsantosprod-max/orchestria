"""Desktop entrypoint — launches FastAPI via uvicorn dentro de um webview nativo.

PyInstaller spec script. O bundled .exe sobe uvicorn em thread, abre uma
janela pywebview apontando para a SPA local e expõe `JsApi` como bridge
JS-Python para diálogos nativos do SO (selecionar arquivo).

Frontend acessa via `window.pywebview.api.escolher_arquivo(titulo)`.

Em desenvolvimento (`make dev`), pywebview pode não estar disponível;
nesse caso o entrypoint cai no fallback `webbrowser.open()` com aviso
no log. Em build empacotado pywebview é mandatório (sem fallback
silencioso — falha terminal se ausente).
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time

import uvicorn

from app.api.main import app

logger = logging.getLogger(__name__)

_HOST = "127.0.0.1"
_PORT = 8000


class JsApi:
    """Bridge JS→Python exposto pela janela pywebview.

    Cada método público é exposto como `window.pywebview.api.<nome>` no
    JavaScript da SPA. Mantenha mínimo e síncrono — métodos longos
    bloqueiam a janela.
    """

    def escolher_arquivo(self, titulo: str = "Selecionar arquivo") -> str | None:
        """Abre dialog nativo do SO; retorna path absoluto ou None."""
        import webview

        wins = webview.windows
        if not wins:
            return None
        result = wins[0].create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=(
                "Excel/SQLite (*.xlsx;*.xls;*.sqlite;*.db)",
                "Todos os arquivos (*.*)",
            ),
        )
        if not result:
            return None
        return result[0]


def _run_uvicorn() -> None:
    uvicorn.run(app, host=_HOST, port=_PORT, log_level="info")


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def main() -> None:
    threading.Thread(target=_run_uvicorn, daemon=True).start()
    time.sleep(1.2)  # dar tempo ao uvicorn ficar pronto

    try:
        import webview  # type: ignore[import-not-found]
    except ImportError:
        if _is_frozen():
            sys.stderr.write(
                "[fatal] pywebview indisponível em build empacotado.\n"
            )
            raise
        logger.warning(
            "pywebview indisponível — fallback webbrowser.open() (dev only)"
        )
        import webbrowser
        webbrowser.open(f"http://{_HOST}:{_PORT}/")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            return
        return

    webview.create_window(
        "Automação de Medição",
        f"http://{_HOST}:{_PORT}/",
        js_api=JsApi(),
        width=1280,
        height=820,
    )
    webview.start(debug=bool(os.environ.get("AUTOMACAO_WEBVIEW_DEBUG")))


if __name__ == "__main__":
    main()
