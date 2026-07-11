from ._imports import *

class ConversionMixin:
    def compile_mod(self):
        if not os.path.exists(self.repak_path):
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("repak_not_found"))
            return
        
        self.progress_dialog = ProgressDialog(self, self.tr("compiling_mod"))
        self.progress_dialog.progress.setRange(0, 0)
        self.progress_dialog.details.append(f"[{datetime.now().strftime('%H:%M:%S')}] {self.tr('running_repak')}")

        self.animation_timer = QtCore.QTimer()

        self.animation_texts = [
            self.tr("compiling_step_1"),
            self.tr("compiling_step_2"),
            self.tr("compiling_step_3"),
            self.tr("compiling_step_4"),
            self.tr("compiling_step_5"),
            self.tr("compiling_step_6"),
            self.tr("compiling_step_7"),
        ]

        import random
        random.shuffle(self.animation_texts) 
        self.animation_index = 0

        def update_animation():
            if hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():

                current_text = self.animation_texts[self.animation_index]
                self.progress_dialog.label.setText(current_text)

                self.progress_dialog.details.append(f"[{datetime.now().strftime('%H:%M:%S')}] {current_text}")

                self.animation_index = (self.animation_index + 1) % len(self.animation_texts)
            else:
                self.animation_timer.stop() 
                
        self.animation_timer.timeout.connect(update_animation)

        self.animation_timer.start(2500) 
        self.progress_dialog.label.setText(self.tr("running_repak"))


        self.progress_dialog.show()

        opp_path = os.path.join(self.mod_p_path, "OPP")
        os.makedirs(opp_path, exist_ok=True)
        watermark_path = os.path.join(opp_path, "CreatedByAudioEditor.txt")
        watermark_content = f"This mod was created using OutlastTrials AudioEditor {current_version}\nCreated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            with open(watermark_path, 'w', encoding='utf-8') as f:
                f.write(watermark_content)
        except Exception:
            pass
        
        self.compile_thread = CompileModThread(self.repak_path, self.mod_p_path)

        self.compile_thread.finished.connect(self.on_compilation_finished)
        self.compile_thread.start()

    def on_compilation_finished(self, success, output):

        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()

        watermark_path = os.path.join(self.mod_p_path, "OPP", "CreatedByAudioEditor.txt")
        if os.path.exists(watermark_path):
            try:
                os.remove(watermark_path)
            except Exception:
                pass
                
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        if success:
            QtWidgets.QMessageBox.information(
                self, 
                self.tr("success"), 
                self.tr("mod_compiled_successfully")
            )
            DEBUG.log(f"Mod compilation successful:\n{output}")
        else:
            error_msg = QtWidgets.QMessageBox(self)
            error_msg.setIcon(QtWidgets.QMessageBox.Warning)
            error_msg.setWindowTitle(self.tr("error"))
            error_msg.setText(self.tr("compilation_failed"))
            error_msg.setInformativeText("See details for the output from repak.exe.")
            error_msg.setDetailedText(output)
            error_msg.exec_()
            DEBUG.log(f"Mod compilation failed:\n{output}", "ERROR")

    def select_wwise_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select WWISE Folder", 
            self.settings.data.get("last_directory", "")
        )
        
        if folder:
            self.wwise_path_edit.setText(folder)
            self.settings.data["last_directory"] = folder
            self.settings.save()

    def open_target_folder(self):
        voice_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", "English(US)")
        sfx_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media")
        loc_dir = os.path.join(self.mod_p_path, "OPP", "Content", "Localization")
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(self.tr("select_folder_to_open_title"))
        dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        label = QtWidgets.QLabel(self.tr("which_folder_to_open"))
        layout.addWidget(label)
        
        btn_layout = QtWidgets.QVBoxLayout()
        
        if os.path.exists(voice_dir):
            voice_btn = QtWidgets.QPushButton(self.tr("voice_files_folder").format(path=voice_dir))
            voice_btn.clicked.connect(lambda: (os.startfile(voice_dir), dialog.accept()))
            btn_layout.addWidget(voice_btn)
        
        if os.path.exists(sfx_dir) and sfx_dir != voice_dir:
            sfx_btn = QtWidgets.QPushButton(self.tr("sfx_files_folder").format(path=sfx_dir))
            sfx_btn.clicked.connect(lambda: (os.startfile(sfx_dir), dialog.accept()))
            btn_layout.addWidget(sfx_btn)
        
        if os.path.exists(loc_dir):
            loc_btn = QtWidgets.QPushButton(self.tr("subtitles_folder").format(path=loc_dir))
            loc_btn.clicked.connect(lambda: (os.startfile(loc_dir), dialog.accept()))
            btn_layout.addWidget(loc_btn)
        
        layout.addLayout(btn_layout)
        
        cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        if not any(os.path.exists(d) for d in [voice_dir, sfx_dir, loc_dir]):
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("no_target_folders_found"))
            return
        
        dialog.exec_()

    def create_wav_to_wem_tab(self):
        """Create simplified WAV to WEM converter tab with logs"""
        main_tab = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(main_tab)
        main_layout.setSpacing(5)
        
        self.wav_converter_tabs = QtWidgets.QTabWidget()
        
        converter_tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(converter_tab)
        layout.setSpacing(5)
        
        instructions = QtWidgets.QLabel(f"""
        <p><b>{self.tr("wav_to_wem_converter")}:</b> {self.tr("converter_instructions")}</p>
        """)
        instructions.setWordWrap(True)
        instructions.setMaximumHeight(40)
        layout.addWidget(instructions)
        
        top_section = QtWidgets.QWidget()
        top_layout = QtWidgets.QHBoxLayout(top_section)
        top_layout.setSpacing(10)
        
        mode_group = QtWidgets.QGroupBox(self.tr("conversion_mode"))
        mode_group.setMaximumHeight(120)
        mode_group.setMinimumWidth(240)
        mode_layout = QtWidgets.QVBoxLayout(mode_group)
        mode_layout.setSpacing(2)
        
        self.strict_mode_radio = QtWidgets.QRadioButton(self.tr("strict_mode"))
        self.strict_mode_radio.setChecked(True)
        self.strict_mode_radio.setToolTip(
            "Standard conversion mode. If the file is too large, an error will be thrown.\n"
            "Use this mode when you want full control over your audio files."
        )
        
        self.adaptive_mode_radio = QtWidgets.QRadioButton(self.tr("adaptive_mode"))
        self.adaptive_mode_radio.setToolTip(
            "Automatically resamples audio to lower sample rates if the file is too large.\n"
            "The system will find the optimal sample rate to match the target file size.\n"
            "Useful for batch processing when exact audio quality is less critical."
        )
        
        strict_desc = QtWidgets.QLabel(f"<small>{self.tr('strict_mode_desc')}</small>")
        strict_desc.setStyleSheet("padding-left: 20px; color: #666;")
        
        adaptive_desc = QtWidgets.QLabel(f"<small>{self.tr('adaptive_mode_desc')}</small>")
        adaptive_desc.setStyleSheet("padding-left: 20px; color: #666;")
        
        mode_layout.addWidget(self.strict_mode_radio)
        mode_layout.addWidget(strict_desc)
        mode_layout.addWidget(self.adaptive_mode_radio)
        mode_layout.addWidget(adaptive_desc)
        mode_layout.addStretch()
        
        top_layout.addWidget(mode_group)
        
        paths_group = QtWidgets.QGroupBox(self.tr("path_configuration"))
        paths_group.setMaximumHeight(120)
        paths_layout = QtWidgets.QFormLayout(paths_group)
        paths_layout.setSpacing(5)
        paths_layout.setContentsMargins(5, 5, 5, 5)
        
        wwise_widget = QtWidgets.QWidget()
        wwise_layout = QtWidgets.QHBoxLayout(wwise_widget)
        wwise_layout.setContentsMargins(0, 0, 0, 0)
        
        self.wwise_path_edit = QtWidgets.QLineEdit()
        self.wwise_path_edit.setPlaceholderText(self.tr("wwise_path_placeholder"))
        self.wwise_path_edit.setText(self.settings.data.get("wav_wwise_path", ""))
        self.wwise_path_edit.editingFinished.connect(lambda: self.settings.data.update({"wav_wwise_path": self.wwise_path_edit.text()}))
        wwise_browse_btn = QtWidgets.QPushButton("...")
        wwise_browse_btn.setMaximumWidth(30)
        wwise_browse_btn.clicked.connect(self.browse_wwise_path)
        
        wwise_layout.addWidget(self.wwise_path_edit)
        wwise_layout.addWidget(wwise_browse_btn)
        paths_layout.addRow(f"{self.tr('wwise_path')}", wwise_widget)
        
        project_widget = QtWidgets.QWidget()
        project_layout = QtWidgets.QHBoxLayout(project_widget)
        project_layout.setContentsMargins(0, 0, 0, 0)
        
        self.converter_project_path_edit = QtWidgets.QLineEdit()
        self.converter_project_path_edit.setPlaceholderText(self.tr("project_path_placeholder"))
        self.converter_project_path_edit.setText(self.settings.data.get("wav_project_path", ""))
        self.converter_project_path_edit.editingFinished.connect(lambda: self.settings.data.update({"wav_project_path": self.converter_project_path_edit.text()}))
        project_browse_btn = QtWidgets.QPushButton("...")
        project_browse_btn.setMaximumWidth(30)
        project_browse_btn.clicked.connect(self.browse_converter_project_path)
        
        project_layout.addWidget(self.converter_project_path_edit)
        project_layout.addWidget(project_browse_btn)
        paths_layout.addRow(f"{self.tr('project_path')}", project_widget)
        
        wav_widget = QtWidgets.QWidget()
        wav_layout = QtWidgets.QHBoxLayout(wav_widget)
        wav_layout.setContentsMargins(0, 0, 0, 0)
        
        self.wav_folder_edit = QtWidgets.QLineEdit()
        self.wav_folder_edit.setPlaceholderText(self.tr("wav_folder_placeholder"))
        self.wav_folder_edit.setText(self.settings.data.get("wav_folder_path", ""))
        self.wav_folder_edit.editingFinished.connect(lambda: self.settings.data.update({"wav_folder_path": self.wav_folder_edit.text()})) 
        wav_browse_btn = QtWidgets.QPushButton("...")
        wav_browse_btn.setMaximumWidth(30)
        wav_browse_btn.clicked.connect(self.browse_wav_folder)
        
        wav_layout.addWidget(self.wav_folder_edit)
        wav_layout.addWidget(wav_browse_btn)
        paths_layout.addRow(f"{self.tr('wav_path')}", wav_widget)
        
        top_layout.addWidget(paths_group)
        
        layout.addWidget(top_section)
        
        files_group = QtWidgets.QGroupBox(self.tr("files_for_conversion"))
        files_layout = QtWidgets.QVBoxLayout(files_group)
        files_layout.setSpacing(5)
        
        controls_widget = QtWidgets.QWidget()
        controls_widget.setMaximumHeight(35)
        controls_layout = QtWidgets.QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        add_all_wav_btn = QtWidgets.QPushButton(self.tr("add_all_wav"))
        add_all_wav_btn.clicked.connect(self.add_all_audio_files_auto)
        
        clear_files_btn = QtWidgets.QPushButton(self.tr("clear"))
        clear_files_btn.clicked.connect(self.clear_conversion_files)
        
        self.convert_btn = QtWidgets.QPushButton(self.tr("convert"))
        self.convert_btn.setMaximumWidth(150)
        self.convert_btn.setMaximumHeight(30)
        self.convert_btn.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                padding: 5px 15px; 
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        self.convert_btn.clicked.connect(self.toggle_conversion)
        
        self.is_converting = False
        self.conversion_thread = None
        
        self.files_count_label = QtWidgets.QLabel(self.tr("files_ready_count").format(count=0))
        self.files_count_label.setStyleSheet("font-weight: bold; color: #666;")
        
        controls_layout.addWidget(add_all_wav_btn)
        add_single_file_btn = QtWidgets.QPushButton(self.tr("add_file_btn"))
        add_single_file_btn.clicked.connect(self.add_single_audio_file)
        
        controls_layout.addWidget(add_all_wav_btn)
        controls_layout.addWidget(add_single_file_btn) 
        controls_layout.addWidget(clear_files_btn)
        controls_layout.addWidget(clear_files_btn)
        controls_layout.addWidget(self.convert_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.files_count_label)
        
        files_layout.addWidget(controls_widget)
        
        self.conversion_files_table = QtWidgets.QTableWidget()
        self.conversion_files_table.setColumnCount(5)
        self.conversion_files_table.setHorizontalHeaderLabels([
            self.tr("wav_file"), self.tr("target_wem"), self.tr("language"), 
            self.tr("target_size"), self.tr("status")
        ])
        self.conversion_files_table.setAcceptDrops(True)
        self.conversion_files_table.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
        self.conversion_files_table.viewport().setAcceptDrops(True)

        self.conversion_files_table.dragEnterEvent = self.table_dragEnterEvent
        self.conversion_files_table.dragMoveEvent = self.table_dragMoveEvent
        self.conversion_files_table.dropEvent = self.table_dropEvent
        self.conversion_files_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.conversion_files_table.customContextMenuRequested.connect(self.show_conversion_context_menu)
        
        header = self.conversion_files_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch) 
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        
        self.conversion_files_table.setAlternatingRowColors(True)
        self.conversion_files_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        files_layout.addWidget(self.conversion_files_table, 1)
        
        layout.addWidget(files_group, 1)
        
        bottom_widget = QtWidgets.QWidget()
        bottom_widget.setMaximumHeight(60)
        bottom_layout = QtWidgets.QVBoxLayout(bottom_widget)
        bottom_layout.setSpacing(2)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        progress_widget = QtWidgets.QWidget()
        progress_layout = QtWidgets.QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(10)
        
        self.conversion_progress = QtWidgets.QProgressBar()
        self.conversion_progress.setMaximumHeight(15)
        
        self.conversion_status = QtWidgets.QLabel(self.tr("ready"))
        self.conversion_status.setStyleSheet("color: #666; font-size: 11px;")
        self.conversion_status.setMinimumWidth(200)
        
        progress_layout.addWidget(self.conversion_progress)
        progress_layout.addWidget(self.conversion_status)
        
        bottom_layout.addWidget(progress_widget)
        
        layout.addWidget(bottom_widget)
        
        self.wav_converter_tabs.addTab(converter_tab, self.tr("convert"))
        
        self.create_conversion_logs_tab()
        
        main_layout.addWidget(self.wav_converter_tabs)
        
        self.wav_converter = WavToWemConverter(self)
        self.wav_converter.progress_updated.connect(self.conversion_progress.setValue)
        self.wav_converter.status_updated.connect(self.update_conversion_status)
        self.wav_converter.conversion_finished.connect(self.on_conversion_finished)
        
        self.converter_tabs.addTab(main_tab, self.tr("wav_to_wem_converter"))

    def table_dragEnterEvent(self, event):
        """Handle drag enter event for conversion table"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def table_dragMoveEvent(self, event):
        """Handle drag move event for conversion table"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def add_single_audio_file(self):
        if hasattr(self, 'add_single_thread') and self.add_single_thread.isRunning():
            QtWidgets.QMessageBox.information(self, "In Progress", "Already processing a file. Please wait.")
            return
            
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            self.settings.data.get("last_audio_dir", ""),
            "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a *.aac *.wma *.opus *.webm);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        self.settings.data["last_audio_dir"] = os.path.dirname(file_path)
        self.settings.save()
        
        progress = ProgressDialog(self, self.tr("add_single_file_title"))
        progress.setWindowFlags(progress.windowFlags() | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        progress.setWindowFlags(progress.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        progress.show()
        
        self.add_single_thread = AddSingleFileThread(self, file_path)
        self.add_single_thread.progress_updated.connect(progress.set_progress)
        self.add_single_thread.details_updated.connect(progress.append_details)
        self.add_single_thread.finished.connect(lambda success: self.on_add_single_finished(progress, success, file_path))
        self.add_single_thread.error_occurred.connect(lambda e: self.on_add_single_error(progress, e))
        
        self.add_single_thread.start()

    def on_add_single_finished(self, progress, success, file_path):
        progress.close()
        
        self.update_conversion_files_table()
        
        filename = os.path.basename(file_path)
        
        if success:
            self.status_bar.showMessage(f"Added: {filename}", 3000)
            self.append_conversion_log(f"✓ Added {filename}")
        else:
            self.status_bar.showMessage(f"File not added: {filename}", 3000)
            self.append_conversion_log(f"✗ Not added: {filename}")

    def on_add_single_error(self, progress, error):
        progress.close()
        
        QtWidgets.QMessageBox.warning(
            self, "Error",
            f"Error adding file:\n\n{error}"
        )
        
        self.append_conversion_log(f"✗ Error: {error}")

    def find_matching_wem_for_audio(self, audio_path, auto_mode=False, replace_all=False, skip_all=False):
        """Find matching WEM for audio file and add to conversion list"""
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        audio_ext = os.path.splitext(audio_path)[1].lower()
        
        selected_language = self.settings.data.get("wem_process_language", "english")
        DEBUG.log(f"Using language from settings: {selected_language}")
        
        if selected_language == "english":
            target_dir_voice = "English(US)"
            voice_lang_filter = ["English(US)"]
        elif selected_language == "french":
            target_dir_voice = "Francais"
            voice_lang_filter = ["French(France)", "Francais"]
        else:
            target_dir_voice = "English(US)"
            voice_lang_filter = ["English(US)"]
        
        existing_file_index = None

        file_pairs_copy = list(self.wav_converter.file_pairs)
        for i, pair in enumerate(file_pairs_copy):
            if pair.get('audio_file') == audio_path:
                existing_file_index = i
                break
        
        if existing_file_index is not None:
            if skip_all:
                self.append_conversion_log(f"✗ Skipped {os.path.basename(audio_path)}: Already in list")
                return False
            
            if replace_all:
                self.append_conversion_log(f"ℹ {os.path.basename(audio_path)}: Already in list (no changes)")
                return False
            
            response = QtCore.QMetaObject.invokeMethod(
                self, "_ask_for_update", QtCore.Qt.BlockingQueuedConnection,
                QtCore.Q_ARG(str, os.path.basename(audio_path))
            )

            if response == "Skip":
                self.append_conversion_log(f"✗ Skipped {os.path.basename(audio_path)}: Already in list")
                return False

        self._build_wem_index()
        
        found_entry = None
        file_id = None
        
        if audio_name.isdigit():
            file_id = audio_name

            if file_id in self.wem_index:

                for entry in self.all_files:
                    if entry.get("Id", "") == file_id:
                        found_entry = entry
                        break
                
                if not found_entry and file_id in self.wem_index:

                    available_langs = list(self.wem_index[file_id].keys())
                    language = available_langs[0] if available_langs else "SFX"
                    
                    found_entry = {
                        "Id": file_id,
                        "Language": language,
                        "ShortName": f"{file_id}.wav" 
                    }
            else:
                self.append_conversion_log(f"✗ {audio_name}: ID not found in WEM files")
                return None
        else:

            if audio_name.startswith("VO_"):
                for entry in self.all_files:
                    shortname = entry.get("ShortName", "")
                    base_shortname = os.path.splitext(shortname)[0]
                    language = entry.get("Language", "")
                    
                    if base_shortname == audio_name and language in voice_lang_filter:
                        found_entry = entry
                        file_id = entry.get("Id", "")
                        break
                
                if not found_entry and '_' in audio_name:
                    parts = audio_name.split('_')
                    if len(parts) > 1 and len(parts[-1]) == 8:
                        try:
                            int(parts[-1], 16)
                            audio_name_no_hex = '_'.join(parts[:-1])
                            for entry in self.all_files:
                                shortname = entry.get("ShortName", "")
                                base_shortname = os.path.splitext(shortname)[0]
                                language = entry.get("Language", "")
                                
                                if base_shortname == audio_name_no_hex and language in voice_lang_filter:
                                    found_entry = entry
                                    file_id = entry.get("Id", "")
                                    break
                        except ValueError:
                            pass
                
                if not found_entry:
                    self.append_conversion_log(f"✗ {audio_name}: Not found in SoundbanksInfo for language {selected_language}")
                    return None
            else:
 
                for entry in self.all_files:
                    shortname = entry.get("ShortName", "")
                    base_shortname = os.path.splitext(shortname)[0]
                    language = entry.get("Language", "")
                    
                    if base_shortname == audio_name and language == "SFX":
                        found_entry = entry
                        file_id = entry.get("Id", "")
                        break
                
                if not found_entry:
                    self.append_conversion_log(f"✗ {audio_name}: Not found in SoundbanksInfo (SFX)")
                    return None
        
        if not found_entry or not file_id:
            self.append_conversion_log(f"✗ {audio_name}: Not found in database")
            return None
        
        if file_id not in self.wem_index:
            self.append_conversion_log(f"✗ {audio_name}: WEM file for ID {file_id} not found in Wems folder")
            return None
        language_from_db = found_entry.get("Language", "SFX")
        if language_from_db in voice_lang_filter:
            language = target_dir_voice
            if target_dir_voice in self.wem_index[file_id]:
                wem_path = self.wem_index[file_id][target_dir_voice]['path']
            else:
                available_langs = list(self.wem_index[file_id].keys())
                self.append_conversion_log(f"✗ {audio_name}: WEM for voice file not found in {target_dir_voice} (available: {', '.join(available_langs)})")
                return None
        else:
            language = "SFX"
            if "SFX" in self.wem_index[file_id]:
                wem_path = self.wem_index[file_id]["SFX"]['path']
            else:
                available_langs = list(self.wem_index[file_id].keys())
                if available_langs:
                    self.append_conversion_log(f"⚠ {audio_name}: WEM for SFX not found in SFX folder, using backup from '{available_langs[0]}'")
                else:
                    self.append_conversion_log(f"✗ {audio_name}: WEM for SFX file not found in any folder")
                    return None
        
        if not wem_path or not os.path.exists(wem_path):
            self.append_conversion_log(f"✗ {audio_name}: WEM file path not valid")
            return None
        
        existing_pair_index = None
        file_pairs_copy = list(self.wav_converter.file_pairs)
        for i, pair in enumerate(file_pairs_copy):
            if pair.get('target_wem') == wem_path and i != existing_file_index:
                existing_pair_index = i
                break
        
        if existing_pair_index is not None:
            existing_pair = self.wav_converter.file_pairs[existing_pair_index]
            
            if skip_all:
                self.append_conversion_log(
                    f"✗ Skipped {os.path.basename(audio_path)}: "
                    f"Target WEM already used by {existing_pair['audio_name']}"
                )
                return False
            
            if replace_all:
                self.wav_converter.file_pairs[existing_pair_index] = {
                    "audio_file": audio_path,
                    "original_format": audio_ext,
                    "needs_conversion": audio_ext != '.wav',
                    "target_wem": wem_path,
                    "audio_name": os.path.basename(audio_path),
                    "wav_name": os.path.basename(audio_path),
                    "target_name": f"{file_id}.wem",
                    "target_size": os.path.getsize(wem_path),
                    "language": language,
                    "file_id": file_id
                }
                if existing_file_index is not None and existing_file_index != existing_pair_index:
                    del self.wav_converter.file_pairs[existing_file_index]
                self.append_conversion_log(
                    f"✓ Replaced {existing_pair['audio_name']} with {os.path.basename(audio_path)} -> {file_id}.wem"
                )
                return True
            
            response = QtCore.QMetaObject.invokeMethod(
                self, "_ask_for_replace", QtCore.Qt.BlockingQueuedConnection,
                QtCore.Q_ARG(str, file_id),
                QtCore.Q_ARG(str, existing_pair['audio_name']),
                QtCore.Q_ARG(str, os.path.basename(audio_path)),
                QtCore.Q_ARG(bool, auto_mode)
            )

            if response == "Replace":
                self.wav_converter.file_pairs[existing_pair_index] = {
                    "audio_file": audio_path,
                    "original_format": audio_ext,
                    "needs_conversion": audio_ext != '.wav',
                    "target_wem": wem_path,
                    "audio_name": os.path.basename(audio_path),
                    "wav_name": os.path.basename(audio_path),
                    "target_name": f"{file_id}.wem",
                    "target_size": os.path.getsize(wem_path),
                    "language": language,
                    "file_id": file_id
                }
                if existing_file_index is not None and existing_file_index != existing_pair_index:
                    del self.wav_converter.file_pairs[existing_file_index]
                self.append_conversion_log(
                    f"✓ Replaced {existing_pair['audio_name']} with {os.path.basename(audio_path)} -> {file_id}.wem"
                )
                return True
            elif response == "Replace All":
                return 'replace_all'
            elif response == "Skip All":
                return 'skip_all'
            else:  # Skip
                self.append_conversion_log(
                    f"✗ Skipped {os.path.basename(audio_path)}: User chose to keep {existing_pair['audio_name']}"
                )
                return False
        
        new_file_pair = {
            "audio_file": audio_path,
            "original_format": audio_ext,
            "needs_conversion": audio_ext != '.wav',
            "target_wem": wem_path,
            "audio_name": os.path.basename(audio_path),
            "wav_name": os.path.basename(audio_path),
            "target_name": f"{file_id}.wem",
            "target_size": os.path.getsize(wem_path),
            "language": language,
            "file_id": file_id
        }

        if existing_file_index is not None:
            self.wav_converter.file_pairs[existing_file_index] = new_file_pair
            self.append_conversion_log(f"✓ Updated {os.path.basename(audio_path)} -> {file_id}.wem ({language})")
        else:
            self.wav_converter.file_pairs.append(new_file_pair)
            self.append_conversion_log(f"✓ Added {os.path.basename(audio_path)} -> {file_id}.wem ({language})")
        
        return True

    def toggle_conversion(self):
        """Toggle between start and stop conversion"""
        self.settings.save()
        if not self.is_converting:
            self.start_wav_conversion()
        else:
            self.stop_wav_conversion()

    def load_converter_file_list(self):
        path = os.path.join(self.base_path, "converter_file_list.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                file_list = json.load(f)
            self.wav_converter.file_pairs.clear()
            for pair in file_list:

                audio_name = pair.get("audio_name") or pair.get("wav_name") or pair.get("target_name") or ""
                wav_name = pair.get("wav_name") or pair.get("audio_name") or pair.get("target_name") or ""
                new_pair = dict(pair)
                new_pair["audio_name"] = audio_name
                new_pair["wav_name"] = wav_name

                if new_pair.get("audio_file") and new_pair.get("target_wem"):
                    self.wav_converter.file_pairs.append(new_pair)
            self.update_conversion_files_table()
        except Exception as e:
            DEBUG.log(f"Failed to load converter file list: {e}", "ERROR")

    def create_converter_tab(self):
        """Create updated converter tab"""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5) 
        layout.setSpacing(5)
        
        header = QtWidgets.QLabel("Audio Converter & Processor")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)
        
        self.converter_tabs = QtWidgets.QTabWidget()
        
     
        self.create_wav_to_wem_tab()
        self.create_localization_exporter_simple_tab()
 
        self.create_wem_processor_main_tab()
        
        layout.addWidget(self.converter_tabs)
        
        self.tabs.addTab(tab, "Converter")

    def show_conversion_context_menu(self, pos):
        """Show context menu for conversion table"""
        item = self.conversion_files_table.itemAt(pos)
        if not item:
            return
        
        selected_rows = set()
        for selected_item in self.conversion_files_table.selectedItems():
            selected_rows.add(selected_item.row())
        
        menu = QtWidgets.QMenu()

        if len(selected_rows) == 1:
            row = item.row()
            if row >= 0 and row < len(self.wav_converter.file_pairs):
                change_target_action = menu.addAction("📁 Browse for Target WEM...")
                change_target_action.triggered.connect(lambda: self.select_custom_target_wem(row))
                
                wems_folder = os.path.join(self.base_path, "Wems")
                available_folders = []
                
                if os.path.exists(wems_folder):
                    for folder in os.listdir(wems_folder):
                        folder_path = os.path.join(wems_folder, folder)
                        if os.path.isdir(folder_path):
                            wem_count = sum(1 for f in os.listdir(folder_path) if f.endswith('.wem'))
                            if wem_count > 0:
                                available_folders.append((folder, folder_path, wem_count))
                
                if available_folders:
                    menu.addSeparator()
                    quick_menu = menu.addMenu("⚡ Quick Select")
                    
                    available_folders.sort(key=lambda x: x[2], reverse=True)
                    
                    for folder_name, folder_path, file_count in available_folders:
                        folder_action = quick_menu.addAction(f"📁 {folder_name} ({file_count} files)")
                        folder_action.triggered.connect(
                            lambda checked, p=folder_path, r=row: self.quick_select_from_folder(p, r)
                        )
                
                menu.addSeparator()
        
        if len(selected_rows) > 1:
            remove_action = menu.addAction(f"❌ Remove {len(selected_rows)} Files")
        else:
            remove_action = menu.addAction("❌ Remove")
        
        remove_action.triggered.connect(lambda: self.remove_conversion_file())
        
        menu.exec_(self.conversion_files_table.mapToGlobal(pos))

    def quick_select_from_folder(self, folder_path, row):
        """Quick select WEM from specific folder"""
        file_pair = self.wav_converter.file_pairs[row]
        wav_name = file_pair['wav_name']
        
        wem_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 
            f"Select Target WEM for {wav_name} from {os.path.basename(folder_path)}",
            folder_path,
            "WEM Audio Files (*.wem);;All Files (*.*)"
        )
        
        if not wem_file:
            return
        
        self.process_selected_wem_file(wem_file, row)

    def process_selected_wem_file(self, wem_file, row):
        """Process selected WEM file and update conversion table"""
        file_pair = self.wav_converter.file_pairs[row]
        wav_name = file_pair['wav_name']
        
        try:
           
            file_size = os.path.getsize(wem_file)
            file_name = os.path.basename(wem_file)
            file_id = os.path.splitext(file_name)[0]
           
            parent_folder = os.path.basename(os.path.dirname(wem_file))
            
            file_info = None
            for entry in self.all_files:
                if entry.get("Id", "") == file_id:
                    file_info = entry
                    break
            
            if file_info:
                language = file_info.get("Language", parent_folder)
                original_name = file_info.get("ShortName", file_name)
                self.append_conversion_log(f"Found {file_id} in database: {original_name}")
            else:
                
                language = parent_folder
                original_name = file_name
                self.append_conversion_log(f"File {file_id} not found in database, using folder name as language")
            
            self.wav_converter.file_pairs[row] = {
                "wav_file": file_pair['wav_file'],
                "target_wem": wem_file,
                "wav_name": file_pair['wav_name'],
                "target_name": file_name,
                "target_size": file_size,
                "language": language,
                "file_id": file_id
            }
            
            self.update_conversion_files_table()
            
            size_kb = file_size / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
            
            self.append_conversion_log(
                f"✓ Changed target for {wav_name}:\n"
                f"  → {file_name} (ID: {file_id})\n"
                f"  → Language: {language}\n"
                f"  → Size: {size_str}\n"
                f"  → Path: {wem_file}"
            )
            
            self.status_bar.showMessage(f"Target updated: {wav_name} → {file_name}", 3000)
            
        except Exception as e:
            self.append_conversion_log(f"✗ Error processing {wem_file}: {str(e)}")
            QtWidgets.QMessageBox.warning(
                self, "Error", 
                f"Error processing selected file:\n{str(e)}"
            )

    def select_custom_target_wem(self, row):
        """Select custom target WEM file from file system"""
        file_pair = self.wav_converter.file_pairs[row]
        wav_name = file_pair['wav_name']
        
        wems_folder = os.path.join(self.base_path, "Wems")
        if not os.path.exists(wems_folder):
            wems_folder = self.base_path
        
        wem_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 
            f"Select Target WEM for {wav_name}",
            wems_folder,
            "WEM Audio Files (*.wem);;All Files (*.*)"
        )
        
        if not wem_file:
            return
      
        self.process_selected_wem_file(wem_file, row)

    def remove_conversion_file(self, row=None):
        """Remove file(s) from conversion list"""
        if row is None:
            selected_rows = set()
            for item in self.conversion_files_table.selectedItems():
                selected_rows.add(item.row())
            
            if not selected_rows:
                return
            
            selected_rows = sorted(selected_rows, reverse=True)
            
            if len(selected_rows) > 1:
                reply = QtWidgets.QMessageBox.question(
                    self, "Confirm Removal",
                    f"Remove {len(selected_rows)} selected files?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if reply != QtWidgets.QMessageBox.Yes:
                    return
            
            removed_names = []
            for row_idx in selected_rows:
                if row_idx < len(self.wav_converter.file_pairs):
                    removed_names.append(self.wav_converter.file_pairs[row_idx]['audio_name'])
                    del self.wav_converter.file_pairs[row_idx]
            
            self.update_conversion_files_table()
            
            if len(removed_names) == 1:
                self.append_conversion_log(f"Removed {removed_names[0]} from conversion list")
            else:
                self.append_conversion_log(f"Removed {len(removed_names)} files from conversion list")
                
        else:
            if row < 0 or row >= len(self.wav_converter.file_pairs):
                return
            
            file_pair = self.wav_converter.file_pairs[row]
            wav_name = file_pair['audio_name']
            
            del self.wav_converter.file_pairs[row]
            self.update_conversion_files_table()
            self.append_conversion_log(f"Removed {wav_name} from conversion list")

    def create_conversion_logs_tab(self):
        """Create logs tab for conversion results"""
        logs_tab = QtWidgets.QWidget()
        logs_layout = QtWidgets.QVBoxLayout(logs_tab)
        
       
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        
        header_label = QtWidgets.QLabel(self.tr("conversion_logs"))
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        clear_logs_btn = QtWidgets.QPushButton(self.tr("clear_logs"))
        clear_logs_btn.setMaximumWidth(120)
        clear_logs_btn.clicked.connect(self.clear_conversion_logs)
        
        save_logs_btn = QtWidgets.QPushButton(self.tr("save_logs"))
        save_logs_btn.setMaximumWidth(120)
        save_logs_btn.clicked.connect(self.save_conversion_logs)
        
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(clear_logs_btn)
        header_layout.addWidget(save_logs_btn)
        
        logs_layout.addWidget(header_widget)
        
    
        self.conversion_logs = QtWidgets.QTextEdit()
        self.conversion_logs.setReadOnly(True)
        self.conversion_logs.setFont(QtGui.QFont("Consolas", 9))
        self.conversion_logs.setPlainText(self.tr("subtitle_export_ready"))
        
        logs_layout.addWidget(self.conversion_logs)
        
        self.wav_converter_tabs.addTab(logs_tab, self.tr("conversion_logs"))

    def clear_conversion_logs(self):
        """Clear conversion logs"""
        self.conversion_logs.clear()
        self.conversion_logs.setPlainText(self.tr("logs_cleared"))

    def save_conversion_logs(self):
        """Save conversion logs to file"""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("save_logs"),
            f"conversion_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.conversion_logs.toPlainText())
                self.update_conversion_status(self.tr("logs_saved"), "green")
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self, self.tr("error"), 
                    f"{self.tr('error_saving_logs')}: {str(e)}"
                )

    def append_conversion_log(self, message, level="INFO"):
        self.log_signal.emit(message, level)

    def add_all_audio_files_auto(self):
        if hasattr(self, 'add_files_thread') and self.add_files_thread.isRunning():
            QtWidgets.QMessageBox.information(self, "In Progress", "A file search is already in progress. Please wait.")
            return

        audio_folder = self.wav_folder_edit.text()

        if not audio_folder or not os.path.exists(audio_folder):
            QtWidgets.QMessageBox.warning(
                self, self.tr("error"), 
                "Please select folder with audio files"
            )
            return
        self.settings.save()
        progress = ProgressDialog(self, "Adding Files")
        progress.show()
        
        self.add_files_thread = AddFilesThread(self, audio_folder)
        self.add_files_thread.progress_updated.connect(progress.set_progress)
        self.add_files_thread.details_updated.connect(progress.append_details)
        self.add_files_thread.finished.connect(lambda a, r, s, n: self.on_add_files_finished(progress, a, r, s, n))
        self.add_files_thread.error_occurred.connect(lambda e: self.on_add_files_error(progress, e))
        
        self.add_files_thread.start()

    def table_dropEvent(self, event):

        if not event.mimeData().hasUrls():
            event.ignore()
            return
        
        file_paths = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                file_paths.append(file_path)
        
        if not file_paths:
            event.ignore()
            return
        
        progress = ProgressDialog(self, self.tr("drop_audio_title"))
        progress.setWindowFlags(progress.windowFlags() | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        progress.setWindowFlags(progress.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        progress.show()
        
        self.drop_files_thread = DropFilesThread(self, file_paths)
        self.drop_files_thread.progress_updated.connect(progress.set_progress)
        self.drop_files_thread.details_updated.connect(progress.append_details)
        self.drop_files_thread.finished.connect(lambda a, r, s, n: self.on_drop_files_finished(progress, a, r, s, n))
        self.drop_files_thread.error_occurred.connect(lambda e: self.on_drop_files_error(progress, e))
        
        self.drop_files_thread.start()
        
        event.acceptProposedAction()

    def on_drop_files_error(self, progress, error):
        progress.close()
        
        QtWidgets.QMessageBox.warning(
            self, "Error",
            f"Error during file drop:\n\n{error}"
        )
        
        self.append_conversion_log(f"✗ Error: {error}")

    def save_converter_file_list(self):
        file_list = []
        for pair in self.wav_converter.file_pairs:
            audio_name = pair.get("audio_name") or pair.get("wav_name") or pair.get("target_name") or ""
            wav_name = pair.get("wav_name") or pair.get("audio_name") or pair.get("target_name") or ""
            file_list.append({
                "audio_file": pair.get("audio_file") or pair.get("wav_file"),
                "target_wem": pair.get("target_wem"),
                "audio_name": audio_name,
                "wav_name": wav_name,
                "target_name": pair.get("target_name"),
                "target_size": pair.get("target_size"),
                "language": pair.get("language"),
                "file_id": pair.get("file_id")
            })
        try:
            with open(os.path.join(self.base_path, "converter_file_list.json"), "w", encoding="utf-8") as f:
                json.dump(file_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            DEBUG.log(f"Failed to save converter file list: {e}", "ERROR")

    def determine_language(self, language_from_soundbank):
        lang_map = {
            'English(US)': 'English(US)',
            'French(France)': 'French(France)', 
            'Francais': 'French(France)',
            'SFX': 'SFX'
        }
        
        return lang_map.get(language_from_soundbank, 'SFX')

    def update_conversion_files_table(self):
        """Update conversion files table with tooltips"""
        self.conversion_files_table.setRowCount(len(self.wav_converter.file_pairs))
        
        for i, pair in enumerate(self.wav_converter.file_pairs):
            audio_name = pair.get('audio_name') or pair.get('wav_name', 'Unknown')
            audio_file = pair.get('audio_file') or pair.get('wav_file', '')
            
            format_info = ""
            if pair.get('original_format') and pair['original_format'] != '.wav':
                format_info = f" [{pair['original_format']}]"
            
            audio_item = QtWidgets.QTableWidgetItem(audio_name + format_info)
            audio_item.setFlags(audio_item.flags() & ~QtCore.Qt.ItemIsEditable)
            audio_item.setToolTip(f"Path: {audio_file}")
            
            if pair.get('needs_conversion', False):
                audio_item.setBackground(QtGui.QColor(255, 245, 220))
            
            self.conversion_files_table.setItem(i, 0, audio_item)
            
            wem_display = f"{pair['file_id']}.wem"
            wem_item = QtWidgets.QTableWidgetItem(wem_display)
            wem_item.setFlags(wem_item.flags() & ~QtCore.Qt.ItemIsEditable)
            wem_item.setToolTip(f"Source: {pair['target_wem']}")
            self.conversion_files_table.setItem(i, 1, wem_item)

            lang_item = QtWidgets.QTableWidgetItem(pair['language'])
            lang_item.setFlags(lang_item.flags() & ~QtCore.Qt.ItemIsEditable)
            
            if self.settings.data["theme"] == "dark":
                if pair['language'] == 'English(US)':
                    lang_item.setBackground(QtGui.QColor(30, 60, 30)) 
                elif pair['language'] == 'Francais':
                    lang_item.setBackground(QtGui.QColor(30, 30, 60))
            else:
                if pair['language'] == 'English(US)':
                    lang_item.setBackground(QtGui.QColor(230, 255, 230)) 
                elif pair['language'] == 'Francais':
                    lang_item.setBackground(QtGui.QColor(230, 230, 255)) 
                
            self.conversion_files_table.setItem(i, 2, lang_item)
            
            size_kb = pair['target_size'] / 1024
            size_item = QtWidgets.QTableWidgetItem(f"{size_kb:.1f} KB")
            size_item.setFlags(size_item.flags() & ~QtCore.Qt.ItemIsEditable)
            size_item.setToolTip(f"Exact size: {pair['target_size']:,} bytes")
            self.conversion_files_table.setItem(i, 3, size_item)
            
            status_text = self.tr("ready")
            if pair.get('needs_conversion', False):
                status_text += " (conversion needed)"
            
            status_item = QtWidgets.QTableWidgetItem(status_text)
            status_item.setFlags(status_item.flags() & ~QtCore.Qt.ItemIsEditable)
            status_item.setToolTip("File ready for conversion")
            self.conversion_files_table.setItem(i, 4, status_item)
        
        count = len(self.wav_converter.file_pairs)
        self.files_count_label.setText(self.tr("files_ready_count").format(count=count))
        
        if count > 0:
            self.files_count_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        else:
            self.files_count_label.setStyleSheet("font-weight: bold; color: #666;")

    def start_wav_conversion(self):
        """Start WAV file conversion"""
        if not self.wav_converter.file_pairs:
            QtWidgets.QMessageBox.warning(
                self, self.tr("warning"), 
                self.tr("add_files_warning")
            )
            return
        
        if not all([self.wwise_path_edit.text(), self.converter_project_path_edit.text()]):
            QtWidgets.QMessageBox.warning(
                self, self.tr("error"), 
                "Please specify Wwise and project paths!"
            )
            return
        
        self.append_conversion_log("=== CONVERSION DIAGNOSTICS ===")
        self.append_conversion_log(f"Wwise path: {self.wwise_path_edit.text()}")
        self.append_conversion_log(f"Project path: {self.converter_project_path_edit.text()}")
        self.append_conversion_log(f"Files to convert: {len(self.wav_converter.file_pairs)}")
        self.append_conversion_log(f"Adaptive mode: {self.adaptive_mode_radio.isChecked()}")
        
        wwise_path = self.wwise_path_edit.text()
        project_path = self.converter_project_path_edit.text()
        
        if not os.path.exists(wwise_path):
            self.append_conversion_log(f"ERROR: Wwise path does not exist: {wwise_path}")
            QtWidgets.QMessageBox.warning(self, "Error", f"Wwise path does not exist:\n{wwise_path}")
            return
        
        if not os.path.exists(project_path):
            os.makedirs(project_path, exist_ok=True)
            
        self.set_conversion_state(True)
        
        self.wav_converter.set_adaptive_mode(self.adaptive_mode_radio.isChecked())
        
        temp_output = os.path.join(self.base_path, "temp_wem_output")
        os.makedirs(temp_output, exist_ok=True)
        
        self.wav_converter.set_paths(wwise_path, project_path, temp_output)
        
        for i in range(self.conversion_files_table.rowCount()):
            status_item = self.conversion_files_table.item(i, 4)
            status_item.setText(self.tr("waiting"))
            status_item.setBackground(QtGui.QColor(255, 255, 200))
        
        self.conversion_progress.setValue(0)
        
        mode_text = self.tr("adaptive_mode") if self.adaptive_mode_radio.isChecked() else self.tr("strict_mode")
        self.update_conversion_status(
            self.tr("starting_conversion").format(mode=mode_text), 
            "blue"
        )
        self.append_conversion_log(f"=== {self.tr('starting_conversion').format(mode=mode_text.upper())} ===")
        
        self.conversion_thread = threading.Thread(target=self.wav_converter.convert_all_files)
        self.conversion_thread.daemon = True  
        self.conversion_thread.start()

    def set_conversion_state(self, converting):
        """Set the conversion state and update UI accordingly"""
        self.is_converting = converting
        
        if converting:

            self.convert_btn.setText("Stop")
            self.convert_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #F44336; 
                    color: white; 
                    font-weight: bold; 
                    padding: 5px 15px; 
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
            """)
            
            self.strict_mode_radio.setEnabled(False)
            self.adaptive_mode_radio.setEnabled(False)
            self.wwise_path_edit.setEnabled(False)
            self.converter_project_path_edit.setEnabled(False)
            self.wav_folder_edit.setEnabled(False)
            
        else:

            self.convert_btn.setText(self.tr("convert"))
            self.convert_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #4CAF50; 
                    color: white; 
                    font-weight: bold; 
                    padding: 5px 15px; 
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            
            self.strict_mode_radio.setEnabled(True)
            self.adaptive_mode_radio.setEnabled(True)
            self.wwise_path_edit.setEnabled(True)
            self.converter_project_path_edit.setEnabled(True)
            self.wav_folder_edit.setEnabled(True)
            
            self.wav_converter.reset_state()

    def stop_wav_conversion(self):
        """Stop the current conversion process"""
        if self.is_converting:
      
            self.wav_converter.stop_conversion()
            
            self.update_conversion_status("Stopping conversion...", "orange")
            self.append_conversion_log("User requested conversion stop")
            
            if hasattr(self, 'conversion_thread') and self.conversion_thread and self.conversion_thread.is_alive():
                self.conversion_thread.join(timeout=3.0)
                
                if self.conversion_thread.is_alive():
                    self.append_conversion_log("Warning: Conversion thread did not stop gracefully")
            
            self.set_conversion_state(False)
            self.update_conversion_status("Conversion stopped by user", "red")
            self.append_conversion_log("Conversion stopped")
            
            self.conversion_progress.setValue(0)

    def on_add_files_finished(self, progress, added, replaced, skipped, not_found):
        progress.close()
        
        self.update_conversion_files_table()
        
        message = f"Added {added} files"
        if replaced > 0:
            message += f"\nReplaced {replaced} files"
        if skipped > 0:
            message += f"\nSkipped {skipped} files"
        if not_found > 0:
            message += f"\n{not_found} files not found in database"
        
        self.append_conversion_log(f"\nResults:\n{message}")
        
        if skipped > 0 or not_found > 0:
            message += "\n\nDetails (see Logs tab for full report):"
            message += "\n- Skipped files: Check Logs for reasons (duplicates, user choice, etc.)"
            message += "\n- Not found: Files without matching WEM/ID in database"
        
        self.save_converter_file_list()
        QtWidgets.QMessageBox.information(self, self.tr("search_complete"), message)

    def on_drop_files_finished(self, progress, added, replaced, skipped, not_found):
        progress.close()
        
        self.update_conversion_files_table()
        
        message = f"Added {added} files"
        if replaced > 0:
            message += f"\nReplaced {replaced} files"
        if skipped > 0:
            message += f"\nSkipped {skipped} files"
        if not_found > 0:
            message += f"\n{not_found} files not found in database"
        
        self.append_conversion_log(f"\nDrop Results:\n{message}")
        
        if skipped > 0 or not_found > 0:
            message += "\n\nDetails (see Logs tab for full report):"
            message += "\n- Skipped files: Check Logs for reasons (duplicates, user choice, etc.)"
            message += "\n- Not found: Files without matching WEM/ID in database"
        
        self.save_converter_file_list()
        QtWidgets.QMessageBox.information(self, self.tr("search_complete"), message)

    def on_add_files_error(self, progress, error):
        progress.close()
        
        QtWidgets.QMessageBox.warning(
            self, "Error",
            f"Error during file addition:\n\n{error}"
        )
        
        self.append_conversion_log(f"✗ Error: {error}")

    def on_conversion_finished(self, results):
        """Handle conversion completion with logging"""
        try:
            successful = [r for r in results if r['result'].get('success', False)]
            failed = [r for r in results if not r['result'].get('success', False)]
            size_warnings = [r for r in results if r['result'].get('size_warning', False)]
            resampled = [r for r in successful if r['result'].get('resampled', False)]
            stopped = [r for r in results if r['result'].get('stopped', False)]
            
            self.conversion_progress.setValue(100)
        
            self.append_conversion_log("=" * 50)
            
            if stopped:
                self.append_conversion_log("CONVERSION STOPPED BY USER")
                self.update_conversion_status("Conversion stopped", "orange")
            else:
                self.append_conversion_log("CONVERSION RESULTS")
            
            self.append_conversion_log("=" * 50)
            self.append_conversion_log(f"Successful: {len(successful)}")
            if resampled:
                self.append_conversion_log(f"Resampled: {len(resampled)}")
            self.append_conversion_log(f"Failed: {len(failed)}")
            if size_warnings:
                self.append_conversion_log(f"Size warnings: {len(size_warnings)}")
            if stopped:
                self.append_conversion_log(f"Stopped: {len(stopped)}")
        
            for i, result_item in enumerate(results):
                if i < self.conversion_files_table.rowCount():
                    status_item = self.conversion_files_table.item(i, 4)
                    result = result_item['result']
                    wav_name = result_item['file_pair']['audio_name']
                    
                    if result.get('stopped', False):
                        status_item.setText("⏹ Stopped")
                        status_item.setBackground(QtGui.QColor(255, 200, 100))
                        status_item.setToolTip("Conversion stopped by user")
                        self.append_conversion_log(f"⏹ {wav_name}: Stopped by user")
                        
                    elif result.get('success', False):
                        size_diff = result.get('size_diff_percent', 0)
                        status_text = "✓ Done"
                        tooltip_text = "Converted successfully"
                        
                        if result.get('resampled', False):
                            sample_rate = result.get('sample_rate', 'unknown')
                            status_text = f"✓ Done ({sample_rate}Hz)"
                            tooltip_text = f"Converted with resampling to {sample_rate}Hz"
                        
                        if size_diff > 2:
                            status_text += f" (~{size_diff:.1f}%)"
                            status_item.setBackground(QtGui.QColor(255, 255, 200))
                        else:
                            status_item.setBackground(QtGui.QColor(230, 255, 230))
                        
                        status_item.setText(status_text)
                        status_item.setToolTip(tooltip_text)
                
                        final_size = result.get('final_size', 0)
                        attempts = result.get('attempts', 0)
                        conversion = result.get('conversion', 'N/A')
                        language = result_item['file_pair']['language']
                        
                        log_msg = f"✓ {wav_name} -> {language} ({final_size:,} bytes, attempts: {attempts}, Conversion: {conversion})"
                        if result.get('resampled', False):
                            log_msg += f" [Resampled to {result.get('sample_rate')}Hz]"
                        
                        self.append_conversion_log(log_msg)
                        
                    else:
                        if result.get('size_warning', False):
                            status_item.setText("⚠ Size")
                            status_item.setBackground(QtGui.QColor(255, 200, 200))
                        else:
                            status_item.setText("✗ Error")
                            status_item.setBackground(QtGui.QColor(255, 230, 230))
                        
                        status_item.setToolTip(result['error'])
                        self.append_conversion_log(f"✗ {wav_name}: {result['error']}")
            
            if successful and not stopped:
                self.update_conversion_status("Deploying files...", "blue")
                self.append_conversion_log("Deploying files...")
                
                try:
                    deployed_count = self.auto_deploy_converted_files_by_language(successful)
                    
                    self.update_conversion_status(
                        f"Done! Converted: {len(successful)}, deployed: {deployed_count}", 
                        "green"
                    )
                    
                    self.append_conversion_log(f"Files deployed to MOD_P: {deployed_count}")
                    self.append_conversion_log("Conversion completed successfully!")

                    message = f"Conversion completed!\n\nSuccessful: {len(successful)}\nFailed: {len(failed)}"
                    if size_warnings:
                        message += f"\nSize warnings: {len(size_warnings)}"
                    
                    QtWidgets.QMessageBox.information(
                        self, "Conversion Complete", message
                    )
                    
                except Exception as e:
                    self.update_conversion_status("Deployment error", "red")
                    self.append_conversion_log(f"DEPLOYMENT ERROR: {str(e)}")
                    QtWidgets.QMessageBox.warning(
                        self, "Error", 
                        f"Conversion complete, but deployment error:\n{str(e)}"
                    )
            elif stopped:
                self.update_conversion_status("Conversion stopped by user", "orange")
                QtWidgets.QMessageBox.information(
                    self, "Conversion Stopped", 
                    f"Conversion was stopped by user.\n\nCompleted: {len(successful)}\nRemaining: {len(stopped)}"
                )
            else:
                self.update_conversion_status("Conversion failed", "red")
                self.append_conversion_log("All files failed to convert")

                self.wav_converter_tabs.setCurrentIndex(1)
                
                QtWidgets.QMessageBox.warning(
                    self, "Error", 
                    f"All files failed to convert: {len(failed)} files.\n"
                    f"See logs for details."
                )
        finally:
            self.set_conversion_state(False)

    def auto_deploy_converted_files_by_language(self, successful_conversions):
        deployed_count = 0
        
        for conversion in successful_conversions:
            try:
                source_path = conversion['result']['output_path']
                file_pair = conversion['file_pair']
                language = file_pair['language']
                file_id = file_pair['file_id']
                
                # UPDATE: Deploy to 'Media' subfolder
                if language == "SFX":
                    target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media")
                else:
                    target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", language)
                
                os.makedirs(target_dir, exist_ok=True)
                
                dest_filename = f"{file_id}.wem"
                dest_path = os.path.join(target_dir, dest_filename)
                
                shutil.copy2(source_path, dest_path)
                deployed_count += 1
                
                DEBUG.log(f"Deployed: {file_pair['audio_name']} -> {dest_filename} in {language} (Media folder)")
                
            except Exception as e:
                DEBUG.log(f"Error deploying {file_pair['audio_name']}: {e}", "ERROR")
                raise e
        
        return deployed_count

    def auto_deploy_converted_files(self, successful_conversions):
       
        language = self.target_language_combo.currentText()
        
        if language == "SFX":
            target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows")
        else:
            target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", language)
        
        os.makedirs(target_dir, exist_ok=True)
        
        copied_count = 0
        for conversion in successful_conversions:
            try:
                source_path = conversion['result']['output_path']
                filename = os.path.basename(source_path)
                dest_path = os.path.join(target_dir, filename)
                
                shutil.copy2(source_path, dest_path)
                copied_count += 1
                
                DEBUG.log(f"Deployed: {filename} to {language}")
                
            except Exception as e:
                DEBUG.log(f"Error deploying {filename}: {e}", "ERROR")
                raise e
        
        DEBUG.log(f"Auto-deployed {copied_count} files to {target_dir}")

    def update_conversion_status(self, message, color="green"):
        color_map = {
            "green": "#4CAF50",
            "blue": "#2196F3", 
            "red": "#F44336",
            "orange": "#FF9800"
        }
        self.conversion_status.setText(message)
        self.conversion_status.setStyleSheet(f"color: {color_map.get(color, color)};")
