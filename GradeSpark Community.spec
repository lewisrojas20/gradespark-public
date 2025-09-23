# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gradespark_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('demo_data', 'demo_data'), ('assets', 'assets'), ('styles.qss', '.'), ('styles_dark.qss', '.')],
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
    [],
    exclude_binaries=True,
    name='GradeSpark Community',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GradeSpark Community',
)
app = BUNDLE(
    coll,
    name='GradeSpark Community.app',
    icon=None,
    bundle_identifier=None,
)
