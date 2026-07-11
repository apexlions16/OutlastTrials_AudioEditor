"""Backward-compatible launcher for OutlastTrials AudioEditor."""

if __name__ == "__main__":
    from outlast_trials_bootstrap import run

    raise SystemExit(run())

# Preserve the historical import surface for third-party scripts.
from outlast_trials_audio_editor import *  # noqa: F401,F403,E402
