# -*- mode: python ; coding: utf-8 -*-
"""Reliable one-folder Windows build for OutlastTrials AudioEditor."""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

project_root = Path(SPECPATH)
app_version = os.environ.get("APP_VERSION", "v1.2.1")
dist_name = f"OutlastTrialsAudioEditor_{app_version}_Windows_x64"

datas = [(str(project_root / "data"), "data")]
binaries = []
hiddenimports = [
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "PyQt5.QtMultimedia",
    "matplotlib.backends.backend_agg",
    "scipy.io.wavfile",
    "outlast_trials_audio_editor.smoke_test",
    "outlast_trials_bootstrap",
]

for package in ("numpy", "scipy", "matplotlib", "psutil"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

analysis = Analysis(
    [str(project_root / "OutlastTrialsAudioEditor.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="OutlastTrials AudioEditor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(project_root / "data" / "app_icon.ico"),
    contents_directory=".",
)

collection = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=dist_name,
)
