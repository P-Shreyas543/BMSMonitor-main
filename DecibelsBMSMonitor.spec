# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Shreyas\\Documents\\Python\\BMSMonitor-main\\BMS_Monitor.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Shreyas\\Documents\\Python\\BMSMonitor-main\\version.json', '.'), ('C:\\Users\\Shreyas\\Documents\\Python\\BMSMonitor-main\\logo_sq.ico', '.'), ('C:\\Users\\Shreyas\\Documents\\Python\\BMSMonitor-main\\logo_sq.png', '.'), ('C:\\Users\\Shreyas\\Documents\\Python\\BMSMonitor-main\\logo_rec.png', '.')],
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
    name='DecibelsBMSMonitor',
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
    icon=['C:\\Users\\Shreyas\\Documents\\Python\\BMSMonitor-main\\logo_sq.ico'],
)
