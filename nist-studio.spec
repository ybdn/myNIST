# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for NIST Studio application.

Optimized for 'onefolder' mode for fast startup times.
- Linux/Windows: COLLECT (folder with executable)
- macOS: BUNDLE (.app bundle for better Gatekeeper compatibility)
"""

import sys
from pathlib import Path

block_cipher = None

# Data files to bundle
datas_list = [
    ('mynist/resources', 'mynist/resources'),
]

# Include NBIS binaries if present (built by CI or manually)
nbis_bin = Path('nbis/bin')
if nbis_bin.exists():
    datas_list.append(('nbis/bin', 'nbis/bin'))

# Essential hidden imports - only what's actually used
hiddenimports = [
    # NIST file parsing
    'nistitl',
    # PyQt5 GUI (core modules only)
    'PyQt5.sip',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtSvg',
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
]

# Aggressive exclusions for smaller bundle and faster load
excludes = [
    # Data science (not used)
    'matplotlib',
    'pandas',
    'scipy',
    'numpy.testing',
    'numpy.f2py',
    'numpy.distutils',
    'numpy.doc',
    'numpy.core.tests',
    # GUI toolkits (not used)
    'tkinter',
    '_tkinter',
    'tcl',
    'tk',
    # PyQt5 modules not used
    'PyQt5.QtDesigner',
    'PyQt5.QtQml',
    'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets',
    'PyQt5.QtNetwork',
    'PyQt5.QtMultimedia',
    'PyQt5.QtMultimediaWidgets',
    'PyQt5.QtBluetooth',
    'PyQt5.QtPositioning',
    'PyQt5.QtLocation',
    'PyQt5.QtWebChannel',
    'PyQt5.QtWebEngine',
    'PyQt5.QtWebEngineCore',
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtWebSockets',
    'PyQt5.QtXml',
    'PyQt5.QtXmlPatterns',
    'PyQt5.QtHelp',
    'PyQt5.QtSql',
    'PyQt5.QtTest',
    'PyQt5.QtDBus',
    'PyQt5.QtSensors',
    'PyQt5.QtSerialPort',
    'PyQt5.QtNfc',
    'PyQt5.QtRemoteObjects',
    'PyQt5.QtTextToSpeech',
    'PyQt5.Qt3DCore',
    'PyQt5.Qt3DExtras',
    'PyQt5.Qt3DInput',
    'PyQt5.Qt3DLogic',
    'PyQt5.Qt3DRender',
    'PyQt5.QtOpenGL',
    # Development/test modules
    'unittest',
    'test',
    'tests',
    '_pytest',
    'pytest',
    'doctest',
    'pdb',
    'pydoc',
    # Build/packaging tools
    'setuptools',
    'pip',
    'wheel',
    'pkg_resources',
    'distutils',
    # IPython/Jupyter
    'IPython',
    'ipykernel',
    'jupyter',
    'notebook',
    # Unused standard library
    'xmlrpc',
    'lib2to3',
    'curses',
    'asyncio',
    'multiprocessing',
    'concurrent',
]

a = Analysis(
    ['mynist/__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    icns_path = Path('mynist/resources/icons/appicon-nist-studio.icns')
    icon_path = str(icns_path) if icns_path.exists() else None
else:
    icon_path = 'mynist/resources/icons/appicon-nist-studio-256.png'

# EXE configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='nist-studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

# Platform-specific packaging
if sys.platform == 'darwin':
    # macOS: Create .app bundle for better Gatekeeper compatibility
    app = BUNDLE(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='NIST-Studio.app',
        icon=icon_path,
        bundle_identifier='com.niststudio.app',
        info_plist={
            'CFBundleName': 'NIST Studio',
            'CFBundleDisplayName': 'NIST Studio',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13.0',
            'NSRequiresAquaSystemAppearance': False,
        },
    )
else:
    # Linux/Windows: Create folder distribution
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name='NIST-Studio',
    )
