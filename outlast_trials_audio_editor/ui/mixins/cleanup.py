from ._imports import *

class CleanupMixin:
    def create_wem_processor_main_tab(self):
        """Create WEM processor with subtabs"""
   
        wem_tab = QtWidgets.QWidget()
        wem_layout = QtWidgets.QVBoxLayout(wem_tab)
        
  
        warning_label = QtWidgets.QLabel(f"""
        <div style="background-color: #ffebcc; border: 2px solid #ff9800; padding: 10px; border-radius: 5px;">
        <h3 style="color: #e65100; margin: 0;">{self.tr("wem_processor_warning")}</h3>
        <p style="margin: 5px 0;"><b>{self.tr("wem_processor_desc")}</b></p>
        <p style="margin: 5px 0;">{self.tr("wem_processor_recommendation")}</p>
        </div>
        """)
        wem_layout.addWidget(warning_label)
   
        self.wem_processor_tabs = QtWidgets.QTabWidget()

        self.create_wem_processing_tab()
        
        wem_layout.addWidget(self.wem_processor_tabs)
        
        self.converter_tabs.addTab(wem_tab, self.tr("wem_processor_tab_title"))

    def show_cleanup_dialog(self, subtitle_files, localization_path):
        
        if subtitle_files:
            DEBUG.log(f"First subtitle file keys: {list(subtitle_files[0].keys())}")
            DEBUG.log(f"First subtitle file: {subtitle_files[0]}")
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(self.tr("cleanup_mod_subtitles"))
        dialog.setMinimumSize(800, 600)
        
        layout = QtWidgets.QVBoxLayout(dialog)

        header_label = QtWidgets.QLabel(self.tr("cleanup_subtitles_found").format(count=len(subtitle_files)))
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(header_label)
        
        info_label = QtWidgets.QLabel(f"Location: {localization_path}")
        info_label.setStyleSheet("color: #666; padding-bottom: 10px;")
        layout.addWidget(info_label)

        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls_widget)
        
        select_all_btn = QtWidgets.QPushButton(self.tr("select_all"))
        select_none_btn = QtWidgets.QPushButton(self.tr("select_none"))
        
        controls_layout.addWidget(select_all_btn)
        controls_layout.addWidget(select_none_btn)
        controls_layout.addStretch()

        group_label = QtWidgets.QLabel(self.tr("quick_select"))
        controls_layout.addWidget(group_label)

        languages = set()
        for f in subtitle_files:
            if 'language' in f:
                languages.add(f['language'])
            elif 'lang' in f:
                languages.add(f['lang'])
        
        lang_combo = None
        if len(languages) > 1:
            lang_combo = QtWidgets.QComboBox()
            lang_combo.addItem(self.tr("select_by_language"))
            for lang in sorted(languages):
                count = sum(1 for f in subtitle_files if f.get('language', f.get('lang', '')) == lang)
                lang_combo.addItem(f"{lang} ({count} files)")
            controls_layout.addWidget(lang_combo)
        
        layout.addWidget(controls_widget)
        
        list_widget = QtWidgets.QListWidget()
        checkboxes = []
        
        for file_info in subtitle_files:
            item_widget = QtWidgets.QWidget()
            item_layout = QtWidgets.QHBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 2, 5, 2)
            
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(True) 
            checkboxes.append(checkbox)
            
            filename = file_info.get('file') or file_info.get('filename') or file_info.get('path') or str(file_info)
            language = file_info.get('language') or file_info.get('lang') or 'Unknown'
            
            if isinstance(filename, str) and ('/' in filename or '\\' in filename):
                filename = os.path.basename(filename)
            
            file_label = QtWidgets.QLabel(f"{filename} ({language})")
            
            item_layout.addWidget(checkbox)
            item_layout.addWidget(file_label)
            item_layout.addStretch()
            
            list_item = QtWidgets.QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            list_widget.addItem(list_item)
            list_widget.setItemWidget(list_item, item_widget)
        
        layout.addWidget(list_widget)
        
        def select_all():
            for checkbox in checkboxes:
                checkbox.setChecked(True)
        
        def select_none():
            for checkbox in checkboxes:
                checkbox.setChecked(False)
        
        def select_by_language(index):
            if lang_combo and index > 0:
                selected_lang = lang_combo.itemText(index).split(' (')[0]
                for i, file_info in enumerate(subtitle_files):
                    file_lang = file_info.get('language') or file_info.get('lang', '')
                    checkboxes[i].setChecked(file_lang == selected_lang)
        
        select_all_btn.clicked.connect(select_all)
        select_none_btn.clicked.connect(select_none)
        if lang_combo:
            lang_combo.currentIndexChanged.connect(select_by_language)
        
        button_box = QtWidgets.QDialogButtonBox()
        delete_btn = button_box.addButton(self.tr("delete_selected"), QtWidgets.QDialogButtonBox.ActionRole)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        
        cancel_btn = button_box.addButton(QtWidgets.QDialogButtonBox.Cancel)
        
        layout.addWidget(button_box)

        def delete_selected():
            selected_files = []
            for i, checkbox in enumerate(checkboxes):
                if checkbox.isChecked():
                    selected_files.append(subtitle_files[i])
            
            if not selected_files:
                QtWidgets.QMessageBox.warning(
                    dialog, self.tr("no_selection"), 
                    self.tr("select_files_to_delete")
                )
                return

            reply = QtWidgets.QMessageBox.question(
                dialog, self.tr("confirm_deletion"),
                self.tr("delete_files_warning").format(count=len(selected_files)),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self.delete_subtitle_files(selected_files)
                dialog.accept()
        
        delete_btn.clicked.connect(delete_selected)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def delete_subtitle_files(self, files_to_delete):
        """Delete selected subtitle files"""
        DEBUG.log(f"Deleting {len(files_to_delete)} subtitle files")
        
        progress = ProgressDialog(self, "Deleting Subtitle Files")
        progress.show()
        
        deleted_count = 0
        error_count = 0

        self.subtitle_export_status.clear()
        self.subtitle_export_status.append("=== Cleaning Up MOD_P Subtitles ===")
        self.subtitle_export_status.append(f"Deleting {len(files_to_delete)} files...")
        self.subtitle_export_status.append("")
        
        for i, file_info in enumerate(files_to_delete):
            progress.set_progress(
                int((i / len(files_to_delete)) * 100),
                f"Deleting {file_info['filename']}..."
            )
            
            try:
                if os.path.exists(file_info['path']):
                    os.remove(file_info['path'])
                    deleted_count += 1
                    self.subtitle_export_status.append(f"✓ Deleted: {file_info['relative_path']}")
                    DEBUG.log(f"Deleted: {file_info['path']}")
 
                    dir_path = os.path.dirname(file_info['path'])
                    try:
                        if os.path.exists(dir_path) and not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            self.subtitle_export_status.append(f"✓ Removed empty directory: {os.path.basename(dir_path)}")
                            
              
                            parent_dir = os.path.dirname(dir_path)
                            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                                os.rmdir(parent_dir)
                                self.subtitle_export_status.append(f"✓ Removed empty directory: {os.path.basename(parent_dir)}")
                    except OSError:
                        pass 
                        
                else:
                    self.subtitle_export_status.append(f"⚠ File already deleted: {file_info['relative_path']}")
                    
            except Exception as e:
                error_count += 1
                self.subtitle_export_status.append(f"✗ Error deleting {file_info['relative_path']}: {str(e)}")
                DEBUG.log(f"Error deleting {file_info['path']}: {e}", "ERROR")
        
        progress.close()
        
        self.subtitle_export_status.append("")
        self.subtitle_export_status.append("=== Cleanup Complete ===")
        self.subtitle_export_status.append(f"Files deleted: {deleted_count}")
        if error_count > 0:
            self.subtitle_export_status.append(f"Errors: {error_count}")
        
     
        if error_count == 0:
            QtWidgets.QMessageBox.information(
                self, self.tr("cleanup_complete"),
                self.tr("files_deleted_successfully").format(count=deleted_count)
            )
        else:
            QtWidgets.QMessageBox.warning(
                self, self.tr("cleanup_with_errors"),
                self.tr("files_deleted_with_errors").format(count=deleted_count, errors=error_count)
            )
        
        DEBUG.log(f"Cleanup complete: {deleted_count} deleted, {error_count} errors")

    def cleanup_mod_p_subtitles(self):
        """Clean up subtitle files from MOD_P folder"""
        DEBUG.log("=== Cleanup MOD_P Subtitles ===")
        
        localization_path = os.path.join(self.mod_p_path, "OPP", "Content", "Localization")
        
        if not os.path.exists(localization_path):
            QtWidgets.QMessageBox.information(
                self, self.tr("no_localization_found"), 
                self.tr("no_localization_message").format(path=localization_path)
            )
            return
        

        subtitle_files = []
        
        try:
            for root, dirs, files in os.walk(localization_path):
                for file in files:
                    if file.endswith('.locres'):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, localization_path)
                        
                     
                        path_parts = relative_path.split(os.sep)
                        if len(path_parts) >= 3:
                            category = path_parts[0]
                            language = path_parts[1]
                            filename = path_parts[2]
                        else:
                            category = "Unknown"
                            language = "Unknown"
                            filename = file
                  
                        file_size = os.path.getsize(file_path)
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        subtitle_files.append({
                            'path': file_path,
                            'relative_path': relative_path,
                            'category': category,
                            'language': language,
                            'filename': filename,
                            'size': file_size,
                            'modified': file_time
                        })
        
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error scanning localization folder:\n{str(e)}")
            return
        
        if not subtitle_files:
            QtWidgets.QMessageBox.information(
                self, self.tr("no_localization_found"), 
                self.tr("no_subtitle_files").format(path=localization_path)
            )
            return
        
        DEBUG.log(f"Found {len(subtitle_files)} subtitle files in MOD_P")
        

        self.show_cleanup_dialog(subtitle_files, localization_path)

    def create_localization_exporter_simple_tab(self):
        """Create simple localization exporter tab with cleanup functionality"""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        
        header = QtWidgets.QLabel(self.tr("localization_exporter"))
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        info_group = QtWidgets.QGroupBox(self.tr("export_modified_subtitles"))
        info_layout = QtWidgets.QVBoxLayout(info_group)
        
        info_text = QtWidgets.QLabel(f"""   
            <h3>{self.tr("export_modified_subtitles")}</h3>
            <p>{self.tr("exports_modified_subtitles_desc")}</p>
            <ul>
                <li>{self.tr("creates_mod_p_structure")}</li>
                <li>{self.tr("supports_multiple_categories")}</li>
                <li>{self.tr("each_language_separate_folder")}</li>
                <li>{self.tr("ready_files_for_mods")}</li>
            </ul>
            """)
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
    
        buttons_widget = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout(buttons_widget)
        
      
        export_btn = QtWidgets.QPushButton(self.tr("export_subtitles_for_game"))
        export_btn.setMaximumWidth(200)
        export_btn.clicked.connect(self.export_subtitles_for_game)
        
 
        cleanup_btn = QtWidgets.QPushButton(self.tr("cleanup_mod_subtitles"))
        cleanup_btn.setMaximumWidth(200)
        cleanup_btn.clicked.connect(self.cleanup_mod_p_subtitles)
        
        buttons_layout.addWidget(export_btn)
        buttons_layout.addWidget(cleanup_btn)
        buttons_layout.addStretch()
        
        layout.addWidget(buttons_widget)
        
     
        self.subtitle_export_status = QtWidgets.QTextEdit()
        self.subtitle_export_status.setReadOnly(True)
        self.subtitle_export_status.setPlainText(self.tr("subtitle_export_ready"))
        layout.addWidget(self.subtitle_export_status)

    def create_wem_processing_tab(self):

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        
        header = QtWidgets.QLabel("WEM File Processing")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        card = QtWidgets.QGroupBox("Instructions")
        card_layout = QtWidgets.QVBoxLayout(card)
        
        instructions = QtWidgets.QLabel(self.tr("converter_instructions2"))
        instructions.setWordWrap(True)
        card_layout.addWidget(instructions)
        
        layout.addWidget(card)
        
        path_group = QtWidgets.QGroupBox("Source Path")
        path_layout = QtWidgets.QHBoxLayout(path_group)
        
        self.wwise_path_edit_old = QtWidgets.QLineEdit()
        self.wwise_path_edit_old.setPlaceholderText("Select WWISE folder...")
        
        browse_btn = ModernButton(self.tr("browse"), primary=True)
        browse_btn.clicked.connect(self.select_wwise_folder_old)
        
        path_layout.addWidget(self.wwise_path_edit_old)
        path_layout.addWidget(browse_btn)
        
        layout.addWidget(path_group)
        
        self.process_btn = ModernButton(self.tr("process_wem_files_btn"), primary=True)
        self.process_btn.clicked.connect(self.process_wem_files)
        layout.addWidget(self.process_btn)
        
    
        self.open_target_btn = ModernButton(self.tr("open_target_folder_btn"))
        self.open_target_btn.clicked.connect(self.open_target_folder)
        layout.addWidget(self.open_target_btn)


        self.converter_status_old = QtWidgets.QTextEdit()
        self.converter_status_old.setReadOnly(True)
        layout.addWidget(self.converter_status_old)
        
        self.wem_processor_tabs.addTab(tab, "Process WEM")

    def browse_wwise_path(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose Wwise path",
            self.wwise_path_edit.text() or ""
        )
        if folder:
            self.wwise_path_edit.setText(folder)
            self.settings.data["wav_wwise_path"] = folder
            self.settings.save()
            
            if hasattr(self, 'wav_converter'):
                project_path = self.converter_project_path_edit.text()
                if project_path:
                    self.wav_converter.set_paths(folder, project_path, self.wav_converter.output_folder or tempfile.gettempdir())

    def browse_converter_project_path(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose path for Wwise project",
            self.converter_project_path_edit.text() or ""
        )
        if folder:
            self.converter_project_path_edit.setText(folder)
            self.settings.data["wav_project_path"] = folder
            self.settings.save()
  
            if hasattr(self, 'wav_converter'):
                wwise_path = self.wwise_path_edit.text()
                if wwise_path:
                    self.wav_converter.set_paths(wwise_path, folder, self.wav_converter.output_folder or tempfile.gettempdir())

    def browse_wav_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose folder with Audio files",
            self.wav_folder_edit.text() or ""
        )
        if folder:
            self.wav_folder_edit.setText(folder)
            self.settings.data["wav_folder_path"] = folder
            self.settings.save()

    def clear_conversion_files(self):
        """Clear conversion files list"""
        if self.wav_converter.file_pairs:
            reply = QtWidgets.QMessageBox.question(
                self, self.tr("confirmation"), 
                self.tr("confirm_clear"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.wav_converter.clear_file_pairs()
                self.conversion_files_table.setRowCount(0)
                self.update_conversion_files_table()
        self.save_converter_file_list()

    def update_conversion_files_list(self):
        self.conversion_files_list.clear()
        for i, pair in enumerate(self.wav_converter.file_pairs):
            display_text = f"{i+1}. {pair['wav_name']} → {pair['target_name']} ({pair['target_size']:,} bytes)"
            self.conversion_files_list.addItem(display_text)

    def select_wwise_folder_old(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select WWISE Folder", 
            self.settings.data.get("last_directory", "")
        )
        
        if folder:
            self.wwise_path_edit_old.setText(folder)
            self.settings.data["last_directory"] = folder
            self.settings.save()

    def update_filter_combo(self, lang):
        widgets = self.tab_widgets[lang]
        filter_combo = widgets["filter_combo"]
        try:
            filter_combo.currentIndexChanged.disconnect()
        except TypeError:
            pass
        current_text = filter_combo.currentText()
        filter_combo.clear()
        filter_combo.addItems([
            self.tr("all_files"), 
            self.tr("with_subtitles"), 
            self.tr("without_subtitles"), 
            self.tr("modified"),
            self.tr("modded")
        ])
        unique_tags = set()
        for entry in self.entries_by_lang.get(lang, []):
            key = os.path.splitext(entry.get("ShortName", ""))[0]
            marking = self.marked_items.get(key, {})
            tag = marking.get('tag')
            if tag:
                unique_tags.add(tag)

        if unique_tags:
            filter_combo.addItem("--- Tags ---")
            for tag in sorted(unique_tags):
                filter_combo.addItem(f"With Tag: {tag}")

        new_index = filter_combo.findText(current_text)
        if new_index >= 0:
            filter_combo.setCurrentIndex(new_index)
        else:
            filter_combo.setCurrentIndex(0)

        filter_combo.currentIndexChanged.connect(lambda: self.populate_tree(lang))
