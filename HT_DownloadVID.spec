# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['App.py'],
    pathex=[],
    binaries=[('ffmpeg/ffmpeg.exe', 'ffmpeg'), ('venv/Scripts/yt-dlp.exe', '.')],
    datas=[],
    hiddenimports=['subprocess'],
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
    name='HT_DownloadVID',
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
