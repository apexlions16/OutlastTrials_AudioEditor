# Modular Architecture

The original 18,698-line `OutlastTrialsAudioEditor.py` remains as a small,
backward-compatible launcher. Application code now lives in the
`outlast_trials_audio_editor` package.

## Layers

- `common.py`: shared third-party imports, platform flags, version, and application root.
- `i18n/`: built-in translation data.
- `models.py`: lightweight data models.
- `debug.py`: logging, debug window, and exception hooks.
- `services/`: BNK/WEM/audio/localization/settings logic.
- `workers.py`: background QThread workers.
- `profiles.py`: profile management and mod import workflow.
- `ui/widgets.py`: reusable widgets.
- `ui/audio_dialogs.py`: trim and volume dialogs.
- `ui/mixins/`: functional slices of the former 9,800-line main window.
- `ui/main_window.py`: the concrete Qt window, Qt slots, and lifecycle methods.
- `app.py`: process startup and splash-screen flow.

Qt-decorated slots intentionally remain on `WemSubtitleApp`, rather than in pure
Python mixins, to preserve PyQt meta-object registration and queued invocation.

The historical command remains valid:

```bash
python OutlastTrialsAudioEditor.py
```
