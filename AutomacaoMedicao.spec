# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — AutomacaoMedicao (FastAPI desktop bundle).

Entrypoint: `app/desktop_entry.py` — sobe uvicorn em 127.0.0.1:8000 e abre
o navegador padrão na SPA servida via StaticFiles por `app/api/main.py`.

Bundled assets:
  - `assets/distribuicao_contratual_normalizada.xlsx` — SSOT versionado
    para bootstrap idempotente da distribuição contratual.
  - `assets/base_treinamentos.xlsx` — SSOT da base de tipos de treinamento.
  - `ui/web/dist/` — build do frontend Vite servido como StaticFiles.
  - Se qualquer um estiver ausente, o build prossegue e o respectivo
    bootstrap detecta a ausência em runtime.
"""

import os
from PyInstaller.utils.hooks import collect_submodules

_DIST_XLSX  = 'assets/distribuicao_contratual_normalizada.xlsx'
_TRAIN_XLSX = 'assets/base_treinamentos.xlsx'
_WEB_DIST   = 'ui/web/dist'

_datas = []
if os.path.exists(_DIST_XLSX):
    _datas.append((_DIST_XLSX, 'assets'))
else:
    print(
        f"[spec] AVISO: '{_DIST_XLSX}' ausente — build prosseguirá sem "
        "o xlsx de bootstrap. Distribuição contratual deverá ser "
        "registrada em runtime."
    )
if os.path.exists(_TRAIN_XLSX):
    _datas.append((_TRAIN_XLSX, 'assets'))
else:
    print(
        f"[spec] AVISO: '{_TRAIN_XLSX}' ausente — build prosseguirá sem "
        "o xlsx de bootstrap. Base de treinamentos deverá ser "
        "importada manualmente em runtime."
    )
if os.path.isdir(_WEB_DIST):
    _datas.append((_WEB_DIST, 'ui/web/dist'))
else:
    print(
        f"[spec] AVISO: '{_WEB_DIST}' ausente — rode `npm run build` em "
        "ui/web/ antes de empacotar para que a SPA seja servida."
    )

_uvicorn_hidden = collect_submodules('uvicorn')

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
        *_uvicorn_hidden,
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
