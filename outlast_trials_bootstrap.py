"""Failure-visible bootstrap for source and PyInstaller entry points."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _report_startup_failure(details: str) -> None:
    root = _runtime_root()
    log_path = root / "startup_crash.log"
    try:
        log_path.write_text(details, encoding="utf-8")
    except OSError:
        pass

    message = (
        "OutlastTrials AudioEditor başlatılamadı.\n\n"
        f"Ayrıntılar şu dosyaya yazıldı:\n{log_path}\n\n"
        f"{details[-2500:]}"
    )
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                None,
                message,
                "OutlastTrials AudioEditor — Başlatma Hatası",
                0x10,
            )
            return
        except Exception:
            pass
    print(message, file=sys.stderr)


def run() -> int:
    smoke_test = "--smoke-test" in sys.argv
    if smoke_test:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    try:
        if smoke_test:
            from outlast_trials_audio_editor.smoke_test import run_smoke_test

            return run_smoke_test()

        from outlast_trials_audio_editor.app import main

        result = main()
        return result if isinstance(result, int) else 0
    except SystemExit:
        raise
    except BaseException:
        _report_startup_failure(traceback.format_exc())
        return 1
