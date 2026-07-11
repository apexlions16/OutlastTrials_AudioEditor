from ..common import *
from ..debug import DEBUG
from ..services.audio import AudioToWavConverter, VolumeProcessor, WavToWemConverter
from .widgets import WaveformWidget

class WemVolumeEditDialog(QtWidgets.QDialog):
    """Dialog for editing WEM file volume"""
    
    def __init__(self, parent, entry, lang, is_mod=False):
        super().__init__(parent)
        self.tr = parent.tr if hasattr(parent, 'tr') else lambda key: key
        self.parent = parent
        self.entry = entry
        self.lang = lang
        self.is_mod = is_mod
        self.volume_processor = VolumeProcessor()
        self.temp_files = []
        self.current_analysis = None
        
        self.setWindowTitle(self.tr("volume_editor_title").format(shortname=entry.get('ShortName', '')))
        self.setMinimumSize(600, 500)
        
        self.wav_converter = WavToWemConverter(parent)
        self.auto_configure_converter()
        
        self.create_ui()
        QtCore.QTimer.singleShot(100, self.analyze_wem_file)

    def auto_configure_converter(self):
        """Automatically configure converter from parent settings"""
        try:
            if hasattr(self.parent, 'wwise_path_edit') and hasattr(self.parent, 'converter_project_path_edit'):
                wwise_path = self.parent.wwise_path_edit.text()
                project_path = self.parent.converter_project_path_edit.text()
                
                if wwise_path and project_path and os.path.exists(wwise_path):
                    self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                    DEBUG.log(f"Auto-configured Wwise: {wwise_path}")
                    return True
            
            wwise_path = self.parent.settings.data.get("wav_wwise_path", "")
            project_path = self.parent.settings.data.get("wav_project_path", "")
            
            if wwise_path and project_path and os.path.exists(wwise_path):
                self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                DEBUG.log(f"Auto-configured Wwise from settings: {wwise_path}")
                return True
                
            DEBUG.log("Could not auto-configure Wwise - no valid paths found", "WARNING")
            return False
            
        except Exception as e:
            DEBUG.log(f"Error auto-configuring Wwise: {e}", "ERROR")
            return False    

    def create_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        header_text = f"Adjusting volume for: {self.entry.get('ShortName', '')}"
        if self.is_mod:
            header_text += " (MOD version)"
        else:
            header_text += " (Original version)"
            
        header = QtWidgets.QLabel(header_text)
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        if not self.volume_processor.is_available():
            error_widget = QtWidgets.QWidget()
            error_layout = QtWidgets.QVBoxLayout(error_widget)
            error_layout.setContentsMargins(20, 20, 20, 20)
            
            error_label = QtWidgets.QLabel(self.tr("volume_deps_missing"))
            error_label.setStyleSheet("color: red; font-size: 14px;")
            error_layout.addWidget(error_label)
            
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(self.reject)
            error_layout.addWidget(close_btn)
            
            layout.addWidget(error_widget)
            return
        
        analysis_group = QtWidgets.QGroupBox(self.tr("audio_analysis_group"))
        analysis_layout = QtWidgets.QFormLayout(analysis_group)
        
        self.current_rms_label = QtWidgets.QLabel(self.tr("analyzing"))
        self.current_peak_label = QtWidgets.QLabel(self.tr("analyzing"))
        self.duration_label = QtWidgets.QLabel(self.tr("analyzing"))

        self.max_safe_label = QtWidgets.QLabel(self.tr("no_limit"))
        
        analysis_layout.addRow(self.tr("current_rms"), self.current_rms_label)
        analysis_layout.addRow(self.tr("current_peak"), self.current_peak_label)
        analysis_layout.addRow(self.tr("duration_label"), self.duration_label)
        analysis_layout.addRow(self.tr("recommended_max"), self.max_safe_label)
        
        layout.addWidget(analysis_group)
        
        control_group = QtWidgets.QGroupBox(self.tr("volume_control_group"))
        control_layout = QtWidgets.QVBoxLayout(control_group)
        
        slider_widget = QtWidgets.QWidget()
        slider_layout = QtWidgets.QHBoxLayout(slider_widget)
        
        slider_layout.addWidget(QtWidgets.QLabel(self.tr("volume_label_simple")))
        
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(1000) 
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.volume_slider.setTickInterval(100)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        slider_layout.addWidget(self.volume_slider, 1)
        
        self.volume_label = QtWidgets.QLabel("100%")
        self.volume_label.setMinimumWidth(80)
        self.volume_label.setAlignment(QtCore.Qt.AlignCenter)
        self.volume_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        slider_layout.addWidget(self.volume_label)
        
        self.volume_spin = QtWidgets.QSpinBox()
        self.volume_spin.setMinimum(0)
        self.volume_spin.setMaximum(9999)  
        self.volume_spin.setValue(100)
        self.volume_spin.setSuffix("%")
        self.volume_spin.valueChanged.connect(self.on_spin_changed)
        slider_layout.addWidget(self.volume_spin)
        
        control_layout.addWidget(slider_widget)
        
        presets_widget = QtWidgets.QWidget()
        presets_layout = QtWidgets.QHBoxLayout(presets_widget)
        presets_layout.addWidget(QtWidgets.QLabel(self.tr("quick_presets")))
        
        preset_buttons = [
            ("25%", 25),
            ("50%", 50),
            ("75%", 75),
            ("100%", 100),
            ("150%", 150),
            ("200%", 200),
            ("300%", 300),
            ("500%", 500),
            ("1000%", 1000)
        ]
        
        for text, value in preset_buttons:
            btn = QtWidgets.QPushButton(text)
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda checked, v=value: self.set_volume(v))
            presets_layout.addWidget(btn)
        
        presets_layout.addStretch()
        control_layout.addWidget(presets_widget)
        
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setStyleSheet("padding: 10px; border: 1px solid #5a5d5f; border-radius: 5px;")
        control_layout.addWidget(self.preview_label)
        self.update_preview()
        
        layout.addWidget(control_group)
        
        self.progress_widget = QtWidgets.QWidget()
        self.progress_widget.hide()
        progress_layout = QtWidgets.QVBoxLayout(self.progress_widget)
        
        self.progress_label = QtWidgets.QLabel("Processing...")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QtWidgets.QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_text = QtWidgets.QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        progress_layout.addWidget(self.status_text)
        
        layout.addWidget(self.progress_widget)
        
        buttons_widget = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout(buttons_widget)
        
        buttons_layout.addStretch()
        
        self.process_btn = QtWidgets.QPushButton(self.tr("apply_volume_change_btn"))
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.process_btn.clicked.connect(self.process_volume_change)
        
        cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.process_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(buttons_widget)
    
    def analyze_wem_file(self):
        """Analyze the WEM file"""
        if not self.volume_processor.is_available():
            return 
        
        try:
            file_id = self.entry.get("Id", "")
            if self.is_mod:
  
                wem_path = self.parent.get_mod_path(file_id, self.lang)
                if not wem_path or not os.path.exists(wem_path):
                 
                    if self.lang != "SFX":
                        wem_path = os.path.join(
                            self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                            "Windows", "Media", self.lang, f"{file_id}.wem"
                        )
                    else:
                        wem_path = os.path.join(
                            self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                            "Windows", "Media", f"{file_id}.wem"
                        )
            else:
                wem_path = self.parent.get_original_path(file_id, self.lang)
            
            if not wem_path or not os.path.exists(wem_path):
                self.current_rms_label.setText("File not found")
                DEBUG.log(f"WemVolumeEditDialog: File not found at {wem_path}", "WARNING")
                return
            
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
            self.temp_files.append(temp_wav)
            
            ok, err = self.parent.wem_to_wav_vgmstream(wem_path, temp_wav)
            if not ok:
                self.current_rms_label.setText("Conversion error")
                return
            
            self.current_analysis = self.volume_processor.analyze_audio(temp_wav)
            if self.current_analysis:
                self.current_rms_label.setText(f"{self.current_analysis['rms_percent']:.1f}%")
                self.current_peak_label.setText(f"{self.current_analysis['peak_percent']:.1f}%")
                self.duration_label.setText(f"{self.current_analysis['duration_seconds']:.2f} seconds")
                
                safe_max = int(self.current_analysis['max_increase'])
                self.max_safe_label.setText(f"{safe_max}% (for no clipping)")
                
            else:
                self.current_rms_label.setText("Analysis failed")
                
        except Exception as e:
            DEBUG.log(f"Error analyzing WEM: {e}", "ERROR")
            self.current_rms_label.setText("Error")
    
    def on_volume_changed(self, value):
        self.volume_label.setText(f"{value}%")
        self.volume_spin.blockSignals(True)
        self.volume_spin.setValue(value)
        self.volume_spin.blockSignals(False)
        self.update_preview()
    
    def on_spin_changed(self, value):
        self.volume_slider.blockSignals(True)
        if value > self.volume_slider.maximum():
            self.volume_slider.setMaximum(value + 100)
        self.volume_slider.setValue(value)
        self.volume_slider.blockSignals(False)
        self.volume_label.setText(f"{value}%")
        self.update_preview()
    
    def set_volume(self, value):
        if value > self.volume_slider.maximum():
            self.volume_slider.setMaximum(value + 100)
        self.volume_slider.setValue(value)
    
    def update_preview(self):
        if not self.current_analysis:
            self.preview_label.setText(self.tr("waiting_for_analysis"))
            return
            
        volume = self.volume_slider.value()
        
        new_rms = self.current_analysis['rms_percent'] * (volume / 100)
        new_peak = self.current_analysis['peak_percent'] * (volume / 100)
        
        preview_text = self.tr("preview_rms_peak").format(new_rms=new_rms, new_peak=new_peak)
        is_dark_theme = self.parent.settings.data.get("theme", "light") == "dark"

        base_style = "padding: 10px; border-radius: 5px;"
        if new_peak > 100:
            preview_text += self.tr("preview_clipping").format(over=new_peak - 100)
            bg_color = "#5a1d1d" if is_dark_theme else "#ffcccc"
            text_color = "#ff8a80" if is_dark_theme else "red"
            self.preview_label.setStyleSheet(f"{base_style} background-color: {bg_color}; color: {text_color};")
        elif new_peak > 95:
            preview_text += self.tr("preview_near_clipping")
            bg_color = "#6b4f1b" if is_dark_theme else "#fff0cc"
            text_color = "#ffd54f" if is_dark_theme else "orange"
            self.preview_label.setStyleSheet(f"{base_style} background-color: {bg_color}; color: {text_color};")
        else:
            bg_color = "#1e4e24" if is_dark_theme else "#ccffcc"
            text_color = "#a5d6a7" if is_dark_theme else "green"
            self.preview_label.setStyleSheet(f"{base_style} background-color: {bg_color}; color: {text_color};")

        self.preview_label.setText(preview_text)
    
    def process_volume_change(self):
        volume = self.volume_slider.value()
        
        if volume == 100:
            QtWidgets.QMessageBox.information(
                self, self.tr("no_change"),
                self.tr("volume_no_change_msg")
            )
            return
        
        if not self.wav_converter.wwise_path or not self.wav_converter.project_path:
            QtWidgets.QMessageBox.warning(
                self, self.tr("config_required"),
                self.tr("wwise_config_required_msg")
            )
            return
        
        self.progress_widget.show()
        self.process_btn.setEnabled(False)
        
        thread = threading.Thread(target=self._process_thread, args=(volume,))
        thread.daemon = True
        thread.start()

    def _process_thread(self, volume):
        """Process volume change in thread"""
        try:
            self.update_progress(10, self.tr("status_preparing"))
            
            file_id = self.entry.get("Id", "")
            shortname = self.entry.get("ShortName", "")
            original_filename = os.path.splitext(shortname)[0]
            
            if self.is_mod:
                # FIX: Use get_mod_path helper to correctly locate the source file
                current_mod_path = self.parent.get_mod_path(file_id, self.lang)
                
                if not current_mod_path or not os.path.exists(current_mod_path):
                    raise Exception("Modified audio file not found. Try reverting to original first.")
                
                backup_path = self.parent.get_backup_path(file_id, self.lang)
                
                if os.path.exists(backup_path):
                    source_wem_path = backup_path
                    self.update_progress(15, self.tr("status_using_backup"))
                    DEBUG.log(f"Using backup as source: {backup_path}")
                else:
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(current_mod_path, backup_path)
                    source_wem_path = backup_path
                    self.update_progress(15, self.tr("status_backup_created"))
                    DEBUG.log(f"Created backup from current mod: {backup_path}")
            else:
                source_wem_path = self.parent.get_original_path(file_id, self.lang)
                if not os.path.exists(source_wem_path):
                    raise Exception(f"Original WEM file not found: {source_wem_path}")
                self.update_progress(15, self.tr("status_using_original"))
            
            self.update_progress(20, self.tr("status_converting_to_wav"))
            
            temp_wav_original = tempfile.NamedTemporaryFile(
                suffix=f'_{original_filename}_source.wav', 
                delete=False
            ).name
            self.temp_files.append(temp_wav_original)
            
            ok, err = self.parent.wem_to_wav_vgmstream(source_wem_path, temp_wav_original)
            if not ok:
                raise Exception(f"WEM to WAV conversion failed: {err}")
            
            self.update_progress(40, self.tr("status_adjusting_volume"))
            
            temp_wav_adjusted = tempfile.NamedTemporaryFile(
                suffix=f'_{original_filename}_vol{volume}.wav', 
                delete=False
            ).name
            self.temp_files.append(temp_wav_adjusted)
            
            success, result = self.volume_processor.change_volume(
                temp_wav_original,
                temp_wav_adjusted,
                volume
            )
            
            if not success:
                raise Exception(f"Volume adjustment failed: {result}")
            
            self.update_progress(60, self.tr("status_preparing_for_wem"))
            
            temp_dir = tempfile.mkdtemp(prefix="volume_adjust_")
            self.temp_files.append(temp_dir)
            
            final_wav_for_wwise = os.path.join(temp_dir, f"{original_filename}.wav")
            shutil.copy2(temp_wav_adjusted, final_wav_for_wwise)
            
            # Use source size as target if we are editing original, or if preserving mod size
            target_size = os.path.getsize(source_wem_path)
            
            file_pair = {
                "wav_file": final_wav_for_wwise,
                "target_wem": source_wem_path,
                "wav_name": f"{original_filename}.wav",
                "target_name": f"{original_filename}.wem",
                "target_size": target_size,
                "language": self.lang,
                "file_id": file_id
            }
            
            if not self.wav_converter.wwise_path:
                raise Exception("Wwise not configured. Please check configuration.")
            
            temp_output = os.path.join(temp_dir, "output")
            os.makedirs(temp_output, exist_ok=True)
            self.wav_converter.output_folder = temp_output
            
            self.update_progress(70, self.tr("status_converting_to_wem"))
            
            conversion_result = self.wav_converter.convert_single_file_main(file_pair, 1, 1)
            
            if not conversion_result.get('success'):
                error_msg = conversion_result.get('error', 'Unknown error')
                raise Exception(f"WEM conversion failed: {error_msg}")
            
            self.update_progress(85, self.tr("status_deploying_to_mod"))
            
            # FIX: Use correct deployment path with Media folder
            if self.lang != "SFX":
                target_dir = os.path.join(
                    self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                    "Windows", "Media", self.lang
                )
            else:
                target_dir = os.path.join(
                    self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                    "Windows", "Media"
                )
            
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, f"{file_id}.wem")
            
            output_wem = conversion_result['output_path']
            shutil.copy2(output_wem, target_path)
            
            try:
                if os.path.exists(temp_output):
                    shutil.rmtree(temp_output)
            except Exception as e:
                DEBUG.log(f"Warning: Failed to cleanup temp output: {e}", "WARNING")
            
            self.update_progress(100, self.tr("status_complete"))
            
            clipping_info = ""
            if result.get('clipped_percent', 0) > 0:
                clipping_info = self.tr("clipping_info_text").format(percent=result['clipped_percent'])

            backup_info = ""
            if self.parent.has_backup(file_id, self.lang):
                backup_info = self.tr("backup_available_info")

            source_info = ""
            if self.is_mod:
                if os.path.exists(self.parent.get_backup_path(file_id, self.lang)):
                    source_info = self.tr("source_info_backup")
                else:
                    source_info = self.tr("source_info_mod_backup_created")
            else:
                source_info = self.tr("source_info_original")

            success_message = self.tr("volume_change_success_msg").format(
                volume=volume,
                actual_change=result.get('actual_change', volume),
                clipping_info=clipping_info,
                source_info=source_info,
                backup_info=backup_info
            )
            
            QtCore.QMetaObject.invokeMethod(
                self, "show_success",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, success_message)
            )
            
        except Exception as e:
            error_message = str(e)
            
            if "Failed to create WEM file" in error_message or "No acceptable result found" in error_message:
                error_message = self.tr("wem_conversion_failed_msg").format(error_message=error_message)
            elif "Wwise not configured" in error_message:
                error_message = self.tr("wwise_not_configured_msg")
            elif "not found" in error_message.lower():
                error_message = self.tr("required_file_not_found_msg").format(error_message=error_message)
            
            QtCore.QMetaObject.invokeMethod(
                self, "show_error",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, error_message)
            )
        
        finally:
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        if os.path.isdir(temp_file):
                            shutil.rmtree(temp_file)
                        else:
                            os.remove(temp_file)
                except Exception as e:
                    DEBUG.log(f"Warning: Failed to cleanup temp file {temp_file}: {e}", "WARNING")  

    def update_progress(self, value, text):
        QtCore.QMetaObject.invokeMethod(
            self.progress_bar, "setValue",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(int, value)
        )
        QtCore.QMetaObject.invokeMethod(
            self.progress_label, "setText",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, text)
        )
        QtCore.QMetaObject.invokeMethod(
            self.status_text, "append",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, f"[{value}%] {text}")
        )
    
    @QtCore.pyqtSlot(str)
    def show_success(self, message):
        self.progress_widget.hide()
        self.process_btn.setEnabled(True)
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        QtWidgets.QMessageBox.information(self, "Success", message)
        if hasattr(self.parent, 'populate_tree'):
            self.parent.populate_tree(self.lang)
        self.accept()
    
    @QtCore.pyqtSlot(str)
    def show_error(self, error):
        self.progress_widget.hide()
        self.process_btn.setEnabled(True)
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        QtWidgets.QMessageBox.critical(self, self.tr("error"), f"{self.tr('volume_change_failed_title')}:\n\n{error}")

class BatchVolumeEditDialog(QtWidgets.QDialog):
    """Dialog for batch editing volume of multiple files"""
    
    def __init__(self, parent, entries_and_lang, is_mod=False):
        super().__init__(parent)
        self.tr = parent.tr if hasattr(parent, 'tr') else lambda key: key
        self.parent = parent
        self.entries_and_lang = entries_and_lang
        self.is_mod = is_mod
        self.volume_processor = VolumeProcessor()
        self.temp_files = []
        
        self.setWindowTitle(self.tr("batch_volume_editor_title").format(count=len(entries_and_lang)))
        self.setMinimumSize(800, 700)
        
        self.wav_converter = WavToWemConverter(parent)
        self.auto_configure_converter()
        
        self.create_ui()
        QtCore.QTimer.singleShot(100, self.analyze_files)
    
    def auto_configure_converter(self):
        try:
            if hasattr(self.parent, 'wwise_path_edit') and hasattr(self.parent, 'converter_project_path_edit'):
                wwise_path = self.parent.wwise_path_edit.text()
                project_path = self.parent.converter_project_path_edit.text()
                if wwise_path and project_path and os.path.exists(wwise_path):
                    self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                    return True
            wwise_path = self.parent.settings.data.get("wav_wwise_path", "")
            project_path = self.parent.settings.data.get("wav_project_path", "")
            if wwise_path and project_path and os.path.exists(wwise_path):
                self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                return True
            return False
        except:
            return False
    
    def create_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        header_text = f"Batch Volume Editor - {len(self.entries_and_lang)} files"
        if self.is_mod:
            header_text += " (MOD versions)"
        else:
            header_text += " (Original versions)"
            
        header = QtWidgets.QLabel(header_text)
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        if not self.volume_processor.is_available():
            error_label = QtWidgets.QLabel(self.tr("volume_deps_missing"))
            error_label.setStyleSheet("color: red; padding: 20px; font-size: 14px;")
            layout.addWidget(error_label)
            close_btn = QtWidgets.QPushButton(self.tr("close"))
            close_btn.clicked.connect(self.reject)
            layout.addWidget(close_btn)
            return
        
        if self.wav_converter.wwise_path and self.wav_converter.project_path:
            config_status = QtWidgets.QLabel(self.tr("wwise_configured_auto"))
            config_status.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        else:
            config_status = QtWidgets.QLabel(self.tr("wwise_not_configured_warning"))
            config_status.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
        layout.addWidget(config_status)
        backup_info_widget = QtWidgets.QWidget()
        backup_info_layout = QtWidgets.QHBoxLayout(backup_info_widget)

        backup_icon = QtWidgets.QLabel("💾")
        backup_text = QtWidgets.QLabel(self.tr("backups_stored_in").format(path=os.path.join(self.parent.base_path, '.backups', 'audio')))
        backup_text.setStyleSheet("color: #666; font-size: 11px;")

        backup_info_layout.addWidget(backup_icon)
        backup_info_layout.addWidget(backup_text)
        backup_info_layout.addStretch()

        layout.addWidget(backup_info_widget)

        control_group = QtWidgets.QGroupBox(self.tr("volume_control_all_files_group"))

        control_layout = QtWidgets.QVBoxLayout(control_group)
        
        slider_widget = QtWidgets.QWidget()
        slider_layout = QtWidgets.QHBoxLayout(slider_widget)
        
        slider_layout.addWidget(QtWidgets.QLabel(self.tr("volume_label_simple")))
        
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(1000)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.volume_slider.setTickInterval(100)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        slider_layout.addWidget(self.volume_slider, 1)
        
        self.volume_label = QtWidgets.QLabel("100%")
        self.volume_label.setMinimumWidth(80)
        self.volume_label.setAlignment(QtCore.Qt.AlignCenter)
        self.volume_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        slider_layout.addWidget(self.volume_label)
        
        self.volume_spin = QtWidgets.QSpinBox()
        self.volume_spin.setMinimum(0)
        self.volume_spin.setMaximum(9999)
        self.volume_spin.setValue(100)
        self.volume_spin.setSuffix("%")
        self.volume_spin.valueChanged.connect(self.on_spin_changed)
        slider_layout.addWidget(self.volume_spin)
        
        control_layout.addWidget(slider_widget)
        
        presets_widget = QtWidgets.QWidget()
        presets_layout = QtWidgets.QHBoxLayout(presets_widget)
        presets_layout.addWidget(QtWidgets.QLabel(self.tr("quick_presets")))
        
        preset_buttons = [
            ("25%", 25), ("50%", 50), ("75%", 75), ("100%", 100),
            ("150%", 150), ("200%", 200), ("300%", 300), ("500%", 500)
        ]
        
        for text, value in preset_buttons:
            btn = QtWidgets.QPushButton(text)
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda checked, v=value: self.set_volume(v))
            presets_layout.addWidget(btn)
        
        presets_layout.addStretch()
        control_layout.addWidget(presets_widget)
        
        layout.addWidget(control_group)
        
        files_group = QtWidgets.QGroupBox(self.tr("files_to_process_group"))
        files_layout = QtWidgets.QVBoxLayout(files_group)
        
        self.files_table = QtWidgets.QTableWidget()
        self.files_table.setColumnCount(6)
        self.files_table.setHorizontalHeaderLabels([
            self.tr("file_header"), self.tr("language_header"), self.tr("current_rms_header"), 
            self.tr("current_peak_header"), self.tr("new_preview_header"), self.tr("status_header")
        ])

        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        
        self.files_table.setAlternatingRowColors(True)
        files_layout.addWidget(self.files_table)
        
        layout.addWidget(files_group)
        
        self.progress_widget = QtWidgets.QWidget()
        self.progress_widget.hide()
        progress_layout = QtWidgets.QVBoxLayout(self.progress_widget)
        
        self.progress_label = QtWidgets.QLabel("Processing...")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QtWidgets.QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.current_file_label = QtWidgets.QLabel("")
        progress_layout.addWidget(self.current_file_label)
        
        layout.addWidget(self.progress_widget)
        
        buttons_widget = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout(buttons_widget)
        
        buttons_layout.addStretch()
        
        self.process_btn = QtWidgets.QPushButton(self.tr("apply_to_all_btn"))
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.process_btn.clicked.connect(self.process_all_files)
        
        cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.process_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(buttons_widget)
        
        self.file_analyses = []
    
    def analyze_files(self):
        """Analyze all files"""
        self.files_table.setRowCount(len(self.entries_and_lang))
        self.file_analyses = []
        
        for i, (entry, lang) in enumerate(self.entries_and_lang):
            self.files_table.setItem(i, 0, QtWidgets.QTableWidgetItem(entry.get('ShortName', '')))
            self.files_table.setItem(i, 1, QtWidgets.QTableWidgetItem(lang))
            self.files_table.setItem(i, 5, QtWidgets.QTableWidgetItem("Analyzing..."))
            
            try:
                file_id = entry.get("Id", "")
                if self.is_mod:
                   
                    wem_path = self.parent.get_mod_path(file_id, lang)
                    if not wem_path or not os.path.exists(wem_path):
                       
                        if lang != "SFX":
                            wem_path = os.path.join(
                                self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                                "Windows", "Media", lang, f"{file_id}.wem"
                            )
                        else:
                            wem_path = os.path.join(
                                self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                                "Windows", "Media", f"{file_id}.wem"
                            )
                else:
                    wem_path = self.parent.get_original_path(file_id, lang)
                
                if wem_path and os.path.exists(wem_path):
                    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
                    self.temp_files.append(temp_wav)
                    
                    ok, err = self.parent.wem_to_wav_vgmstream(wem_path, temp_wav)
                    if ok:
                        analysis = self.volume_processor.analyze_audio(temp_wav)
                        if analysis:
                            self.file_analyses.append(analysis)
                            self.files_table.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{analysis['rms_percent']:.1f}%"))
                            self.files_table.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{analysis['peak_percent']:.1f}%"))
                            self.files_table.setItem(i, 5, QtWidgets.QTableWidgetItem("Ready"))
                            continue
                
                self.file_analyses.append(None)
                self.files_table.setItem(i, 2, QtWidgets.QTableWidgetItem("N/A"))
                self.files_table.setItem(i, 3, QtWidgets.QTableWidgetItem("N/A"))
                self.files_table.setItem(i, 5, QtWidgets.QTableWidgetItem("Error"))
                
            except Exception as e:
                self.file_analyses.append(None)
                self.files_table.setItem(i, 5, QtWidgets.QTableWidgetItem("Error"))
        
        self.update_preview_all()
    
    def on_volume_changed(self, value):
        self.volume_label.setText(f"{value}%")
        self.volume_spin.blockSignals(True)
        self.volume_spin.setValue(value)
        self.volume_spin.blockSignals(False)
        self.update_preview_all()
    
    def on_spin_changed(self, value):
        self.volume_slider.blockSignals(True)
        if value > self.volume_slider.maximum():
            self.volume_slider.setMaximum(value + 100)
        self.volume_slider.setValue(value)
        self.volume_slider.blockSignals(False)
        self.volume_label.setText(f"{value}%")
        self.update_preview_all()
    
    def set_volume(self, value):
        if value > self.volume_slider.maximum():
            self.volume_slider.setMaximum(value + 100)
        self.volume_slider.setValue(value)
    
    def update_preview_all(self):
        volume = self.volume_slider.value()
        
        for i, analysis in enumerate(self.file_analyses):
            if analysis:
                new_rms = analysis['rms_percent'] * (volume / 100)
                new_peak = analysis['peak_percent'] * (volume / 100)
                
                preview_text = f"RMS {new_rms:.1f}%, Peak {new_peak:.1f}%"
                if new_peak > 100:
                    preview_text += " ⚠️"
                
                preview_item = QtWidgets.QTableWidgetItem(preview_text)
                if new_peak > 100:
                    preview_item.setBackground(QtGui.QColor(255, 200, 200))
                elif new_peak > 95:
                    preview_item.setBackground(QtGui.QColor(255, 240, 200))
                else:
                    preview_item.setBackground(QtGui.QColor(200, 255, 200))
                
                self.files_table.setItem(i, 4, preview_item)
            else:
                self.files_table.setItem(i, 4, QtWidgets.QTableWidgetItem("N/A"))
    
    def process_all_files(self):
        volume = self.volume_slider.value()
        
        if volume == 100:
            QtWidgets.QMessageBox.information(self, "No Change", "Volume is set to 100% (no change).")
            return
        
        if not self.wav_converter.wwise_path or not self.wav_converter.project_path:
            QtWidgets.QMessageBox.warning(self, "Configuration Required", self.tr("wwise_config_required_msg"))
            return
        
        self.progress_widget.show()
        self.process_btn.setEnabled(False)
        
        thread = threading.Thread(target=self._process_all_thread, args=(volume,))
        thread.daemon = True
        thread.start()
    
    def _process_all_thread(self, volume):
        """Process all files in thread"""
        try:
            total_files = len(self.entries_and_lang)
            successful = 0
            failed = 0
            
            for i, (entry, lang) in enumerate(self.entries_and_lang):
                if self.file_analyses[i] is None:
                    failed += 1
                    QtCore.QMetaObject.invokeMethod(
                        self, "update_file_status",
                        QtCore.Qt.QueuedConnection,
                        QtCore.Q_ARG(int, i),
                        QtCore.Q_ARG(str, self.tr("status_skipped_no_analysis"))
                    )
                    continue
                
                progress = int((i / total_files) * 100)
                file_name = entry.get('ShortName', f'File {i+1}')
                shortname = entry.get("ShortName", "")
                original_filename = os.path.splitext(shortname)[0]
                file_id = entry.get("Id", "")
                
                QtCore.QMetaObject.invokeMethod(
                    self, "update_progress",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(int, progress),
                    QtCore.Q_ARG(str, f"Processing {i+1}/{total_files}"),
                    QtCore.Q_ARG(str, file_name)
                )
                
                try:
                    if self.is_mod:
                        
                        current_mod_path = self.parent.get_mod_path(file_id, lang)
                        
                        if not current_mod_path or not os.path.exists(current_mod_path):
                            raise Exception(f"Modified audio file not found for {file_name}")
                        
                        backup_path = self.parent.get_backup_path(file_id, lang)
                        
                        if os.path.exists(backup_path):
                            source_wem_path = backup_path
                        else:
                            backup_dir = os.path.dirname(backup_path)
                            os.makedirs(backup_dir, exist_ok=True)
                            shutil.copy2(current_mod_path, backup_path)
                            source_wem_path = backup_path
                    else:
                        source_wem_path = self.parent.get_original_path(file_id, lang)
                        
                        if not os.path.exists(source_wem_path):
                            raise Exception(f"Original WEM file not found: {source_wem_path}")
                    
                    temp_wav_original = tempfile.NamedTemporaryFile(suffix=f'_{original_filename}_original.wav', delete=False).name
                    self.temp_files.append(temp_wav_original)
                    
                    ok, err = self.parent.wem_to_wav_vgmstream(source_wem_path, temp_wav_original)
                    if not ok:
                        raise Exception(f"WEM to WAV conversion failed: {err}")
                    
                    temp_wav_adjusted = tempfile.NamedTemporaryFile(suffix=f'_{original_filename}_adjusted.wav', delete=False).name
                    self.temp_files.append(temp_wav_adjusted)
                    
                    success, result = self.volume_processor.change_volume(
                        temp_wav_original,
                        temp_wav_adjusted,
                        volume
                    )
                    
                    if not success:
                        raise Exception(f"Volume adjustment failed: {result}")
                    
                    temp_dir = tempfile.mkdtemp(prefix=f"batch_volume_{i}_")
                    self.temp_files.append(temp_dir)
                    
                    final_wav_for_wwise = os.path.join(temp_dir, f"{original_filename}.wav")
                    shutil.copy2(temp_wav_adjusted, final_wav_for_wwise)
                    
                    original_wem_size = os.path.getsize(source_wem_path)
                    
                    file_pair = {
                        "wav_file": final_wav_for_wwise,
                        "target_wem": source_wem_path,
                        "wav_name": f"{original_filename}.wav",
                        "target_name": f"{original_filename}.wem",
                        "target_size": original_wem_size,
                        "language": lang,
                        "file_id": file_id
                    }
                    
                    temp_output = os.path.join(temp_dir, "output")
                    os.makedirs(temp_output, exist_ok=True)
                    self.wav_converter.output_folder = temp_output
                    
                    conversion_result = self.wav_converter.convert_single_file_main(file_pair, i+1, total_files)
                    
                    if not conversion_result.get('success'):
                        raise Exception(f"WEM conversion failed: {conversion_result.get('error', 'Unknown error')}")
                    
                    output_wem = conversion_result['output_path']
                    
                    if lang != "SFX":
                        target_dir = os.path.join(
                            self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                            "Windows", "Media", lang
                        )
                    else:
                        target_dir = os.path.join(
                            self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                            "Windows", "Media"
                        )
                    
                    os.makedirs(target_dir, exist_ok=True)
                    target_path = os.path.join(target_dir, f"{file_id}.wem")
                    
                    shutil.copy2(output_wem, target_path)
                    successful += 1
                    
                    QtCore.QMetaObject.invokeMethod(
                        self, "update_file_status",
                        QtCore.Qt.QueuedConnection,
                        QtCore.Q_ARG(int, i),
                        QtCore.Q_ARG(str, f"✓ {volume}%")
                    )
                    
                except Exception as e:
                    failed += 1
                    error_msg = str(e)
                    if len(error_msg) > 50:
                        error_msg = error_msg[:47] + "..."
                    
                    QtCore.QMetaObject.invokeMethod(
                        self, "update_file_status",
                        QtCore.Qt.QueuedConnection,
                        QtCore.Q_ARG(int, i),
                        QtCore.Q_ARG(str, f"✗ {error_msg}")
                    )
                    DEBUG.log(f"Error processing {file_name}: {str(e)}", "ERROR")
            
            QtCore.QMetaObject.invokeMethod(
                self, "processing_complete",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(int, successful),
                QtCore.Q_ARG(int, failed),
                QtCore.Q_ARG(int, volume)
            )
            
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(
                self, "show_error",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, str(e))
            )

    @QtCore.pyqtSlot(int, str, str)
    def update_progress(self, progress, main_text, current_file):
        self.progress_bar.setValue(progress)
        self.progress_label.setText(main_text)
        self.current_file_label.setText(current_file)

    @QtCore.pyqtSlot(int, str)
    def update_file_status(self, row, status):
        if row < self.files_table.rowCount():
            self.files_table.setItem(row, 5, QtWidgets.QTableWidgetItem(status))

    @QtCore.pyqtSlot(int, int, int)
    def processing_complete(self, successful, failed, volume):
        self.progress_widget.hide()
        self.process_btn.setEnabled(True)
        
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    if os.path.isdir(temp_file):
                        shutil.rmtree(temp_file)
                    else:
                        os.remove(temp_file)
            except Exception as e:
                DEBUG.log(f"Failed to clean up temp file {temp_file}: {e}", "WARNING")
        
        message = self.tr("batch_process_complete_msg").format(volume=volume, successful=successful, failed=failed)
        QtWidgets.QMessageBox.information(self, self.tr("batch_process_complete_title"), message)
        
        for lang in set(lang for _, lang in self.entries_and_lang):
            if hasattr(self.parent, 'populate_tree'):
                self.parent.populate_tree(lang)
        
        self.accept()

    @QtCore.pyqtSlot(str)
    def show_error(self, error):
        self.progress_widget.hide()
        self.process_btn.setEnabled(True)
        QtWidgets.QMessageBox.critical(self, self.tr("batch_process_error_title"), error)

class AudioTrimDialog(QtWidgets.QDialog):
    
    def __init__(self, parent, entry, lang, is_mod=False):
        super().__init__(parent)
        self.tr = parent.tr if hasattr(parent, 'tr') else lambda key: key
        self.parent = parent
        self.entry = entry
        self.lang = lang
        self.is_mod = is_mod
        self.temp_files = []
        self.source_wav = None
        self.start_ms = 0
        self.end_ms = 0
        
        self.setWindowTitle(self.tr("trim_editor_title").format(shortname=entry.get('ShortName', ''))) 
        self.setMinimumSize(800, 450)
        
        self.ffmpeg_path = AudioToWavConverter().find_ffmpeg()
        if not self.ffmpeg_path or not MATPLOTLIB_AVAILABLE:
            msg = self.tr("trim_deps_missing")
            QtWidgets.QMessageBox.critical(self, self.tr("error"), msg)

        self.wav_converter = WavToWemConverter(parent)
        self.auto_configure_converter()

        self.player = QtMultimedia.QMediaPlayer()
        self.player.setNotifyInterval(10)

        self.create_ui()
        QtCore.QTimer.singleShot(100, self.prepare_audio)

    def auto_configure_converter(self):
        try:
            if hasattr(self.parent, 'wwise_path_edit') and hasattr(self.parent, 'converter_project_path_edit'):
                wwise_path = self.parent.wwise_path_edit.text()
                project_path = self.parent.converter_project_path_edit.text()
                if wwise_path and project_path and os.path.exists(wwise_path):
                    self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                    return True
            wwise_path = self.parent.settings.data.get("wav_wwise_path", "")
            project_path = self.parent.settings.data.get("wav_project_path", "")
            if wwise_path and project_path and os.path.exists(wwise_path):
                self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                return True
            return False
        except:
            return False

    def create_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        header_text = self.tr("trimming_audio_for").format(shortname=self.entry.get('ShortName', ''))
        header_text += self.tr("version_mod") if self.is_mod else self.tr("version_original")
        header = QtWidgets.QLabel(header_text)
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        self.waveform_widget = WaveformWidget()
        self.waveform_widget.rangeChanged.connect(self.update_times_from_waveform)
        self.waveform_widget.zoomRequested.connect(self.on_wheel_zoom)
        self.waveform_widget.seekRequested.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.waveform_widget.set_playhead)
        layout.addWidget(self.waveform_widget)

        self.scroll_bar = QtWidgets.QScrollBar(QtCore.Qt.Horizontal)
        self.scroll_bar.valueChanged.connect(self.on_scroll)
        layout.addWidget(self.scroll_bar)

        zoom_widget = QtWidgets.QWidget()
        zoom_layout = QtWidgets.QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        self.zoom_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.zoom_slider.setRange(0, 100)
        self.zoom_slider.valueChanged.connect(self.on_zoom)
        zoom_layout.addWidget(QtWidgets.QLabel(self.tr("zoom_label")))
        zoom_layout.addWidget(self.zoom_slider)
        layout.addWidget(zoom_widget)

        time_widget = QtWidgets.QWidget()
        time_layout = QtWidgets.QFormLayout(time_widget)
        self.start_time_edit = QtWidgets.QSpinBox()
        self.start_time_edit.setSuffix(" ms")
        self.start_time_edit.editingFinished.connect(self.update_waveform_from_times)
        self.end_time_edit = QtWidgets.QSpinBox()
        self.end_time_edit.setSuffix(" ms")
        self.end_time_edit.editingFinished.connect(self.update_waveform_from_times)
        self.duration_label = QtWidgets.QLabel("New Duration: 0.000 s")
        self.duration_label.setStyleSheet("font-weight: bold;")
        time_layout.addRow(self.tr("start_time_label"), self.start_time_edit)
        time_layout.addRow(self.tr("end_time_label"), self.end_time_edit)
        time_layout.addRow(self.tr("new_duration_label"), self.duration_label)
        layout.addWidget(time_widget)

        playback_layout = QtWidgets.QHBoxLayout()
        self.play_btn = QtWidgets.QPushButton(self.tr("play_pause_btn"))
        self.play_btn.clicked.connect(self.toggle_playback)
        self.preview_btn = QtWidgets.QPushButton(self.tr("preview_trim_btn"))
        self.preview_btn.clicked.connect(self.preview_trim)
        self.stop_btn = QtWidgets.QPushButton(self.tr("stop_btn"))
        self.stop_btn.clicked.connect(self.stop_playback)
        playback_layout.addWidget(self.play_btn)
        playback_layout.addWidget(self.preview_btn)
        playback_layout.addWidget(self.stop_btn)
        layout.addLayout(playback_layout)
        self.progress_widget = QtWidgets.QWidget()
        self.progress_widget.hide()
        progress_layout = QtWidgets.QVBoxLayout(self.progress_widget)
        self.progress_label = QtWidgets.QLabel("Processing...")
        self.progress_bar = QtWidgets.QProgressBar()
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_widget)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        self.process_btn = QtWidgets.QPushButton(self.tr("apply_trim_btn"))
        self.process_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.process_btn.clicked.connect(self.process_trim)
        cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.process_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

    def prepare_audio(self):
        try:
            file_id = self.entry.get("Id", "")
            wem_path = self.parent.get_mod_path(file_id, self.lang) if self.is_mod else self.parent.get_original_path(file_id, self.lang)
            if not os.path.exists(wem_path): raise FileNotFoundError("Audio file not found!")

            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
            self.temp_files.append(temp_wav)
            
            ok, err = self.parent.wem_to_wav_vgmstream(wem_path, temp_wav)
            if not ok: raise Exception(f"WEM to WAV conversion failed: {err}")

            self.source_wav = temp_wav
            self.waveform_widget.set_waveform(self.source_wav)
            
            url = QtCore.QUrl.fromLocalFile(self.source_wav)
            self.player.setMedia(QtMultimedia.QMediaContent(url))
            self.player.durationChanged.connect(self.on_duration_changed)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, self.tr("error"), self.tr("preparing_audio_failed").format(e=e))
            self.reject()

    def on_duration_changed(self, duration):
        self.waveform_widget.set_duration(duration)
        self.start_time_edit.setRange(0, duration)
        self.end_time_edit.setRange(0, duration)
        self.end_time_edit.setValue(duration)
        self.update_times_from_waveform(0, duration)
        self.on_zoom(0)
    def on_zoom(self, value):
        if self.waveform_widget.duration_ms <= 0: return

        min_view_ms = 50
        max_view_ms = self.waveform_widget.duration_ms
        
        zoom_factor = value / 100.0
        view_duration = int(max_view_ms / (1 + 99 * zoom_factor))
        view_duration = max(min_view_ms, view_duration)

        self.scroll_bar.setPageStep(view_duration)
        self.scroll_bar.setRange(0, self.waveform_widget.duration_ms - view_duration)
        
        current_center = self.waveform_widget.view_start_ms + (self.waveform_widget.view_end_ms - self.waveform_widget.view_start_ms) / 2
        new_start = int(current_center - view_duration / 2)
        
        self.scroll_bar.setValue(new_start)
        self.on_scroll(new_start)

    def on_scroll(self, value):
        view_duration = self.scroll_bar.pageStep()
        self.waveform_widget.set_view_range(value, value + view_duration)
    def on_wheel_zoom(self, delta, mouse_x):
        """Handles zooming with the mouse wheel with smooth, centered scaling."""
        if self.waveform_widget.duration_ms <= 0: return

        zoom_factor = 1.15 if delta > 0 else 1 / 1.15

        current_view_start = self.waveform_widget.view_start_ms
        current_view_end = self.waveform_widget.view_end_ms
        current_view_duration = current_view_end - current_view_start

        time_at_cursor = self.waveform_widget._x_to_ms(mouse_x, current_view_start, current_view_end)

        new_view_duration = current_view_duration / zoom_factor
        
        min_view_ms = 20
        new_view_duration = max(min_view_ms, min(self.waveform_widget.duration_ms, new_view_duration))

        cursor_ratio = (time_at_cursor - current_view_start) / current_view_duration
        new_view_start = time_at_cursor - (new_view_duration * cursor_ratio)
        new_view_end = new_view_start + new_view_duration

        if new_view_start < 0:
            new_view_start = 0
            new_view_end = new_view_duration
        if new_view_end > self.waveform_widget.duration_ms:
            new_view_end = self.waveform_widget.duration_ms
            new_view_start = new_view_end - new_view_duration
        
        self.scroll_bar.setPageStep(int(new_view_duration))
        self.scroll_bar.setRange(0, self.waveform_widget.duration_ms - int(new_view_duration))
        self.scroll_bar.setValue(int(new_view_start))
        
        if new_view_duration >= self.waveform_widget.duration_ms:
            zoom_slider_value = 0
        elif new_view_duration <= min_view_ms:
            zoom_slider_value = 100
        else:
            max_view_ms = self.waveform_widget.duration_ms
            factor = (max_view_ms / new_view_duration - 1) / 99
            zoom_slider_value = int(factor * 100)
            
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(zoom_slider_value)
        self.zoom_slider.blockSignals(False)
    def update_times_from_waveform(self, start_ms, end_ms):
        self.start_ms, self.end_ms = start_ms, end_ms
        self.start_time_edit.blockSignals(True)
        self.end_time_edit.blockSignals(True)
        self.start_time_edit.setValue(start_ms)
        self.end_time_edit.setValue(end_ms)
        self.start_time_edit.blockSignals(False)
        self.end_time_edit.blockSignals(False)
        self.update_duration_label()

    def update_waveform_from_times(self):
        start_ms = self.start_time_edit.value()
        end_ms = self.end_time_edit.value()
        self.waveform_widget.set_selection_range(start_ms, end_ms)
        self.update_times_from_waveform(start_ms, end_ms)
        
    def update_duration_label(self):
        new_duration = self.end_ms - self.start_ms
        self.duration_label.setText(self.tr("new_duration_format").format(duration_sec=new_duration/1000, duration_ms=new_duration))

    def toggle_playback(self):
        if self.player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stop_playback(self):
        self.player.stop()
        self.waveform_widget.set_playhead(0)

    def preview_trim(self):
        self.player.setPosition(self.start_ms)
        self.player.play()
        
        def check_position(position):
            if position >= self.end_ms:
                self.player.stop()
                try: self.player.positionChanged.disconnect(check_position)
                except TypeError: pass
        
        try: self.player.positionChanged.disconnect()
        except TypeError: pass
        finally:
            self.player.positionChanged.connect(check_position)
            self.player.positionChanged.connect(self.waveform_widget.set_playhead)

    def process_trim(self):
        self.progress_widget.show()
        self.process_btn.setEnabled(False)
        
        thread = threading.Thread(target=self._process_thread)
        thread.daemon = True
        thread.start()

    def _process_thread(self):
        try:
            self.update_progress(10, "Preparing...")

            self.update_progress(20, self.tr("trimming_with_ffmpeg"))
            trimmed_wav = tempfile.NamedTemporaryFile(suffix='_trimmed.wav', delete=False).name
            self.temp_files.append(trimmed_wav)
            
            start_sec = self.start_ms / 1000.0
            duration_sec = (self.end_ms - self.start_ms) / 1000.0
            
            cmd = [
                self.ffmpeg_path, '-i', self.source_wav,
                '-ss', str(start_sec), '-t', str(duration_sec),
                '-acodec', 'pcm_s16le',
                '-ar', str(self.waveform_widget.sample_rate), 
                trimmed_wav, '-y'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo, creationflags=CREATE_NO_WINDOW)
            if result.returncode != 0:
                raise Exception(f"FFmpeg trimming failed: {result.stderr}")
            file_id = self.entry.get("Id", "")
            shortname = self.entry.get("ShortName", "")
            original_filename = os.path.splitext(shortname)[0]
            
            if self.is_mod:
                current_mod_path = self.parent.get_mod_path(file_id, self.lang)
                if not os.path.exists(current_mod_path):
                     raise Exception("Modified audio file not found")
                
                backup_path = self.parent.get_backup_path(file_id, self.lang)
                if not os.path.exists(backup_path):
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(current_mod_path, backup_path)
            
            source_wem_path = self.parent.get_original_path(file_id, self.lang)
            target_size = os.path.getsize(source_wem_path)

            file_pair = {
                "wav_file": trimmed_wav, "target_wem": source_wem_path,
                "wav_name": f"{original_filename}.wav", "target_name": f"{original_filename}.wem",
                "target_size": target_size, "language": self.lang, "file_id": file_id
            }

            self.update_progress(60, "Converting to WEM...")
            conversion_result = self.wav_converter.convert_single_file_main(file_pair, 1, 1)

            if not conversion_result.get('success'):
                raise Exception(f"WEM conversion failed: {conversion_result.get('error', 'Unknown error')}")

            self.update_progress(85, "Deploying to MOD_P...")
            target_path = self.parent.get_mod_path(file_id, self.lang)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy2(conversion_result['output_path'], target_path)

            self.update_progress(100, self.tr("status_complete"))
            QtCore.QMetaObject.invokeMethod(self, "show_success", QtCore.Qt.QueuedConnection)

        except Exception as e:
            QtCore.QMetaObject.invokeMethod(self, "show_error", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, str(e)))
    def cleanup_before_exit(self):
        if hasattr(self, 'player'):
            self.player.stop()
        
        for f in self.temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except PermissionError:
                    DEBUG.log(f"Could not delete temp file (in use?): {f}", "WARNING")
                except Exception as e:
                    DEBUG.log(f"Error deleting temp file {f}: {e}", "ERROR")
        self.temp_files = []
    def update_progress(self, value, text):
        QtCore.QMetaObject.invokeMethod(self.progress_bar, "setValue", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(int, value))
        QtCore.QMetaObject.invokeMethod(self.progress_label, "setText", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, text))

    @QtCore.pyqtSlot()
    def show_success(self):
        self.progress_widget.hide()
        QtWidgets.QMessageBox.information(self, self.tr("success"), self.tr("trim_success_msg"))
        self.parent.populate_tree(self.lang)
        self.accept()
        
    @QtCore.pyqtSlot(str)
    def show_error(self, error):
        self.progress_widget.hide()
        self.process_btn.setEnabled(True)
        QtWidgets.QMessageBox.critical(self, self.tr("error"), f"{self.tr('trim_failed_title')}:\n\n{error}")
    def accept(self):
        self.cleanup_before_exit()
        super().accept()

    def reject(self):
        self.cleanup_before_exit()
        super().reject()
    def closeEvent(self, event):
        self.cleanup_before_exit()
        super().closeEvent(event)
