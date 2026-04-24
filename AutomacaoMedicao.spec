# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — AutomacaoMedicao.

Bundled assets:
  - `assets/distribuicao_contratual_normalizada.xlsx` é source-of-truth
    versionado (repo privado) e empacotado via PyInstaller `datas=`.
  - `assets/base_treinamentos.xlsx` é source-of-truth da tabela de tipos
    de treinamentos; empacotado via PyInstaller `datas=`.
  - Se ausentes no build, os bundles são gerados sem eles e os bootstraps
    idempotentes detectam a ausência em runtime.
"""

import os
from PyInstaller.utils.hooks import collect_all

# collect_all emits a "font_shapes / circle_shapes / rendering quality will be bad"
# warning during PyInstaller analysis when building from WSL2. This is expected:
# the build runs via venv_win (a Windows PE32 executable), which calls GDI32
# AddFontResourceExW with a \\wsl$ UNC path — GDI32 cannot load fonts from network
# paths at analysis time. At runtime the .exe extracts to %TEMP% (a local path)
# and font loading succeeds normally. No fonts are missing from the bundle.
_ctk_datas, _ctk_binaries, _ctk_hiddenimports = collect_all('customtkinter')

_DIST_XLSX  = 'assets/distribuicao_contratual_normalizada.xlsx'
_TRAIN_XLSX = 'assets/base_treinamentos.xlsx'
_datas = [*_ctk_datas]
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

a = Analysis(
    ['ui/gui.py'],
    pathex=['.'],
    binaries=[*_ctk_binaries],
    datas=_datas,
    hiddenimports=['app', 'app.cli', 'app.cli.validar_hr', 'darkdetect', *_ctk_hiddenimports],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
