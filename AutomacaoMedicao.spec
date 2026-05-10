# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — AutomacaoMedicao (FastAPI desktop bundle).

Entrypoint: `app/desktop_entry.py` — sobe uvicorn em 127.0.0.1:8000 e abre
o navegador padrão na SPA servida via StaticFiles por `app/api/main.py`.

Bundled assets:
  - `app/ui/web/dist/` — build do frontend Vite servido como StaticFiles.
  - Bases de dados (treinamentos, cobrança, distribuição, tags) são
    registradas em runtime via UI — não há bootstrap por arquivo bundled.
"""

import os
from PyInstaller.utils.hooks import collect_submodules

_WEB_DIST = 'app/ui/web/dist'

_datas = []
if os.path.isdir(_WEB_DIST):
    _datas.append((_WEB_DIST, 'app/ui/web/dist'))
else:
    print(
        f"[spec] AVISO: '{_WEB_DIST}' ausente — rode `npm run build` em "
        "app/ui/web/ antes de empacotar para que a SPA seja servida."
    )

try:
    import webview  # noqa: F401
except ImportError as exc:
    raise SystemExit(
        "[spec] pywebview não instalado no venv de build. "
        "Rode `pip install -e .` (ou `pip install pywebview==5.4`) antes "
        "de empacotar — sem ele o .exe levanta ModuleNotFoundError em runtime."
    ) from exc

_uvicorn_hidden  = collect_submodules('uvicorn')
_openpyxl_hidden = collect_submodules('openpyxl')
_fastapi_hidden  = collect_submodules('fastapi')
_webview_hidden  = collect_submodules('webview')

a = Analysis(
    ['app/desktop_entry.py'],
    pathex=['.'],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        'app',
        'app.api.main',
        'app.cli',
        'app.cli.validar_hr',
        'sqlite3',
        *_uvicorn_hidden,
        *_openpyxl_hidden,
        *_fastapi_hidden,
        *_webview_hidden,
        'webview.platforms.edgechromium',
        'proxy_tools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AutomacaoMedicao',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
