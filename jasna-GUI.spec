# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['jasna-GUI.py'],
    pathex=[],
    binaries=[],
    datas=[('jasna-v2-T-256.ico', '.')],  # 包含图标文件
    hiddenimports=[],
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
    name='jasna-GUI-v6.0',
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
    icon=['jasna-v2-T-256.ico'],
)
