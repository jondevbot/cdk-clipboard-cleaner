# PyInstaller spec — Windows onefile, no Qt, windowed (no console flash).
# CLI sidecars stay onefile (wine-pyside-windows-bundle).

a = Analysis(
    ["run_app.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["app", "app.cleaner", "app.clipboard_win", "app.main"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "pydoc_data",
        "PySide6",
        "PyQt5",
        "PyQt6",
        "numpy",
        "PIL",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CDK_Clipboard_Cleaner",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
