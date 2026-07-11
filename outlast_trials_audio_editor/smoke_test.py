"""Packaged-application startup check used by Windows CI builds."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def run_smoke_test() -> int:
    """Import the public API, create the main window, then exit immediately.

    The test intentionally avoids profile initialization and game-file scanning,
    because those require a local The Outlast Trials installation. It still
    exercises the packaged Python runtime, Qt plugins, all public modules, the
    application data path, and main-window construction.
    """

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    root = _runtime_root()
    log_path = root / "packaging_smoke_test.log"

    try:
        required = (
            root / "data" / "splash.png",
            root / "data" / "repak.exe",
            root / "data" / "UnrealLocres.exe",
            root / "data" / "ffmpeg.exe",
            root / "data" / "vgmstream" / "vgmstream-cli.exe",
        )
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise FileNotFoundError("Paket dosyaları eksik:\n" + "\n".join(missing))

        import outlast_trials_audio_editor as public_api
        from PyQt5 import QtWidgets

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(
            ["OutlastTrialsAudioEditor", "--smoke-test"]
        )
        window = public_api.WemSubtitleApp()
        window.close()
        app.processEvents()

        log_path.write_text("OK\n", encoding="utf-8")
        return 0
    except BaseException:
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        return 1
