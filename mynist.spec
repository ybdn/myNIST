# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for myNIST application."""

from pathlib import Path

block_cipher = None

datas_list = [
    ('mynist/resources', 'mynist/resources'),
]

# Inclure les binaires NBIS s'ils sont présents dans le repo (nbis/ ou nbis/bin).
nbis_dir = Path('nbis')
if nbis_dir.exists():
    datas_list.append(('nbis', 'nbis'))

a = Analysis(
    ['mynist/__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'nistitl',
        'PyQt5.sip',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PIL',
        'PIL.Image',
        'wsq',
        'wsq.WsqImagePlugin',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mynist',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip symbols to reduce size (Ubuntu optimization)
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='mynist/resources/icons/appicon-nist-studio.ico',  # Application icon
)
