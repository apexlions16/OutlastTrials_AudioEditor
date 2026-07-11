from ..common import *
from ..debug import DEBUG

class ModernButton(QtWidgets.QPushButton):
    def __init__(self, text="", icon=None, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setProperty("primary", primary)
        if icon:
            self.setIcon(QtGui.QIcon(icon))
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setMinimumHeight(36)

class AudioTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent=None, wem_app=None, lang=None):
        super().__init__(parent)
        self.wem_app = wem_app
        self.lang = lang
        self._highlighted_item = None
        self._highlighted_brush = QtGui.QBrush(QtGui.QColor(255, 255, 180))
    def keyPressEvent(self, event):
        """Handle key presses for audio playback and other actions."""
        key = event.key()
        modifiers = event.modifiers()

        if key == QtCore.Qt.Key_Space and modifiers == QtCore.Qt.NoModifier:
            if self.wem_app:
                self.wem_app.play_current(play_mod=False)
            event.accept()

        elif key == QtCore.Qt.Key_Space and modifiers == QtCore.Qt.ControlModifier:
            if self.wem_app:
                self.wem_app.play_current(play_mod=True)
            event.accept()

        elif key == QtCore.Qt.Key_Delete and modifiers == QtCore.Qt.NoModifier:
            if self.wem_app:
                self.wem_app.delete_current_mod_audio() 
            event.accept()
        else:
            super().keyPressEvent(event)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
           
            pos = event.pos()
            item = self.itemAt(pos)
            self._set_highlighted_item(item)
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self._set_highlighted_item(None)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._set_highlighted_item(None)
        if not event.mimeData().hasUrls():
            return super().dropEvent(event)
        urls = event.mimeData().urls()
        if not urls:
            return
        file_path = urls[0].toLocalFile()
        if not file_path.lower().endswith(('.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.opus', '.webm')):
            QtWidgets.QMessageBox.warning(self, self.tr("invalid_file_title"), self.tr("audio_only_drop_msg"))
            return
        pos = event.pos()
        item = self.itemAt(pos)
        if not item or item.childCount() > 0:
            QtWidgets.QMessageBox.information(self, self.tr("drop_audio_title"), self.tr("drop_on_file_msg"))
            return
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            return
        shortname = entry.get("ShortName", "")
        reply = QtWidgets.QMessageBox.question(
            self, self.tr("replace_audio_title"),
            self.tr("replace_audio_confirm_msg").format(shortname=shortname, filename=os.path.basename(file_path)),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            if self.wem_app:
                self.wem_app.quick_load_custom_audio(entry, self.lang, custom_file=file_path)
        event.acceptProposedAction()

    def _set_highlighted_item(self, item):
   
        if self._highlighted_item is not None:
            for col in range(self.columnCount()):
                self._highlighted_item.setBackground(col, QtGui.QBrush())
    
        self._highlighted_item = item
        if item is not None:
            for col in range(self.columnCount()):
                item.setBackground(col, self._highlighted_brush)

class SearchBar(QtWidgets.QWidget):
    searchChanged = QtCore.pyqtSignal(str)
    
    def __init__(self, placeholder_text=""):
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_icon = QtWidgets.QLabel("🔍")
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText(placeholder_text)
        self.clear_btn = QtWidgets.QPushButton("✕")
        self.clear_btn.setMaximumWidth(30)
        self.clear_btn.hide()
        
        layout.addWidget(self.search_icon)
        layout.addWidget(self.search_input)
        layout.addWidget(self.clear_btn)
        
        self.search_input.textChanged.connect(self._on_text_changed)
        self.clear_btn.clicked.connect(self.clear)
        
    def _on_text_changed(self, text):
        self.clear_btn.setVisible(bool(text))
        self.searchChanged.emit(text)
        
    def clear(self):
        self.search_input.clear()
        
    def text(self):
        return self.search_input.text()

class ProgressDialog(QtWidgets.QDialog):
    details_updated = QtCore.pyqtSignal(str)
    def __init__(self, parent=None, title="Processing..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        self.label = QtWidgets.QLabel("Please wait...")
        self.progress = QtWidgets.QProgressBar()
        self.details = QtWidgets.QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(100)
        
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        layout.addWidget(self.details)
        self.details_updated.connect(self.append_details)
    @QtCore.pyqtSlot(int, str)
    def set_progress(self, value, text=""):
        self.progress.setValue(value)
        if text:
            self.label.setText(text)
    
    @QtCore.pyqtSlot(str)        
    def append_details(self, text):
        self.details.append(text)

class ClickableProgressBar(QtWidgets.QProgressBar):
    """A progress bar that allows seeking by clicking on it."""
    clicked = QtCore.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        """Handle mouse press events to calculate the seek position."""
        if event.button() == QtCore.Qt.LeftButton:
            percent = event.pos().x() / self.width()
            
            target_position = int(self.maximum() * percent)
            
            self.clicked.emit(target_position)
            
            self.setValue(target_position)

class ClickableLabel(QtWidgets.QLabel):
    """A QLabel that emits a clicked signal."""
    clicked = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()

class WaveformWidget(QtWidgets.QWidget):
    rangeChanged = QtCore.pyqtSignal(int, int)
    viewChanged = QtCore.pyqtSignal(int, int)
    zoomRequested = QtCore.pyqtSignal(int, int)
    seekRequested = QtCore.pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        
        self.audio_data = None
        self.resampled_data = None
        self.sample_rate = 0
        
        self.duration_ms = 0
        self.selection_start_ms = 0
        self.selection_end_ms = 0
        self.view_start_ms = 0
        self.view_end_ms = 0
        self.playhead_ms = 0
        
        self.is_selecting = False
        
        self.selection_color = QtGui.QColor(0, 120, 215, 70)
        self.playhead_color = QtGui.QColor(255, 0, 0)
        self.background_color = QtGui.QColor(25, 25, 26)
        self.waveform_color = QtGui.QColor(150, 180, 210)
        
        self.setMouseTracking(True)
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta != 0:
            self.zoomRequested.emit(delta, event.pos().x())
        event.accept()
    def set_duration(self, duration_ms):
        self.duration_ms = duration_ms
        self.selection_end_ms = duration_ms
        self.view_end_ms = duration_ms
        self.viewChanged.emit(0, self.duration_ms)

    def set_waveform(self, wav_path):
        if not MATPLOTLIB_AVAILABLE:
            self.audio_data = None
            self.update()
            return
        
        try:
            import wave
            
            with wave.open(wav_path, 'rb') as wf:
                self.sample_rate = wf.getframerate()
                sampwidth = wf.getsampwidth()
                nframes = wf.getnframes()
                channels = wf.getnchannels()
                
                frames = wf.readframes(nframes)
            
            if sampwidth == 1:
                dtype = np.uint8
                max_val = 2**8 / 2
            elif sampwidth == 2:
                dtype = np.int16
                max_val = 2**15
            elif sampwidth == 3:
                data = np.empty((nframes, channels, 4), dtype=np.uint8)
                data[:, :, :sampwidth] = np.frombuffer(frames, dtype=np.uint8).reshape(-1, channels, sampwidth)
                data[:, :, sampwidth:] = (data[:, :, sampwidth - 1:sampwidth] >> 7) * 255
                data = data.view(np.int32)
                max_val = 2**23
            elif sampwidth == 4:
                try:
                    data = np.frombuffer(frames, dtype=np.float32)
                    max_val = 1.0 
                except (TypeError, ValueError):
                    data = np.frombuffer(frames, dtype=np.int32)
                    max_val = 2**31
            else:
                raise ValueError(f"Unsupported sample width: {sampwidth}")

            if sampwidth != 4 or max_val != 1.0:
                 data = np.frombuffer(frames, dtype=dtype)
            
            if channels > 1:
                data = data.reshape(-1, channels)
                data = data.mean(axis=1)

            self.audio_data = data.astype(np.float32) / max_val
            
            DEBUG.log(f"Waveform data loaded: {len(self.audio_data)} samples, sample rate: {self.sample_rate}, sampwidth: {sampwidth}")
        
        except Exception as e:
            DEBUG.log(f"Error loading waveform data: {e}", "ERROR")
            self.audio_data = None
        
        self.update()

    def set_selection_range(self, start_ms, end_ms):
        self.selection_start_ms = max(0, start_ms)
        self.selection_end_ms = min(self.duration_ms, end_ms)
        self.update()

    def set_view_range(self, start_ms, end_ms):
        self.view_start_ms = max(0, start_ms)
        self.view_end_ms = min(self.duration_ms, end_ms)
        self.update()

    def set_playhead(self, position_ms):
        self.playhead_ms = position_ms
        self.update()
        
    def _ms_to_sample(self, ms):
        return int(ms / 1000.0 * self.sample_rate)

    def _sample_to_ms(self, sample_index):
        return int(sample_index / self.sample_rate * 1000.0)

    def _ms_to_x(self, ms):
        view_duration = self.view_end_ms - self.view_start_ms
        if view_duration <= 0: return 0
        return ((ms - self.view_start_ms) / view_duration) * self.width()

    def _x_to_ms(self, x, view_start=None, view_end=None):
        start = view_start if view_start is not None else self.view_start_ms
        end = view_end if view_end is not None else self.view_end_ms
        
        view_duration = end - start
        if view_duration <= 0: return 0
        return start + int((x / self.width()) * view_duration)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), self.background_color)

        if self.audio_data is not None and self.duration_ms > 0:
            view_duration = self.view_end_ms - self.view_start_ms
            if view_duration <= 0:
                painter.end()
                return

            start_sample = self._ms_to_sample(self.view_start_ms)
            end_sample = self._ms_to_sample(self.view_end_ms)
            visible_data = self.audio_data[start_sample:end_sample]

            if len(visible_data) > 0:
        
                path = QtGui.QPainterPath()
                h = self.height()
                half_h = h / 2
                
                samples_per_pixel = len(visible_data) / self.width()
                
                if samples_per_pixel < 1: 
              
                    path.moveTo(0, half_h - visible_data[0] * half_h)
                    for i, sample in enumerate(visible_data):
                        x = i * (self.width() / len(visible_data))
                        y = half_h - sample * half_h
                        path.lineTo(x, y)
                else:
                    step = int(samples_per_pixel)
                    path.moveTo(0, half_h)
                    for i in range(self.width()):
                        start = i * step
                        end = start + step
                        if start >= len(visible_data): break
                        
                        chunk = visible_data[start:end]
                        min_val = np.min(chunk)
                        max_val = np.max(chunk)
                        
                        y_max = half_h - max_val * half_h
                        y_min = half_h - min_val * half_h
                        
                        painter.setPen(QtGui.QPen(self.waveform_color, 1))
                        painter.drawLine(i, int(y_min), i, int(y_max))
                
                if not path.isEmpty():
                    painter.setPen(QtGui.QPen(self.waveform_color, 1))
                    painter.drawPath(path)

        start_x = self._ms_to_x(self.selection_start_ms)
        end_x = self._ms_to_x(self.selection_end_ms)
        painter.fillRect(QtCore.QRectF(start_x, 0, end_x - start_x, self.height()), self.selection_color)
        
        if self.view_start_ms <= self.playhead_ms <= self.view_end_ms:
            playhead_x = self._ms_to_x(self.playhead_ms)
            painter.setPen(self.playhead_color)
            painter.drawLine(int(playhead_x), 0, int(playhead_x), self.height())
        
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.duration_ms > 0:
            seek_ms = self._x_to_ms(event.pos().x())
            
            self.seekRequested.emit(seek_ms)
            
            self.is_selecting = True
            self.selection_start_ms = seek_ms
            self.selection_end_ms = seek_ms
            
            self.set_playhead(seek_ms) 
            self.rangeChanged.emit(self.selection_start_ms, self.selection_end_ms)
            self.update()

    def mouseMoveEvent(self, event):
        current_ms = self._x_to_ms(event.pos().x())
        self.setToolTip(f"{current_ms / 1000:.3f} s")

        if self.is_selecting and self.duration_ms > 0:
            start = min(self.selection_start_ms, current_ms)
            end = max(self.selection_start_ms, current_ms)
            if self.selection_start_ms != start or self.selection_end_ms != end:
                self.set_selection_range(start, end)
                self.rangeChanged.emit(start, end)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_selecting = False
