# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for NIST Studio application."""

import sys
from pathlib import Path

block_cipher = None

datas_list = [
    ('mynist/resources', 'mynist/resources'),
]

# Include NBIS binaries if present (built by CI or manually)
nbis_bin = Path('nbis/bin')
if nbis_bin.exists():
    datas_list.append(('nbis/bin', 'nbis/bin'))

a = Analysis(
    ['mynist/__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        # NIST file parsing
        'nistitl',
        # PyQt5 GUI
        'PyQt5.sip',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtSvg',  # Used for SVG icons
        # Pillow image processing
        'PIL',
        'PIL.Image',
        'PIL.ImageOps',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.ImageEnhance',
        # JPEG2000 decoding
        'imagecodecs',
        # WSQ decoding (fingerprint images)
        'wsq',
        'wsq.WsqImagePlugin',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'pandas',
        'scipy',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Determine icon path based on OS
if sys.platform == 'win32':
    icon_path = 'mynist/resources/icons/appicon-nist-studio.ico'
elif sys.platform == 'darwin':
    # macOS requires .icns for proper dock icon display
    icns_path = Path('mynist/resources/icons/appicon-nist-studio.icns')
    icon_path = str(icns_path) if icns_path.exists() else None
else:
    icon_path = 'mynist/resources/icons/appicon-nist-studio-256.png'

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='nist-studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Disabled: strip causes issues on Windows
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
