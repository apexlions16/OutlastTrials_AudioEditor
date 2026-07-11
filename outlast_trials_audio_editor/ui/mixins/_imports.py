"""Shared imports for mechanically extracted main-window mixins."""

from ...common import *
from ...debug import DEBUG, DebugWindow
from ...easter_egg import EasterEggLoader
from ...i18n import TRANSLATIONS
from ...profiles import ProfileDialog, ProfileManagerDialog
from ...services.audio import AudioPlayer, AudioToWavConverter, WEMAnalyzer, WavToWemConverter
from ...services.bnk import BNKEditor, BnkInfoLoader
from ...services.localization import SaveSubtitlesThread, SubtitleEditor, SubtitleLoaderThread, UnrealLocresManager
from ...services.settings import AppSettings
from ...workers import (
    AddFilesThread,
    AddSingleFileThread,
    CompileModThread,
    DropFilesThread,
    ResourceUpdaterThread,
    WemScannerThread,
)
from ..audio_dialogs import AudioTrimDialog, BatchVolumeEditDialog, WemVolumeEditDialog
from ..widgets import AudioTreeWidget, ClickableProgressBar, ModernButton, ProgressDialog, SearchBar
