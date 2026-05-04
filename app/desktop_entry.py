"""Desktop entrypoint — launches the FastAPI app via uvicorn and opens the browser.

Used as the PyInstaller spec script. The bundled .exe starts uvicorn on a
local port, then opens the default browser pointed at the SPA served by
StaticFiles. Closing the browser does not terminate the server; the user
closes the console window (or signals the process) to stop.
"""

from __future__ import annotations

import threading
import time
import webbrowser

import uvicorn

from app.api.main import app

_HOST = "127.0.0.1"
_PORT = 8000


def _abrir_navegador_quando_pronto() -> None:
    time.sleep(1.2)
    webbrowser.open(f"http://{_HOST}:{_PORT}/")


def main() -> None:
    threading.Thread(target=_abrir_navegador_quando_pronto, daemon=True).start()
    uvicorn.run(app, host=_HOST, port=_PORT, log_level="info")


if __name__ == "__main__":
    main()
