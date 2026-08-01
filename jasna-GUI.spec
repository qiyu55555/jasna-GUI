# -*- mode: python ; coding: utf-8 -*-

import os
import pymediainfo

# 获取pymediainfo包目录，用于打包MediaInfo.dll
_pymediainfo_dir = os.path.dirname(pymediainfo.__file__)
_mediainfo_dll = os.path.join(_pymediainfo_dir, 'MediaInfo.dll')

# pymediainfo库在加载时会从 os.path.dirname(__file__) 即pymediainfo包目录中查找MediaInfo.dll
# 因此需要将MediaInfo.dll放到pymediainfo子目录中，而不是根目录
_pymediainfo_binaries = []
if os.path.exists(_mediainfo_dll):
    _pymediainfo_binaries.append((_mediainfo_dll, 'pymediainfo'))


a = Analysis(
    ['jasna-GUI.py'],
    pathex=[],
    binaries=_pymediainfo_binaries,
    datas=[('jasna-v2-T-256.ico', '.')],  # 包含图标文件
    hiddenimports=['pymediainfo'],
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
    name='jasna-GUI-v9.2',
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
