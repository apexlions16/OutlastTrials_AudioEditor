"""Shared runtime imports and application-wide constants.

This module intentionally centralizes the broad dependency surface inherited from
upstream's former single-file layout. Feature modules import from here while the
refactor is stabilized; dependencies can be narrowed incrementally later.
"""

import sys
import os
import json
import subprocess
import tempfile
import shutil
import threading
import csv
import traceback
import time
import requests
from packaging import version
from functools import partial
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia
from PyQt5.QtCore import QObject, pyqtSignal
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import struct
from collections import namedtuple
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    import numpy as np
    import scipy.io.wavfile as wavfile
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    text = str(ImportError)
    MATPLOTLIB_AVAILABLE = False
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
CuePoint = namedtuple('CuePoint', ['id', 'position', 'chunk_id', 'chunk_start', 'block_start', 'sample_offset'])
Label = namedtuple('Label', ['id', 'text'])

if sys.platform == "win32":
    import subprocess
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    CREATE_NO_WINDOW = 0x08000000
else:
    startupinfo = None
    CREATE_NO_WINDOW = 0
current_version = "v1.2.1"

PACKAGE_ROOT = Path(__file__).resolve().parent
APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PACKAGE_ROOT.parent
