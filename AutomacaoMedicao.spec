# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — AutomacaoMedicao.

Bundled asset:
  - `assets/distribuicao_contratual_normalizada.xlsx` é source-of-truth
    versionado (repo privado) e empacotado via PyInstaller `datas=`.
  - Se ausente no build, o bundle é gerado sem ele e
    `db.popular_bd_se_vazio()` detecta a ausência em runtime — o fluxo
    de validação solicita o arquivo ao usuário via GUI/CLI.
"""

import os
from PyInstaller.utils.hooks import collect_all

_ctk_datas, _ctk_binaries, _ctk_hiddenimports = collect_all('customtkinter')

_DIST_XLSX = 'assets/distribuicao_contratual_normalizada.xlsx'
_datas = [*_ctk_datas]
if os.path.exists(_DIST_XLSX):
    _datas.append((_DIST_XLSX, 'assets'))
else:
    print(
        f"[spec] AVISO: '{_DIST_XLSX}' ausente — build prosseguirá sem "
        "o xlsx de bootstrap. Distribuição contratual deverá ser "
        "registrada em runtime."
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
