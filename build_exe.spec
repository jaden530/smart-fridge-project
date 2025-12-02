# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Build Configuration for Smart Fridge
================================================

This creates a Windows .exe that bundles everything:
- Python interpreter
- All dependencies
- Models and data files
- UI templates

Usage:
    pyinstaller build_exe.spec

Output:
    dist/SmartFridge.exe (double-click to run!)
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all data files
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('model_data', 'model_data'),
    ('.env', '.'),
]

# Collect hidden imports (packages PyInstaller might miss)
hiddenimports = [
    'ultralytics',
    'face_recognition',
    'dlib',
    'cv2',
    'numpy',
    'flask',
    'sqlalchemy',
    'werkzeug',
] + collect_submodules('ultralytics')

# Analysis
a = Analysis(
    ['src/launcher.py'],  # Main entry point
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove unnecessary files to reduce size
a.datas = [x for x in a.datas if not x[0].startswith('matplotlib')]
a.datas = [x for x in a.datas if not x[0].startswith('PIL')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SmartFridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console for debugging (change to False for release)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/icon.ico' if os.path.exists('static/icon.ico') else None,
)
