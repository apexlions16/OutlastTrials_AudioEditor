from ._imports import *

class LocalizationMixin:
    def load_subtitles(self):
        DEBUG.log("=== Loading Subtitles (Profile-aware) ===")
        self.subtitles = {}
        self.original_subtitles = {}
        self.all_subtitle_files = {}

        self.scan_localization_folder()

        subtitle_lang = self.settings.data["subtitle_lang"]
        self.load_subtitles_for_language(subtitle_lang)

        self.modified_subtitles.clear()
        for key, value in self.subtitles.items():
            if key in self.original_subtitles and self.original_subtitles[key] != value:
                self.modified_subtitles.add(key)

            elif key not in self.original_subtitles:
                self.modified_subtitles.add(key)
        
        DEBUG.log(f"Found {len(self.modified_subtitles)} modified subtitles after comparing with originals.")
        DEBUG.log("=== Subtitle Loading Complete ===")

    def scan_localization_folder(self):
        """Scan Localization folder for all subtitle files"""
        localization_path = os.path.join(self.base_path, "Localization")
        DEBUG.log(f"Scanning localization folder: {localization_path}")
        
        self.all_subtitle_files = {}
        
        if not os.path.exists(localization_path):
            DEBUG.log("Localization folder not found, creating structure", "WARNING")

            os.makedirs(localization_path, exist_ok=True)

            default_langs = ["en", "ru-RU", "fr-FR", "de-DE", "es-ES"]
            for lang in default_langs:
                lang_path = os.path.join(localization_path, "OPP_Subtitles", lang)
                os.makedirs(lang_path, exist_ok=True)

                locres_path = os.path.join(lang_path, "OPP_Subtitles.locres")
                if not os.path.exists(locres_path):

                    empty_subtitles = {}
                    self.create_empty_locres_file(locres_path, empty_subtitles)

            return self.scan_localization_folder()

        try:
            for item in os.listdir(localization_path):
                item_path = os.path.join(localization_path, item)
                
                if not os.path.isdir(item_path):
                    continue
                    
                DEBUG.log(f"Found subtitle category: {item}")

                try:
                    for lang_item in os.listdir(item_path):
                        lang_path = os.path.join(item_path, lang_item)
                        
                        if not os.path.isdir(lang_path):
                            continue
                            
                        DEBUG.log(f"Found language folder: {lang_item} in {item}")
   
                        try:
                            for file_item in os.listdir(lang_path):
                                if file_item.endswith('.locres') and not file_item.endswith('_working.locres'):
                                    file_path = os.path.join(lang_path, file_item)
                                    
                                    key = f"{item}/{lang_item}/{file_item}"
                                    self.all_subtitle_files[key] = {
                                        'path': file_path,
                                        'category': item,
                                        'language': lang_item,
                                        'filename': file_item,
                                        'relative_path': f"Localization/{item}/{lang_item}/{file_item}"
                                    }
                                    
                                    DEBUG.log(f"Found subtitle file: {key}")
                                    
                        except PermissionError:
                            DEBUG.log(f"Permission denied accessing {lang_path}", "WARNING")
                            continue
                            
                except PermissionError:
                    DEBUG.log(f"Permission denied accessing {item_path}", "WARNING")
                    continue
                    
        except Exception as e:
            DEBUG.log(f"Error scanning localization folder: {e}", "ERROR")
        
        DEBUG.log(f"Total subtitle files found: {len(self.all_subtitle_files)}")

    def create_empty_locres_file(self, path, subtitles):
        """Create an empty locres file using a two-step process."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                pass 
            DEBUG.log(f"Created empty placeholder locres file at: {path}")

            csv_path = path.replace('.locres', '.csv')
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)

                writer.writerow(["Key", "Source", "Translation"])
            
            if os.path.exists(self.unreal_locres_path):
                result = subprocess.run(
                    [self.unreal_locres_path, "import", path, csv_path],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(self.unreal_locres_path) or ".",
                    startupinfo=startupinfo,
                    creationflags=CREATE_NO_WINDOW,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                if result.returncode != 0:

                    DEBUG.log(f"UnrealLocres.exe failed during import for {path}: {result.stderr}", "WARNING")

            if os.path.exists(csv_path):
                os.remove(csv_path)
                
        except Exception as e:
            DEBUG.log(f"Error creating empty locres file at {path}: {e}", "ERROR")

    def load_subtitles_for_language(self, language):
        DEBUG.log(f"Loading subtitles for language: {language}")
        
        self.subtitles = {}
        self.original_subtitles = {}
        self.key_to_file_map = {}

        DEBUG.log("--- Loading original subtitles and building key map ---")
        for key, file_info in self.all_subtitle_files.items():
            if file_info['language'] == language:
                try:
                    original_data = self.locres_manager.export_locres(file_info['path'])
                    self.original_subtitles.update(original_data)

                    for sub_key in original_data:
                        self.key_to_file_map[sub_key] = file_info
                except Exception as e:
                    DEBUG.log(f"Failed to load original subtitles from {file_info['path']}: {e}", "ERROR")

        self.subtitles = self.original_subtitles.copy()
        DEBUG.log(f"Loaded {len(self.original_subtitles)} original subtitle entries and mapped them to files.")

        if self.mod_p_path and os.path.exists(self.mod_p_path):
            DEBUG.log(f"--- Loading modded subtitles from profile: {self.active_profile_name} ---")
            mod_loc_path = os.path.join(self.mod_p_path, "OPP", "Content", "Localization")
            
            if os.path.exists(mod_loc_path):
                for key, file_info in self.all_subtitle_files.items():
                    if file_info['language'] == language:
                        mod_file_path = os.path.join(mod_loc_path, file_info['category'], file_info['language'], file_info['filename'])
                        
                        if os.path.exists(mod_file_path):
                            DEBUG.log(f"Found modded subtitle file: {mod_file_path}")
                            try:
                                mod_data = self.locres_manager.export_locres(mod_file_path)
                                self.subtitles.update(mod_data)
                                DEBUG.log(f"Applied {len(mod_data)} subtitle entries from mod file.")
                            except Exception as e:
                                DEBUG.log(f"Failed to load mod subtitles from {mod_file_path}: {e}", "ERROR")
            else:
                DEBUG.log("No Localization folder in active mod profile.")
        else:
            DEBUG.log("No active mod profile to load modded subtitles from.")

    def create_resource_updater_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setSpacing(5)
        header_layout.addWidget(QtWidgets.QLabel(f"<h2>{self.tr('updater_header')}</h2>"))
        desc_label = QtWidgets.QLabel(self.tr("updater_description"))
        desc_label.setWordWrap(True)
        header_layout.addWidget(desc_label)
        layout.addLayout(header_layout)

        pak_group_layout = QtWidgets.QFormLayout()
        pak_group_layout.setSpacing(10)
        pak_group_layout.setContentsMargins(0, 10, 0, 0)
        
        self.pak_path_edit = QtWidgets.QLineEdit()
        self.pak_path_edit.setPlaceholderText(self.tr("pak_file_path_placeholder"))
        if self.settings.data.get("game_path"):
            potential_pak = os.path.join(self.settings.data.get("game_path"), "OPP", "Content", "Paks", "OPP-WindowsClient.pak")
            if os.path.exists(potential_pak):
                self.pak_path_edit.setText(potential_pak)
        
        pak_browse_btn = QtWidgets.QPushButton(self.tr("browse"))
        pak_browse_btn.clicked.connect(self.browse_for_pak)
        
        pak_widget = QtWidgets.QWidget()
        pak_widget_layout = QtWidgets.QHBoxLayout(pak_widget)
        pak_widget_layout.setContentsMargins(0,0,0,0)
        pak_widget_layout.addWidget(self.pak_path_edit)
        pak_widget_layout.addWidget(pak_browse_btn)

        pak_group_layout.addRow(f"<b>1. {self.tr('pak_file_path_label')}</b>", pak_widget)
        layout.addLayout(pak_group_layout)
        
        res_group_layout = QtWidgets.QFormLayout()
        res_group_layout.setSpacing(10)

        res_widget = QtWidgets.QWidget()
        res_layout = QtWidgets.QHBoxLayout(res_widget)
        res_layout.setContentsMargins(0,0,0,0)
        self.update_audio_check = QtWidgets.QCheckBox(self.tr("update_audio_check"))
        self.update_audio_check.setChecked(True)
        self.update_loc_check = QtWidgets.QCheckBox(self.tr("update_localization_check"))
        self.update_loc_check.setChecked(True)
        res_layout.addWidget(self.update_audio_check)
        res_layout.addWidget(self.update_loc_check)
        res_layout.addStretch()
        
        res_group_layout.addRow(f"<b>2. {self.tr('select_resources_group')}:</b>", res_widget)
        layout.addLayout(res_group_layout)
        
        button_layout = QtWidgets.QHBoxLayout()
        self.start_update_btn = QtWidgets.QPushButton(self.tr("start_update_btn"))
        self.start_update_btn.setMinimumHeight(20)
        self.start_update_btn.clicked.connect(self.start_update_process)
        
        self.cancel_update_btn = QtWidgets.QPushButton(self.tr("cancel"))
        self.cancel_update_btn.setMinimumHeight(20)
        self.cancel_update_btn.clicked.connect(self.cancel_update_process)
        self.cancel_update_btn.hide() 

        button_layout.addWidget(self.start_update_btn)
        button_layout.addWidget(self.cancel_update_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.update_progress_group = QtWidgets.QGroupBox(f"3. {self.tr('update_process_group')}")
        progress_layout = QtWidgets.QVBoxLayout(self.update_progress_group)

        self.update_progress_bar = QtWidgets.QProgressBar()
        self.update_status_label = QtWidgets.QLabel(self.tr("update_log_ready"))
        self.update_status_label.setStyleSheet("font-weight: bold;")
        self.update_fun_status_label = QtWidgets.QLabel("") 
        self.update_fun_status_label.setStyleSheet("color: #888; font-style: italic;")
        self.update_log_widget = QtWidgets.QTextEdit()
        self.update_log_widget.setReadOnly(True)
        self.update_log_widget.setFont(QtGui.QFont("Consolas", 9))
        self.update_log_widget.setMaximumHeight(250)

        progress_layout.addWidget(self.update_status_label)
        progress_layout.addWidget(self.update_fun_status_label)
        progress_layout.addWidget(self.update_progress_bar)
        progress_layout.addWidget(self.update_log_widget)
        
        layout.addWidget(self.update_progress_group)
        layout.addStretch()

        self.tabs.addTab(tab, self.tr("resource_updater_tab"))

    def browse_for_pak(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Game Pak file", self.settings.data.get("game_path", ""), "Pak files (*.pak)")
        if path:
            self.pak_path_edit.setText(path)

    def on_major_step_update(self, message, progress):
        self.update_status_label.setText(message)
        self.update_progress_bar.setValue(progress)

    def update_animation_text(self):

        if hasattr(self, 'animation_texts') and self.animation_texts:
            text = self.animation_texts[self.animation_index]
            self.update_fun_status_label.setText(f"-> {text}")
            self.animation_index = (self.animation_index + 1) % len(self.animation_texts)

    def start_update_process(self):
        pak_path = self.pak_path_edit.text()
        update_audio = self.update_audio_check.isChecked()
        update_loc = self.update_loc_check.isChecked()

        if not pak_path or not os.path.exists(pak_path):
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("pak_file_not_selected"))
            return

        if not update_audio and not update_loc:
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("no_resources_selected"))
            return

        folders_to_replace = []
        if update_audio: folders_to_replace.append("Wems")
        if update_loc: folders_to_replace.append("Localization")

        reply = QtWidgets.QMessageBox.question(self, self.tr("update_confirm_title"),
                                    self.tr("update_confirm_msg").format(resource_folder=", ".join(folders_to_replace)),
                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.No:
            return

        self.start_update_btn.hide()
        self.cancel_update_btn.show()
        self.pak_path_edit.setEnabled(False)
        self.update_audio_check.setEnabled(False)
        self.update_loc_check.setEnabled(False)
        
        self.update_log_widget.clear()
        self.update_status_label.setText(self.tr("update_process_started"))
        self.update_fun_status_label.show()
        self.update_progress_bar.setRange(0, 0)
        self.update_start_time = time.time()
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.timeout.connect(self.update_elapsed_time)
        self.update_timer.start(1000) 
        self.update_elapsed_time()

        self.animation_timer = QtCore.QTimer(self)
        self.animation_texts = [
            self.tr("update_fun_status_1"), self.tr("update_fun_status_2"),
            self.tr("update_fun_status_3"), self.tr("update_fun_status_4"),
            self.tr("update_fun_status_5"), self.tr("update_fun_status_6"),
            self.tr("update_fun_status_7"),
        ]
        import random
        random.shuffle(self.animation_texts)
        self.animation_index = 0
        self.animation_timer.timeout.connect(self.update_animation_text)
        self.animation_timer.start(3000)
        self.update_animation_text()

        self.updater_thread = ResourceUpdaterThread(self, pak_path, update_audio, update_loc)
        self.updater_thread.major_step_update.connect(self.update_status_label.setText)
        self.updater_thread.log_update.connect(self.update_log_widget.append)
        self.updater_thread.finished.connect(self.on_update_finished)
        self.updater_thread.start()

    def cancel_update_process(self):
        if hasattr(self, 'updater_thread') and self.updater_thread.isRunning():
            self.updater_thread.cancel()

    def update_elapsed_time(self):
        if not hasattr(self, 'update_start_time'):
            return

        elapsed_seconds = int(time.time() - self.update_start_time)
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        time_str = f"({minutes:02d}:{seconds:02d})"
        
      
        current_status = self.update_status_label.text().split(" (")[0]
        self.update_status_label.setText(f"{current_status} {time_str}")

    def on_update_finished(self, status, message):
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()

        self.start_update_btn.show()
        self.cancel_update_btn.hide()
        self.pak_path_edit.setEnabled(True)
        self.update_audio_check.setEnabled(True)
        self.update_loc_check.setEnabled(True)
        
        self.update_fun_status_label.hide()
        
        self.update_progress_bar.setRange(0, 100)
        
        if status == "success":
            self.update_status_label.setText(self.tr('done'))
            self.update_progress_bar.setValue(100)
            
            audio_was_updated = self.update_audio_check.isChecked()
            if audio_was_updated:

                self.update_log_widget.append(f"\n--- {self.tr('update_rescanning_orphans')} ---")
                self.status_bar.showMessage(self.tr("update_rescanning_orphans"), 0)
                QtWidgets.QApplication.processEvents() 
                
                self.perform_blocking_orphan_scan()
            QtWidgets.QMessageBox.information(self, self.tr("update_complete_title"), f"{message}\n\n{self.tr('restart_recommended')}")

        elif status == "failure":
            self.update_status_label.setText(self.tr('error_status'))
            self.update_progress_bar.setValue(0)
            QtWidgets.QMessageBox.critical(self, self.tr("update_failed_title"), f"{self.tr('update_failed_msg')}\n\n{message}")
        
        elif status == "cancelled":
            self.update_status_label.setText(self.tr('update_cancelled_by_user'))
            self.update_progress_bar.setValue(0)

    def create_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.create_menu_bar()
        self.create_toolbar()

        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status()

        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_widget)

        self.global_search = SearchBar(placeholder_text=self.tr("search_placeholder"))
        self.global_search.searchChanged.connect(self.on_global_search)
        content_layout.addWidget(self.global_search)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tab_widgets = {}

        languages = list(self.entries_by_lang.keys())

        if "French(France)" not in languages and any("French" in lang for lang in languages):
            french_variants = [lang for lang in languages if "French" in lang]
            if french_variants:
                languages = languages
                
        if "SFX" not in languages:
            self.entries_by_lang["SFX"] = []
            languages.append("SFX")
            
        for lang in sorted(languages):
            self.create_language_tab(lang)

        self.create_converter_tab()
        self.load_converter_file_list()
        self.create_subtitle_editor_tab()
        self.create_resource_updater_tab()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        content_layout.addWidget(self.tabs)
        main_layout.addWidget(content_widget)

        # if self.entries_by_lang:
        #     first_lang = sorted(self.entries_by_lang.keys())[0]
        #     self.populate_tree(first_lang)
        #     self.populated_tabs.add(first_lang)
            
        def delayed_init():
            if hasattr(self, 'subtitle_lang_combo'):
                self.populate_subtitle_editor_controls()
            
            for lang in self.tab_widgets.keys():
                self.update_filter_combo(lang)

        QtCore.QTimer.singleShot(500, delayed_init)

    def refresh_subtitle_editor(self):
        """Refresh subtitle editor data"""
        DEBUG.log("Refreshing subtitle editor")
        self.scan_localization_folder()
        self.populate_subtitle_editor_controls()
        self.status_bar.showMessage("Localization editor refreshed", 2000)

    def on_global_search_changed_for_subtitles(self, text):
        if hasattr(self, 'subtitle_editor_tab_widget') and self.tabs.currentWidget() == self.subtitle_editor_tab_widget:
            self.on_subtitle_filter_changed()

    def get_global_search_text(self):
        """Get text from global search bar"""
        return self.global_search.text() if hasattr(self, 'global_search') else ""

    def create_subtitle_editor_tab(self):
        """Create tab for editing subtitles without audio files"""
        tab = QtWidgets.QWidget()
        self.subtitle_editor_tab_widget = tab
        layout = QtWidgets.QVBoxLayout(tab)
        
        header = QtWidgets.QLabel(f"""
        <h3>{self.tr("localization_editor")}</h3>
        <p>{self.tr("localization_editor_desc")}</p>
        """)
        layout.addWidget(header)
        
        status_widget = QtWidgets.QWidget()
        status_layout = QtWidgets.QHBoxLayout(status_widget)
        
        self.subtitle_status_label = QtWidgets.QLabel("Ready")
        self.subtitle_status_label.setStyleSheet("color: #666; font-style: italic;")
        
        self.subtitle_progress = QtWidgets.QProgressBar()
        self.subtitle_progress.setVisible(False)
        self.subtitle_progress.setMaximumHeight(20)
        
        self.subtitle_cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
        self.subtitle_cancel_btn.setVisible(False)
        self.subtitle_cancel_btn.setMaximumWidth(80)
        self.subtitle_cancel_btn.clicked.connect(self.cancel_subtitle_loading)
        
        status_layout.addWidget(self.subtitle_status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.subtitle_progress)
        status_layout.addWidget(self.subtitle_cancel_btn)
        
        layout.addWidget(status_widget)
        
        controls = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls)
        
        category_label = QtWidgets.QLabel("Category:")
        self.subtitle_category_combo = QtWidgets.QComboBox()
        self.subtitle_category_combo.setMinimumWidth(150)
        
        self.orphaned_only_checkbox = QtWidgets.QCheckBox(self.tr("without_audio_filter"))
        self.orphaned_only_checkbox.setToolTip(self.tr("without_audio_filter_tooltip"))
        
        self.modified_only_checkbox = QtWidgets.QCheckBox(self.tr("modified_only_filter"))
        self.modified_only_checkbox.setToolTip(self.tr("modified_only_filter_tooltip"))
        
        self.with_audio_only_checkbox = QtWidgets.QCheckBox(self.tr("with_audio_only_filter"))
        self.with_audio_only_checkbox.setToolTip(self.tr("with_audio_only_filter_tooltip"))
        
        refresh_btn = QtWidgets.QPushButton(self.tr("refresh_btn"))
        refresh_btn.setToolTip(self.tr("refresh_btn_tooltip"))
        refresh_btn.clicked.connect(self.refresh_subtitle_editor)
        
        controls_layout.addWidget(category_label)
        controls_layout.addWidget(self.subtitle_category_combo)
        controls_layout.addWidget(self.orphaned_only_checkbox)
        controls_layout.addWidget(self.modified_only_checkbox)
        controls_layout.addWidget(self.with_audio_only_checkbox)
        controls_layout.addStretch()
        controls_layout.addWidget(refresh_btn)
        
        layout.addWidget(controls)
        
        self.subtitle_category_combo.currentTextChanged.connect(self.on_subtitle_filter_changed)
        self.orphaned_only_checkbox.toggled.connect(self.on_subtitle_filter_changed)
        self.modified_only_checkbox.toggled.connect(self.on_subtitle_filter_changed)
        self.with_audio_only_checkbox.toggled.connect(self.on_subtitle_filter_changed)
        
        self.subtitle_table = QtWidgets.QTableWidget()
        self.subtitle_table.setColumnCount(4)
        self.subtitle_table.setHorizontalHeaderLabels([self.tr("key_header"), self.tr("original_header"), self.tr("current_header"), self.tr("audio_header")])
        
        header = self.subtitle_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        
        self.subtitle_table.setAlternatingRowColors(True)
        self.subtitle_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.subtitle_table.itemDoubleClicked.connect(self.edit_subtitle_from_table)
        
        self.subtitle_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.subtitle_table.customContextMenuRequested.connect(self.show_subtitle_table_context_menu)
        
        layout.addWidget(self.subtitle_table)
        
        btn_widget = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout(btn_widget)
        
        edit_btn = QtWidgets.QPushButton(self.tr("edit_selected_btn"))
        edit_btn.clicked.connect(self.edit_selected_subtitle)
        
        btn_layout.addWidget(edit_btn)
        btn_layout.addStretch()
        
        save_all_btn = QtWidgets.QPushButton(self.tr("save_all_changes_btn"))
        save_all_btn.clicked.connect(self.save_all_subtitle_changes)
        btn_layout.addWidget(save_all_btn)
        
        layout.addWidget(btn_widget)
        
        self.subtitle_editor_loaded = False
        self.audio_keys_cache = None
        self.subtitle_loader_thread = None
        
        self.tabs.addTab(tab, self.tr("localization_editor"))
        self.global_search.searchChanged.connect(self.on_global_search_changed_for_subtitles)

    def cancel_subtitle_loading(self):
        """Cancel current subtitle loading operation"""
        if self.subtitle_loader_thread and self.subtitle_loader_thread.isRunning():
            self.subtitle_loader_thread.stop()
            self.subtitle_loader_thread.wait(2000)
        
        self.hide_subtitle_loading_ui()
        self.subtitle_status_label.setText("Loading cancelled")

    def show_subtitle_loading_ui(self):
        """Show loading UI elements"""
        self.subtitle_progress.setVisible(True)
        self.subtitle_cancel_btn.setVisible(True)
        
        self.subtitle_category_combo.setEnabled(False)
        self.orphaned_only_checkbox.setEnabled(False)

    def hide_subtitle_loading_ui(self):
        """Hide loading UI elements"""
        self.subtitle_progress.setVisible(False)
        self.subtitle_cancel_btn.setVisible(False)
        
        self.subtitle_category_combo.setEnabled(True)
        self.orphaned_only_checkbox.setEnabled(True)

    def populate_subtitle_editor_controls(self):
        """Populate category controls"""
        DEBUG.log("Populating subtitle editor controls")
        
        self.subtitle_category_combo.currentTextChanged.disconnect()
        
        try:
            categories = set()
            
            for file_info in self.all_subtitle_files.values():
                categories.add(file_info['category'])
            
            DEBUG.log(f"Found categories: {categories}")
            
            current_category = self.subtitle_category_combo.currentText()
            
            self.subtitle_category_combo.clear()
            self.subtitle_category_combo.addItem("All Categories")
            if categories:
                sorted_categories = sorted(categories)
                self.subtitle_category_combo.addItems(sorted_categories)
                
                if current_category and current_category != "All Categories":
                    if current_category in categories:
                        self.subtitle_category_combo.setCurrentText(current_category)
            
            DEBUG.log(f"Category combo: {self.subtitle_category_combo.count()} items")
            
        finally:
            self.subtitle_category_combo.currentTextChanged.connect(self.on_subtitle_filter_changed)
        
        self.load_subtitle_editor_data()

    def on_subtitle_filter_changed(self):
        """Handle filter changes with debouncing"""
        if hasattr(self, 'filter_timer'):
            self.filter_timer.stop()
        
        self.filter_timer = QtCore.QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.load_subtitle_editor_data)
        self.filter_timer.start(500)

    def build_audio_keys_cache(self):
        """Build cache of audio keys for orphaned subtitle detection"""
        if self.audio_keys_cache is not None:
            return self.audio_keys_cache
        
        DEBUG.log("Building audio keys cache...")
        self.audio_keys_cache = set()
        
        for entry in self.all_files:
            shortname = entry.get("ShortName", "")
            if shortname:
                audio_key = os.path.splitext(shortname)[0]
                self.audio_keys_cache.add(audio_key)
        
        DEBUG.log(f"Built cache with {len(self.audio_keys_cache)} audio keys")
    
        sample_keys = list(self.audio_keys_cache)[:5]
        DEBUG.log(f"Sample audio keys: {sample_keys}")
        
        return self.audio_keys_cache

    def load_subtitle_editor_data(self):
        """Load subtitle data for editor asynchronously"""
        selected_category = self.subtitle_category_combo.currentText()
        orphaned_only = self.orphaned_only_checkbox.isChecked()
        modified_only = self.modified_only_checkbox.isChecked()
        with_audio_only = self.with_audio_only_checkbox.isChecked()
        search_text = self.get_global_search_text()
        
        DEBUG.log(f"Loading subtitle editor data: category={selected_category}, language={self.settings.data['subtitle_lang']}, orphaned={orphaned_only}, modified={modified_only}, with_audio={with_audio_only}")
        
 
        if orphaned_only and with_audio_only:
            self.with_audio_only_checkbox.setChecked(False)
            with_audio_only = False
            DEBUG.log("Disabled 'with_audio_only' because 'orphaned_only' is active")
        
        if self.subtitle_loader_thread and self.subtitle_loader_thread.isRunning():
            self.subtitle_loader_thread.stop()
            self.subtitle_loader_thread.wait(1000)

        if (orphaned_only or with_audio_only):
            if self.audio_keys_cache is None:
                self.build_audio_keys_cache()
            DEBUG.log(f"Audio cache has {len(self.audio_keys_cache) if self.audio_keys_cache else 0} keys")
        
        self.show_subtitle_loading_ui()
        self.subtitle_status_label.setText("Loading subtitles...")
        self.subtitle_progress.setValue(0)
        
        self.subtitle_table.setRowCount(0)

        self.subtitle_loader_thread = SubtitleLoaderThread(
            self, self.all_subtitle_files, self.locres_manager, 
            self.subtitles, self.original_subtitles,
            self.settings.data["subtitle_lang"], selected_category, orphaned_only, modified_only, with_audio_only,
            search_text, self.audio_keys_cache, self.modified_subtitles
        )
        
        self.subtitle_loader_thread.dataLoaded.connect(self.on_subtitle_data_loaded)
        self.subtitle_loader_thread.statusUpdate.connect(self.subtitle_status_label.setText)
        self.subtitle_loader_thread.progressUpdate.connect(self.subtitle_progress.setValue)
        
        self.subtitle_loader_thread.start()

    def on_subtitle_data_loaded(self, subtitles_to_show):
        """Handle loaded subtitle data"""
        self.hide_subtitle_loading_ui()
        
        self.populate_subtitle_table(subtitles_to_show)
        
        status_parts = [f"{len(subtitles_to_show)} subtitles"]
        
        filters_active = []
        if self.orphaned_only_checkbox.isChecked():
            filters_active.append("without audio")
        
        if self.modified_only_checkbox.isChecked():
            filters_active.append("modified only")
            
        if self.with_audio_only_checkbox.isChecked():
            filters_active.append("with audio only")
        
        search_text = self.get_global_search_text().strip()
        if search_text:
            filters_active.append(f"search: '{search_text}'")
        
        selected_category = self.subtitle_category_combo.currentText()
        if selected_category and selected_category != "All Categories":
            filters_active.append(f"category: {selected_category}")
        
        if filters_active:
            status_parts.append(f"({', '.join(filters_active)})")
        
        self.subtitle_status_label.setText(" ".join(status_parts))

    def populate_subtitle_table(self, subtitles_to_show):
        """Populate the subtitle table with data"""
        self.subtitle_table.setRowCount(len(subtitles_to_show))
        
        if len(subtitles_to_show) == 0:
            return
        
        sorted_items = sorted(subtitles_to_show.items())
        
        for row, (key, data) in enumerate(sorted_items):
            key_item = QtWidgets.QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.subtitle_table.setItem(row, 0, key_item)
            
            original_text = data['original']
            original_display = self.truncate_text(original_text, 150)
            original_item = QtWidgets.QTableWidgetItem(original_display)
            original_item.setFlags(original_item.flags() & ~QtCore.Qt.ItemIsEditable)
            original_item.setToolTip(original_text)
            self.subtitle_table.setItem(row, 1, original_item)
            
            current_text = data['current']
            current_display = self.truncate_text(current_text, 150)
            current_item = QtWidgets.QTableWidgetItem(current_display)
            current_item.setToolTip(current_text)
            self.subtitle_table.setItem(row, 2, current_item)
            
            has_audio = data.get('has_audio', False)
            audio_item = QtWidgets.QTableWidgetItem("🔊" if has_audio else "")
            audio_item.setFlags(audio_item.flags() & ~QtCore.Qt.ItemIsEditable)
            audio_item.setToolTip(self.tr("has_audio_file") if has_audio else self.tr("no_audio_file"))
            audio_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.subtitle_table.setItem(row, 3, audio_item)
            
            is_modified = data.get('is_modified', False)
            if is_modified:
                highlight_color = QtGui.QColor(85, 72, 35) if self.settings.data.get("theme", "light") == "dark" else QtGui.QColor(255, 255, 200)
                for col in range(4):
                    item = self.subtitle_table.item(row, col)
                    if item:
                        item.setBackground(highlight_color)
            
            search_text = self.get_global_search_text().lower().strip()
            if search_text:
                if (search_text in key.lower() or 
                    search_text in original_text.lower() or 
                    search_text in current_text.lower()):
                    for col in range(4):
                        item = self.subtitle_table.item(row, col)
                        if item:
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)

    def truncate_text(self, text, max_length):
        """Truncate text for display"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def edit_subtitle_from_table(self, item):
        """Edit subtitle from table double-click"""
        if not item:
            return
            
        try:
            row = item.row()
            key = self.subtitle_table.item(row, 0).text()
            current_text = self.subtitle_table.item(row, 2).toolTip() or self.subtitle_table.item(row, 2).text()
            original_text = self.subtitle_table.item(row, 1).toolTip() or self.subtitle_table.item(row, 1).text()
            
            stored_key = key
            stored_row = row
            
            editor = SubtitleEditor(self, key, current_text, original_text)
            if editor.exec_() == QtWidgets.QDialog.Accepted:
                new_text = editor.get_text()
                self.subtitles[key] = new_text
                if key in self.key_to_file_map:
                    file_info = self.key_to_file_map[key]
                    self.dirty_subtitle_files.add(file_info['path'])
                    DEBUG.log(f"Marked file as dirty due to edit: {file_info['path']}")
                if new_text != original_text:
                    self.modified_subtitles.add(key)
                else:
                    self.modified_subtitles.discard(key)
                
                target_row = self.find_table_row_by_key(stored_key)
                if target_row >= 0:
                    try:
                        current_item = self.subtitle_table.item(target_row, 2)
                        if current_item:
                            display_text = self.truncate_text(new_text, 150)
                            current_item.setText(display_text)
                            current_item.setToolTip(new_text)
                            
                            if new_text != original_text:
                 
                                highlight_color = QtGui.QColor(85, 72, 35) if self.settings.data.get("theme", "light") == "dark" else QtGui.QColor(255, 255, 200)
                                for col in range(4):
                                    cell_item = self.subtitle_table.item(target_row, col)
                                    if cell_item:
                                        cell_item.setBackground(highlight_color)
                    
                            else:
      
                                base_color = self.palette().color(QtGui.QPalette.Base)
                                for col in range(4):
                                    cell_item = self.subtitle_table.item(target_row, col)
                                    if cell_item:
                                        cell_item.setBackground(base_color)
                                        
                    except RuntimeError as e:
                        DEBUG.log(f"Table item was deleted during update: {e}", "WARNING")
                        self.load_subtitle_editor_data()
                else:
                    DEBUG.log("Table row not found after edit, refreshing")
                    self.load_subtitle_editor_data()
                
                self.update_status()
                
        except RuntimeError as e:
            DEBUG.log(f"Error in edit_subtitle_from_table: {e}", "ERROR")
            self.load_subtitle_editor_data()

    def find_table_row_by_key(self, target_key):
        """Find table row by subtitle key"""
        for row in range(self.subtitle_table.rowCount()):
            try:
                key_item = self.subtitle_table.item(row, 0)
                if key_item and key_item.text() == target_key:
                    return row
            except RuntimeError:
                continue
        return -1

    def edit_selected_subtitle(self):
        """Edit currently selected subtitle"""
        current_row = self.subtitle_table.currentRow()
        if current_row >= 0:
            item = self.subtitle_table.item(current_row, 0)
            if item:
                self.edit_subtitle_from_table(item)

    def save_all_subtitle_changes(self):
        """Save all subtitle changes to working files in a separate thread."""
        if not self.ensure_active_profile():
            return
            
        if not self.modified_subtitles:
            QtWidgets.QMessageBox.information(self, self.tr("no_changes"), self.tr("no_modified_subtitles"))
            return

        self.progress_dialog = ProgressDialog(self, self.tr("Saving Subtitles..."))
        self.progress_dialog.show()

        self.save_thread = SaveSubtitlesThread(self)
        self.save_thread.progress_updated.connect(self.progress_dialog.set_progress)
        self.save_thread.finished.connect(self.on_save_finished)
        self.save_thread.start()

    def on_save_finished(self, count, errors):
        """Handles the completion of the subtitle saving thread."""
        self.progress_dialog.close()
        
        self.update_status()
        for lang in self.populated_tabs:
            self.populate_tree(lang)
        
        if not errors:
            self.dirty_subtitle_files.clear()
            QtWidgets.QMessageBox.information(self, self.tr("success"), 
                f"{self.tr('subtitle_save_success')}\n\nUpdated {count} file(s) in your mod profile.")
            self.status_bar.showMessage(self.tr("subtitle_save_success"), 3000)
        else:
            error_details = "\n".join(errors)
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setWindowTitle(self.tr("save_error"))
            msg_box.setText(f"Completed with {len(errors)} error(s).")
            msg_box.setDetailedText(error_details)
            msg_box.exec_()
            self.status_bar.showMessage(f"Save completed with {len(errors)} error(s)", 5000)

    def show_subtitle_table_context_menu(self, pos):
        selected_items = self.subtitle_table.selectedItems()
        if not selected_items:
            return
        
        selected_rows = sorted(list(set(item.row() for item in selected_items)))
        
        first_row = selected_rows[0]
        key = self.subtitle_table.item(first_row, 0).text()
        has_audio = self.subtitle_table.item(first_row, 3).text() == "🔊"

        menu = QtWidgets.QMenu()
        if self.settings.data["theme"] == "dark":
            menu.setStyleSheet(self.get_dark_menu_style())
        
        if len(selected_rows) > 1:
            edit_action = menu.addAction(f"✏️ {self.tr('edit_subtitle')} ({len(selected_rows)} items)")
            edit_action.setEnabled(False) 
            
            revert_action = menu.addAction(f"↩️ {self.tr('revert_to_original')} ({len(selected_rows)} items)")
        else:
            edit_action = menu.addAction(f"✏️ {self.tr('edit_subtitle')}")
            revert_action = menu.addAction(f"↩️ {self.tr('revert_to_original')}")

        edit_action.triggered.connect(lambda: self.edit_subtitle_from_table(self.subtitle_table.item(first_row, 0)))
        revert_action.triggered.connect(lambda: self.revert_subtitle_from_table(selected_rows))
        
        menu.addSeparator()
        
        if len(selected_rows) == 1 and has_audio:
            goto_audio_action = menu.addAction(f"🔊 {self.tr('go_to_audio_action')}")
            goto_audio_action.triggered.connect(lambda: self.go_to_audio_file(key))
            menu.addSeparator()
        
        copy_key_action = menu.addAction(f"{self.tr('copy_key')}")
        copy_key_action.triggered.connect(lambda: QtWidgets.QApplication.clipboard().setText(key))
        
        copy_text_action = menu.addAction(f"{self.tr('copy_text')}")
        current_text = self.subtitle_table.item(first_row, 2).toolTip() or self.subtitle_table.item(first_row, 2).text()
        copy_text_action.triggered.connect(lambda: QtWidgets.QApplication.clipboard().setText(current_text))
        
        menu.exec_(self.subtitle_table.mapToGlobal(pos))

    def go_to_audio_file(self, subtitle_key):
        """Navigate to audio file corresponding to subtitle"""
        DEBUG.log(f"Looking for audio file for subtitle key: {subtitle_key}")
        
        target_entry = None
        target_lang = None
        
        for entry in self.all_files:
            shortname = entry.get("ShortName", "")
            if shortname:
                audio_key = os.path.splitext(shortname)[0]
                if audio_key == subtitle_key:
                    target_entry = entry
                    target_lang = entry.get("Language", "SFX")
                    break
        
        if not target_entry:
            QtWidgets.QMessageBox.information(
                self, self.tr("info"), 
                self.tr("tab_not_found_for_lang").format(lang=target_lang)
            )
            return
        
        DEBUG.log(f"Found audio file: {target_entry.get('ShortName')} in language: {target_lang}")
        
        for i in range(self.tabs.count()):
            tab_text = self.tabs.tabText(i)
            if target_lang in tab_text:
                self.tabs.setCurrentIndex(i)
                
                if target_lang not in self.populated_tabs:
                    self.populate_tree(target_lang)
                    self.populated_tabs.add(target_lang)
                
                self.find_and_select_audio_item(target_lang, target_entry)
                
                self.status_bar.showMessage(f"Navigated to audio file: {target_entry.get('ShortName')}", 3000)
                return
        
        QtWidgets.QMessageBox.information(
            self, self.tr("audio_not_found"), 
            self.tr("audio_not_found_for_key").format(key=subtitle_key)
        )

    def find_and_select_audio_item(self, lang, target_entry):
        """Find and select audio item in tree"""
        if lang not in self.tab_widgets:
            return
        
        tree = self.tab_widgets[lang]["tree"]
        target_id = target_entry.get("Id", "")
        target_shortname = target_entry.get("ShortName", "")
        
        def search_items(parent_item):
            for i in range(parent_item.childCount()):
                item = parent_item.child(i)
                
                if item.childCount() == 0:
                    try:
                        entry = item.data(0, QtCore.Qt.UserRole)
                        if entry:
                            if (entry.get("Id") == target_id or 
                                entry.get("ShortName") == target_shortname):
                                tree.clearSelection()
                                tree.setCurrentItem(item)
                                item.setSelected(True)
                                
                                parent = item.parent()
                                if parent:
                                    parent.setExpanded(True)
                                
                                tree.scrollToItem(item)
                                self.on_selection_changed(lang)
                                
                                return True
                    except RuntimeError:
                        continue
                else:
                    if search_items(item):
                        return True
            return False
        
        try:
            root = tree.invisibleRootItem()
            if not search_items(root):
                DEBUG.log(f"Could not find item in tree for: {target_shortname}")
        except RuntimeError:
            pass

    def revert_subtitle_from_table(self, rows_to_revert):
        """Revert subtitle(s) to original from table for a list of row indices."""
        if not rows_to_revert:
            return

        reverted_count = 0
        for row in rows_to_revert:
            try:
                key_item = self.subtitle_table.item(row, 0)
                if not key_item:
                    continue
                
                key = key_item.text()
                
                if key in self.original_subtitles:
                    original_text = self.original_subtitles[key]
                    
                    self.subtitles[key] = original_text
                    self.modified_subtitles.discard(key)
                    if key in self.key_to_file_map:
                        file_info = self.key_to_file_map[key]
                        self.dirty_subtitle_files.add(file_info['path'])
                        DEBUG.log(f"Marked file as dirty due to revert: {file_info['path']}")

                    current_item = self.subtitle_table.item(row, 2)
                    current_item.setText(self.truncate_text(original_text, 150))
                    current_item.setToolTip(original_text)
                    
                    base_color = self.palette().color(QtGui.QPalette.Base)
                    for col in range(4):
                        item = self.subtitle_table.item(row, col)
                        if item:
                            item.setBackground(base_color)

                    reverted_count += 1
            except Exception as e:
                DEBUG.log(f"Error reverting subtitle at row {row}: {e}", "ERROR")

        if reverted_count > 0:
            self.update_status()
            self.status_bar.showMessage(f"Reverted {reverted_count} subtitle(s) to original", 3000)

    def process_wem_files(self):
        wwise_root = self.wwise_path_edit_old.text()
        if not wwise_root or not os.path.exists(wwise_root):
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid WWISE folder path!")
            return
            
        progress = ProgressDialog(self, "Processing WEM Files")
        progress.show()
        
        # Find SFX paths
        sfx_paths = []
        for root, dirs, files in os.walk(wwise_root):
            if root.endswith(".cache\\Windows\\SFX"):
                sfx_paths.append(root)
                
        if not sfx_paths:
            progress.close()
            QtWidgets.QMessageBox.warning(self, "Error", "No .cache/Windows/SFX/ folders found!")
            return
        

        selected_language = self.settings.data.get("wem_process_language", "english")
        DEBUG.log(f"Selected WEM process language: {selected_language}")
        

        if selected_language == "english":
            target_dir_voice = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", "English(US)")
            voice_lang_filter = ["English(US)"]
        elif selected_language == "french":
            target_dir_voice = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", "Francais")
            voice_lang_filter = ["French(France)", "Francais"]
        else:
            target_dir_voice = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)")
            voice_lang_filter = ["English(US)"]
        
        target_dir_sfx = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media")
        
        os.makedirs(target_dir_voice, exist_ok=True)
        os.makedirs(target_dir_sfx, exist_ok=True)
        
        all_wem_files = []
        vo_wem_files = []
        
        for sfx_path in sfx_paths:
            for filename in os.listdir(sfx_path):
                if filename.endswith(".wem"):
                    base_name = os.path.splitext(filename)[0]
                    all_wem_files.append(base_name)
                    if base_name.startswith("VO_"):
                        vo_wem_files.append(base_name)
        
        DEBUG.log(f"Found {len(all_wem_files)} total WEM files on disk")
        DEBUG.log(f"Found {len(vo_wem_files)} VO WEM files on disk")
        DEBUG.log(f"First 10 VO WEM files on disk: {vo_wem_files[:10]}")
        
        voice_mapping = {}  
        sfx_mapping = {}    
        voice_files_in_db = []

        vo_from_streamed = 0
        vo_from_media_files = 0
        vo_skipped_wrong_lang = 0
        
        for entry in self.all_files:
            shortname = entry.get("ShortName", "")
            base_shortname = os.path.splitext(shortname)[0]
            file_id = entry.get("Id", "")
            language = entry.get("Language", "")
            source = entry.get("Source", "")
            
            file_info = {
                'id': file_id,
                'language': language,
                'source': source,
                'original_name': shortname
            }

            if base_shortname.startswith("VO_"):

                if language in voice_lang_filter:
                    voice_mapping[base_shortname] = file_info
                    voice_files_in_db.append(base_shortname)
                    
                    if source == "StreamedFiles":
                        vo_from_streamed += 1
                        DEBUG.log(f"Added StreamedFiles VO: {base_shortname} -> ID {file_id} ({language})")
                    elif source == "MediaFilesNotInAnyBank":
                        vo_from_media_files += 1
                        if vo_from_media_files <= 10:  
                            DEBUG.log(f"Added MediaFilesNotInAnyBank VO: {base_shortname} -> ID {file_id} ({language})")
                else:
          
                    vo_skipped_wrong_lang += 1
                    if vo_skipped_wrong_lang <= 5: 
                        DEBUG.log(f"Skipped VO (wrong language): {base_shortname} -> ID {file_id} ({language})")
            
            elif language == "SFX" or (source == "MediaFilesNotInAnyBank" and not base_shortname.startswith("VO_")):
                sfx_mapping[base_shortname] = file_info
        
        DEBUG.log(f"Voice files from StreamedFiles: {vo_from_streamed}")
        DEBUG.log(f"Voice files from MediaFilesNotInAnyBank: {vo_from_media_files}")
        DEBUG.log(f"Voice files skipped (wrong language): {vo_skipped_wrong_lang}")
        DEBUG.log(f"Total voice files for {selected_language}: {len(voice_files_in_db)}")
        DEBUG.log(f"First 10 voice files in database: {voice_files_in_db[:10]}")

        exact_matches = []
        potential_matches = []
        
        for wem_file in vo_wem_files:
            if wem_file in voice_mapping:
                exact_matches.append(wem_file)
            else:
   
                wem_without_hex = wem_file

                if '_' in wem_file:
                    parts = wem_file.split('_')
   
                    if len(parts) > 1 and len(parts[-1]) == 8:
                        try:
                            int(parts[-1], 16) 
                            wem_without_hex = '_'.join(parts[:-1])
                            DEBUG.log(f"Removing hex suffix: {wem_file} -> {wem_without_hex}")
                        except ValueError:
                            pass
                
                if wem_without_hex in voice_mapping and wem_without_hex != wem_file:
                    potential_matches.append((wem_file, wem_without_hex))
        
        DEBUG.log(f"Exact matches found: {len(exact_matches)}")
        DEBUG.log(f"Potential matches (after removing hex): {len(potential_matches)}")
        DEBUG.log(f"First 5 exact matches: {exact_matches[:5]}")
        DEBUG.log(f"First 5 potential matches: {potential_matches[:5]}")

        for wem_file, db_file in potential_matches:
            if db_file in voice_mapping:
                voice_mapping[wem_file] = voice_mapping[db_file].copy()
                voice_mapping[wem_file]['matched_via'] = f"hex_removal_from_{db_file}"
                DEBUG.log(f"Added potential match: {wem_file} -> {voice_mapping[wem_file]['id']} (via {db_file}) [{voice_mapping[wem_file]['language']}]")
        
        DEBUG.log(f"Voice mapping after adding potential matches: {len(voice_mapping)} files")

        name_to_ids = {}
        for name, info in voice_mapping.items():
            base_name = name.split('_')
            if len(base_name) > 3:
                check_name = '_'.join(base_name[:4]) 
                if check_name not in name_to_ids:
                    name_to_ids[check_name] = []
                name_to_ids[check_name].append((info['id'], info['language']))
        
        for name, ids in name_to_ids.items():
            if len(ids) > 1:
                DEBUG.log(f"WARNING: Multiple IDs for similar name '{name}': {ids}")
        
        self.converter_status_old.clear()
        self.converter_status_old.append(f"=== Processing WEM Files for {selected_language.capitalize()} ===")
        self.converter_status_old.append(f"Voice target: {target_dir_voice}")
        self.converter_status_old.append(f"SFX target: {target_dir_sfx}")
        self.converter_status_old.append("")
        self.converter_status_old.append(f"Analysis Results:")
        self.converter_status_old.append(f"  WEM files on disk: {len(all_wem_files)} total, {len(vo_wem_files)} VO files")
        self.converter_status_old.append(f"  Voice files in database for {selected_language}: {len(voice_files_in_db)}")
        self.converter_status_old.append(f"    - From StreamedFiles: {vo_from_streamed}")
        self.converter_status_old.append(f"    - From MediaFilesNotInAnyBank: {vo_from_media_files}")
        self.converter_status_old.append(f"    - Skipped (wrong language): {vo_skipped_wrong_lang}")
        self.converter_status_old.append(f"  Exact matches: {len(exact_matches)}")
        self.converter_status_old.append(f"  Potential matches (hex removal): {len(potential_matches)}")
        self.converter_status_old.append(f"  Total mappable files: {len(exact_matches) + len(potential_matches)}")
        self.converter_status_old.append("")
        
        processed = 0
        voice_processed = 0
        sfx_processed = 0
        skipped = 0
        renamed_count = 0
        total_files = len(all_wem_files)
        
        for sfx_path in sfx_paths:
            DEBUG.log(f"Processing folder: {sfx_path}")
            
            for filename in os.listdir(sfx_path):
                if filename.endswith(".wem"):
                    src_path = os.path.join(sfx_path, filename)
                    base_name = os.path.splitext(filename)[0]
                    
                    file_info = None
                    dest_filename = filename
                    target_dir = target_dir_sfx
                    is_voice = base_name.startswith("VO_")
                    classification = "Unknown"
                    
                    if is_voice:
                        target_dir = target_dir_voice
                        classification = f"Voice ({selected_language})"

                        if base_name in voice_mapping:
                            file_info = voice_mapping[base_name]
                            dest_filename = f"{file_info['id']}.wem"
                            match_method = file_info.get('matched_via', 'exact_match')
                            file_language = file_info.get('language', 'Unknown')
                            classification += f" (ID {file_info['id']}, {match_method}, {file_language})"
                            renamed_count += 1
                            DEBUG.log(f"FOUND MATCH: {filename} -> {dest_filename} ({match_method}) [Language: {file_language}]")
                        else:
                            classification += " (no ID found - keeping original name)"
                            DEBUG.log(f"NO MATCH FOUND for {filename}")
                            
                    else:

                        classification = "SFX"
                        search_keys = [
                            base_name,
                            base_name.rsplit("_", 1)[0] if "_" in base_name else base_name,
                        ]
                        
                        for search_key in search_keys:
                            if search_key in sfx_mapping:
                                file_info = sfx_mapping[search_key]
                                dest_filename = f"{file_info['id']}.wem"
                                classification += f" (matched '{search_key}' -> ID {file_info['id']})"
                                renamed_count += 1
                                break
                        
                        if not file_info:
                            classification += " (no ID found - keeping original name)"
                    
                    dest_path = os.path.join(target_dir, dest_filename)
                    
                    try:

                        if os.path.exists(dest_path):
                            base_dest_name = os.path.splitext(dest_filename)[0]
                            counter = 1
                            while os.path.exists(os.path.join(target_dir, f"{base_dest_name}_{counter}.wem")):
                                counter += 1
                            dest_filename = f"{base_dest_name}_{counter}.wem"
                            dest_path = os.path.join(target_dir, dest_filename)
                            classification += " (duplicate renamed)"
                        
                        shutil.move(src_path, dest_path)
                        processed += 1
                        
                        if is_voice:
                            voice_processed += 1
                            icon = "🎙"
                        else:
                            sfx_processed += 1
                            icon = "🔊"
                        
                        progress.set_progress(int((processed / total_files) * 100), f"Processing {filename}...")
                        
                        self.converter_status.append(f"{icon} {classification}: {filename} → {dest_filename}")
                        QtWidgets.QApplication.processEvents()
                        
                    except Exception as e:
                        self.converter_status.append(f"✗ ERROR: {filename} - {str(e)} [{classification}]")
                        skipped += 1
                        DEBUG.log(f"Error processing {filename}: {e}", "ERROR")
                        
        progress.close()
        
        success_rate = (renamed_count / voice_processed * 100) if voice_processed > 0 else 0
        
        self.converter_status_old.append("")
        self.converter_status_old.append("=== Processing Complete ===")
        self.converter_status_old.append(f"Total files processed: {processed}")
        self.converter_status_old.append(f"Voice files ({selected_language}): {voice_processed}")
        self.converter_status_old.append(f"SFX files: {sfx_processed}")
        self.converter_status_old.append(f"Files renamed to ID: {renamed_count}")
        self.converter_status_old.append(f"Files kept original name: {processed - renamed_count}")
        self.converter_status_old.append(f"Voice rename success rate: {success_rate:.1f}%")
        if skipped > 0:
            self.converter_status.append(f"Skipped/Errors: {skipped}")
        
        QtWidgets.QMessageBox.information(
            self, "Processing Complete",
            f"Processed {processed} files for {selected_language.capitalize()} language.\n"
            f"Voice files: {voice_processed}\n"
            f"Renamed to ID: {renamed_count}\n"
            f"Success rate: {success_rate:.1f}%\n"
            f"Kept original names: {processed - renamed_count}"
        )

    def cleanup_working_locres(self):
        DEBUG.log("=== Cleanup Working Locres Files ===")
        localization_path = os.path.join(self.base_path, "Localization")
        if not os.path.exists(localization_path):
            QtWidgets.QMessageBox.information(
                self, self.tr("no_localization_found"), 
                self.tr("no_localization_message").format(path=localization_path)
            )
            return

        working_files = []
        for root, dirs, files in os.walk(localization_path):
            for file in files:
                if file.endswith('_working.locres'):
                    file_path = os.path.join(root, file)
                    working_files.append(file_path)

        if not working_files:
            QtWidgets.QMessageBox.information(
                self, self.tr("no_localization_found"), 
                "No working subtitle files (_working.locres) found in Localization."
            )
            return

        deleted = 0
        errors = 0
        for file_path in working_files:
            try:
                os.remove(file_path)
                DEBUG.log(f"Deleted: {file_path}")
                deleted += 1

                parent = os.path.dirname(file_path)
                while parent != localization_path and os.path.isdir(parent) and not os.listdir(parent):
                    os.rmdir(parent)
                    parent = os.path.dirname(parent)
            except Exception as e:
                DEBUG.log(f"Error deleting {file_path}: {e}", "ERROR")
                errors += 1

        msg = f"Deleted {deleted} working subtitle files."
        if errors:
            msg += f"\nErrors: {errors}"
        QtWidgets.QMessageBox.information(self, "Cleanup Complete", msg)

    def save_subtitles_to_file(self):

        if not self.dirty_subtitle_files:
            return True

        DEBUG.log(f"=== Performing Blocking Save for {len(self.dirty_subtitle_files)} files ===")
        try:
            for original_path in list(self.dirty_subtitle_files):
                file_info = None
                for info in self.all_subtitle_files.values():
                    if info['path'] == original_path:
                        file_info = info
                        break
                
                if not file_info:
                    DEBUG.log(f"Could not find file info for dirty path: {original_path}", "WARNING")
                    continue
                
                target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "Localization", file_info['category'], file_info['language'])
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, file_info['filename'])

                subtitles_to_write = self.locres_manager.export_locres(original_path)
                
                for key in subtitles_to_write.keys():
                    if key in self.subtitles:
                        subtitles_to_write[key] = self.subtitles[key]

                shutil.copy2(original_path, target_path)

                if not self.locres_manager.import_locres(target_path, subtitles_to_write):
                    raise Exception(f"Failed to write to {target_path}")

            self.dirty_subtitle_files.clear()
            DEBUG.log("Blocking save successful, dirty files cleared.")
            return True
        except Exception as e:
            DEBUG.log(f"Blocking save error: {e}", "ERROR")
            return False

    def show_settings_dialog(self):
        dialog = QtWidgets.QDialog(self)    
        dialog.setWindowTitle(self.tr("settings"))
        dialog.setMinimumWidth(500)
        
        layout = QtWidgets.QFormLayout(dialog)
        
        lang_combo = QtWidgets.QComboBox()
        lang_map = [("English", "en"), ("Русский", "ru"), ("Polski", "pl"), ("Español (México)", "es-MX")]
        for name, code in lang_map:
            lang_combo.addItem(name, code)
        
        current_lang_code = self.settings.data["ui_language"]
        index = next((i for i, (name, code) in enumerate(lang_map) if code == current_lang_code), 0)
        lang_combo.setCurrentIndex(index)
        
        theme_combo = QtWidgets.QComboBox()
        theme_combo.addItem(self.tr("light"), "light")
        theme_combo.addItem(self.tr("dark"), "dark")
        theme_combo.setCurrentIndex(0 if self.settings.data["theme"] == "light" else 1)
        
        subtitle_combo = QtWidgets.QComboBox()
        subtitle_langs = [
            "de-DE", "en", "es-ES", "es-MX", "fr-FR", "it-IT", "ja-JP", "ko-KR",
            "pl-PL", "pt-BR", "ru-RU", "tr-TR", "zh-CN", "zh-TW"
        ]
        subtitle_combo.addItems(subtitle_langs)
        subtitle_combo.setCurrentText(self.settings.data["subtitle_lang"])
        
        game_path_widget = QtWidgets.QWidget()
        game_path_layout = QtWidgets.QHBoxLayout(game_path_widget)
        game_path_layout.setContentsMargins(0, 0, 0, 0)
        
        game_path_edit = QtWidgets.QLineEdit()
        game_path_edit.setText(self.settings.data.get("game_path", ""))
        game_path_edit.setPlaceholderText("Path to game root folder")
        
        game_path_btn = QtWidgets.QPushButton(self.tr("browse"))
        game_path_btn.clicked.connect(lambda: self.browse_game_path(game_path_edit))
        
        game_path_layout.addWidget(game_path_edit)
        game_path_layout.addWidget(game_path_btn)

        auto_save_check = QtWidgets.QCheckBox(self.tr("auto_save"))
        auto_save_check.setChecked(self.settings.data.get("auto_save", True))

        layout.addRow(self.tr("interface_language"), lang_combo)
        layout.addRow(self.tr("theme"), theme_combo)
        layout.addRow(self.tr("subtitle_language"), subtitle_combo)
        layout.addRow(self.tr("game_path"), game_path_widget)
        
        quick_load_group = QtWidgets.QGroupBox(self.tr("quick_load_settings_group"))
        quick_load_layout = QtWidgets.QVBoxLayout(quick_load_group)
        
        quick_load_label = QtWidgets.QLabel(self.tr("quick_load_mode_label"))
        quick_load_layout.addWidget(quick_load_label)
        
        quick_load_strict = QtWidgets.QRadioButton(self.tr("quick_load_strict"))
        quick_load_adaptive = QtWidgets.QRadioButton(self.tr("quick_load_adaptive"))
        
        current_quick_mode = self.settings.data.get("quick_load_mode", "strict")
        if current_quick_mode == "adaptive":
            quick_load_adaptive.setChecked(True)
        else:
            quick_load_strict.setChecked(True)
        
        quick_load_layout.addWidget(quick_load_strict)
        quick_load_layout.addWidget(quick_load_adaptive)
        
        layout.addRow(quick_load_group)
        layout.addRow(auto_save_check)
        wem_lang_combo = QtWidgets.QComboBox()
        wem_lang_combo.addItem("English (US)", "english")
        wem_lang_combo.addItem("Francais (France)", "french")
        current_wem_lang = self.settings.data.get("wem_process_language", "english")
        wem_lang_combo.setCurrentIndex(0 if current_wem_lang == "english" else 1)
        wem_lang_combo.setToolTip(self.tr("wemprocces_desc"))

        layout.addRow(self.tr("wem_process_language"), wem_lang_combo)
        conversion_method_group = QtWidgets.QGroupBox(self.tr("conversion_method_group"))
        conversion_method_layout = QtWidgets.QVBoxLayout(conversion_method_group)
        
        self.bnk_overwrite_radio = QtWidgets.QRadioButton(self.tr("bnk_overwrite_radio"))
        self.bnk_overwrite_radio.setToolTip(self.tr("bnk_overwrite_tooltip"))
        self.adaptive_radio = QtWidgets.QRadioButton(self.tr("adaptive_size_matching_radio"))
        self.adaptive_radio.setToolTip(self.tr("adaptive_size_matching_tooltip"))
        
        current_method = self.settings.data.get("conversion_method", "adaptive")
        if current_method == "bnk":
            self.bnk_overwrite_radio.setChecked(True)
        else:
            self.adaptive_radio.setChecked(True)
            
        conversion_method_layout.addWidget(self.adaptive_radio)
        conversion_method_layout.addWidget(self.bnk_overwrite_radio)
        
        layout.addRow(conversion_method_group)
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addRow(btn_box)
        
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            old_subtitle_lang = self.settings.data["subtitle_lang"]
            old_ui_lang = self.settings.data["ui_language"]
            
            new_ui_lang = lang_combo.currentData()
            new_subtitle_lang = subtitle_combo.currentText()

            self.settings.data["ui_language"] = new_ui_lang
            self.settings.data["theme"] = theme_combo.currentData()
            self.settings.data["subtitle_lang"] = new_subtitle_lang
            self.settings.data["game_path"] = game_path_edit.text()
            self.settings.data["auto_save"] = auto_save_check.isChecked()
            self.settings.data["wem_process_language"] = wem_lang_combo.currentData() 
            if self.bnk_overwrite_radio.isChecked():
                self.settings.data["conversion_method"] = "bnk"
            else:
                self.settings.data["conversion_method"] = "adaptive"
            
            if quick_load_adaptive.isChecked():
                self.settings.data["quick_load_mode"] = "adaptive"
            else:
                self.settings.data["quick_load_mode"] = "strict"
            
            self.settings.save()

            self.apply_settings()

            if new_ui_lang != old_ui_lang:
                self.current_lang = new_ui_lang
                
                msg_box = QtWidgets.QMessageBox(self)
                msg_box.setWindowTitle(self.tr("settings_saved_title"))
                msg_box.setText(self.tr("close_required_message"))
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                
                close_btn = msg_box.addButton(self.tr("close_now_button"), QtWidgets.QMessageBox.AcceptRole)
                later_btn = msg_box.addButton(self.tr("cancel"), QtWidgets.QMessageBox.RejectRole)
                
                msg_box.exec_()

                if msg_box.clickedButton() == close_btn:
                    self.close()
                else:
                    self.current_lang = old_ui_lang

            if new_subtitle_lang != old_subtitle_lang:
                DEBUG.log(f"Subtitle language changed from {old_subtitle_lang} to {new_subtitle_lang}")
                self.load_subtitles()
                self.modified_subtitles.clear()
                for key, value in self.subtitles.items():
                    if key in self.original_subtitles and self.original_subtitles[key] != value:
                        self.modified_subtitles.add(key)
                    elif key not in self.original_subtitles:
                        self.modified_subtitles.add(key)
                DEBUG.log(f"Recalculated modified subtitles for {new_subtitle_lang}: {len(self.modified_subtitles)} found.")
                for lang in list(self.populated_tabs):
                    self.populate_tree(lang)
                self.update_status()

                if hasattr(self, 'subtitle_table'):
                    self.load_subtitle_editor_data()

    def browse_game_path(self, edit_widget):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, self.tr("select_game_path"), 
            edit_widget.text() or ""
        )
        
        if folder:
            edit_widget.setText(folder)

    def update_ui_language(self):
        self.setWindowTitle(self.tr("app_title"))
        
        # update menus
        self.menuBar().clear()
        self.create_menu_bar()
        
        # update tabs
        for i, (lang, widgets) in enumerate(self.tab_widgets.items()):
            if i < self.tabs.count() - 1:
                # update filter combo
                current_filter = widgets["filter_combo"].currentIndex()
                widgets["filter_combo"].clear()
                widgets["filter_combo"].addItems([
                    self.tr("all_files"), 
                    self.tr("with_subtitles"), 
                    self.tr("without_subtitles"), 
                    self.tr("modified"),
                    self.tr("modded")
                ])
                widgets["filter_combo"].setCurrentIndex(current_filter)
                
                tab_widget = self.tabs.widget(i)
                if tab_widget:
                    self.update_group_boxes_recursively(tab_widget)

    def update_group_boxes_recursively(self, widget):

        if isinstance(widget, QtWidgets.QGroupBox):
            title = widget.title()

            if "subtitle" in title.lower() or "preview" in title.lower():
                widget.setTitle(self.tr("subtitle_preview"))
            elif "file" in title.lower() or "info" in title.lower():
                widget.setTitle(self.tr("file_info"))

        for child in widget.findChildren(QtWidgets.QWidget):
            if isinstance(child, QtWidgets.QGroupBox):
                title = child.title()

                if "subtitle" in title.lower() or "preview" in title.lower():
                    child.setTitle(self.tr("subtitle_preview"))
                elif "file" in title.lower() or "info" in title.lower():
                    child.setTitle(self.tr("file_info"))
