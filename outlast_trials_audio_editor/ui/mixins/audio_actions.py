from ._imports import *

class AudioActionsMixin:
    def create_toolbar(self):
        toolbar = QtWidgets.QToolBar()
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        self.profile_action = toolbar.addAction(f"👤 {self.tr('profiles')}")
        self.profile_action.setToolTip(self.tr("profile_manager_tooltip"))
        self.profile_action.triggered.connect(self.show_profile_manager)
        
        toolbar.addSeparator()
        self.edit_subtitle_action = toolbar.addAction(self.tr("edit_button"))
        self.edit_subtitle_action.setShortcut("F2")
        self.edit_subtitle_action.triggered.connect(self.edit_current_subtitle)
        
        self.save_wav_action = toolbar.addAction(self.tr("export_button"))
        self.save_wav_action.setShortcut("Ctrl+E")
        self.save_wav_action.triggered.connect(self.save_current_wav)
        self.volume_adjust_action = toolbar.addAction(self.tr("volume_toolbar_btn"))
        self.volume_adjust_action.setToolTip(self.tr("volume_adjust_tooltip_no_selection"))
        self.volume_adjust_action.triggered.connect(self.adjust_selected_volume)
        self.delete_mod_action = toolbar.addAction(self.tr("delete_mod_button"))
        self.delete_mod_action.setToolTip("Delete modified audio for selected file")
        self.delete_mod_action.triggered.connect(self.delete_current_mod_audio)
        toolbar.addSeparator()
        
        self.expand_all_action = toolbar.addAction(self.tr("expand_all"))
        self.expand_all_action.triggered.connect(self.expand_all_trees)
        
        self.collapse_all_action = toolbar.addAction(self.tr("collapse_all"))
        self.collapse_all_action.triggered.connect(self.collapse_all_trees)

    def adjust_selected_volume(self):
        """Adjust volume for selected file(s) - works for single or multiple selection"""
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            QtWidgets.QMessageBox.information(self, self.tr("no_language_selected"), self.tr("select_language_tab_first"))
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        file_items = [item for item in items if item.childCount() == 0 and item.data(0, QtCore.Qt.UserRole)]
        
        if not file_items:
            QtWidgets.QMessageBox.information(self, self.tr("no_files_selected"), self.tr("select_files_for_volume"))
            return
        
        if not hasattr(self, 'wav_converter'):
            self.wav_converter = WavToWemConverter(self)
        
        if len(file_items) == 1:
            entry = file_items[0].data(0, QtCore.Qt.UserRole)
            self.adjust_single_file_volume(entry, current_lang)
        else:
            self.adjust_multiple_files_volume(file_items, current_lang)

    def adjust_single_file_volume(self, entry, lang):
        """Adjust volume for single file"""
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(self.tr("select_version_title"))
        msg.setText(self.tr("adjust_volume_for").format(filename=entry.get('ShortName', '')))
        original_btn = msg.addButton(self.tr("original"), QtWidgets.QMessageBox.ActionRole)
        
        file_id = entry.get("Id", "")
        
        mod_wem_path = self.get_mod_path(file_id, lang)
        
        mod_btn = None
        if os.path.exists(mod_wem_path):
            mod_btn = msg.addButton(self.tr("mod"), QtWidgets.QMessageBox.ActionRole)
        
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        msg.exec_()
        
        if msg.clickedButton() == original_btn:
            dialog = WemVolumeEditDialog(self, entry, lang, False)
            dialog.exec_()
        elif mod_btn and msg.clickedButton() == mod_btn:
            dialog = WemVolumeEditDialog(self, entry, lang, True)
            dialog.exec_()

    def adjust_multiple_files_volume(self, file_items, lang):
        """Adjust volume for multiple files"""

        entries_and_lang = []
        for item in file_items:
            entry = item.data(0, QtCore.Qt.UserRole)
            if entry:
                entries_and_lang.append((entry, lang))
        
        if not entries_and_lang:
            return
        
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(self.tr("select_version_title"))
        msg.setText(self.tr("batch_adjust_volume_for").format(count=len(entries_and_lang)))

        original_btn = msg.addButton(self.tr("original"), QtWidgets.QMessageBox.ActionRole)

        has_mod_files = False
        for entry, _ in entries_and_lang:
            file_id = entry.get("Id", "")
            if lang != "SFX":
                mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem")
            else:
                mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
            
            if os.path.exists(mod_wem_path):
                has_mod_files = True
                break
        
        mod_btn = None
        if has_mod_files:
            mod_btn = msg.addButton("Mod", QtWidgets.QMessageBox.ActionRole)
        
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        msg.exec_()
        
        if msg.clickedButton() == original_btn:
            dialog = BatchVolumeEditDialog(self, entries_and_lang, False)
            dialog.exec_()
        elif mod_btn and msg.clickedButton() == mod_btn:
            dialog = BatchVolumeEditDialog(self, entries_and_lang, True)
            dialog.exec_()

    def delete_current_mod_audio(self):
        """Delete mod audio for currently selected file"""
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items or items[0].childCount() > 0:
            return
            
        item = items[0]
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            return
            
        self.delete_mod_audio(entry, current_lang)

    def on_item_double_clicked(self, item, column):
        if item.childCount() > 0: 
            return
            
        if column == 2:  
            self.edit_current_subtitle()
        else:
            self.play_current()

    def get_backup_path(self, file_id, lang):
        backup_root = os.path.join(self.base_path, ".backups", "audio")
        
        if lang != "SFX":
            backup_dir = os.path.join(backup_root, lang)
        else:
            backup_dir = os.path.join(backup_root, "SFX")
        
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, f"{file_id}.wem")
        
        DEBUG.log(f"Backup path for {file_id} ({lang}): {backup_path}")
        return backup_path

    def create_backup_if_needed(self, file_id, lang):
        if lang != "SFX":
            mod_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem")
        else:
            mod_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
        
        backup_path = self.get_backup_path(file_id, lang)
        
        if os.path.exists(mod_path) and not os.path.exists(backup_path):
            shutil.copy2(mod_path, backup_path)
            DEBUG.log(f"Created backup: {backup_path}")
            return True
        
        DEBUG.log(f"Backup not created: mod_exists={os.path.exists(mod_path)}, backup_exists={os.path.exists(backup_path)}")
        return False

    def restore_from_backup(self, file_id, lang):
        backup_path = self.get_backup_path(file_id, lang)
        
        if not os.path.exists(backup_path):
            return False, "No backup found"
        
        try:
            backup_wem_size = os.path.getsize(backup_path)
        except Exception as e:
            return False, f"Could not read backup file: {e}"

        if lang != "SFX":
            mod_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", lang, f"{file_id}.wem")
        else:
            mod_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", f"{file_id}.wem")
        
        try:
            os.makedirs(os.path.dirname(mod_path), exist_ok=True)
            shutil.copy2(backup_path, mod_path)
            DEBUG.log(f"Restored WEM: {mod_path} (Size: {backup_wem_size})")
        except Exception as e:
            return False, str(e)
            
        try:
            source_id = int(file_id)
            bnk_updated_count = 0
            
            bnk_files_info = self.find_relevant_bnk_files()

            for bnk_path, bnk_type in bnk_files_info:
    
                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else:
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                
                if not os.path.exists(mod_bnk_path):
                    os.makedirs(os.path.dirname(mod_bnk_path), exist_ok=True)
                    shutil.copy2(bnk_path, mod_bnk_path)
                    DEBUG.log(f"Created new mod BNK for restoration: {os.path.basename(mod_bnk_path)}")

                if os.path.exists(mod_bnk_path):
                    mod_editor = BNKEditor(mod_bnk_path)

                    if mod_editor.modify_sound(source_id, new_size=backup_wem_size):
                        mod_editor.save_file()
                        self.invalidate_bnk_cache(source_id)
                        bnk_updated_count += 1

            return True, f"Restored WEM and updated {bnk_updated_count} BNK files."
        
        except Exception as e:
            return False, f"WEM restored but BNK update failed: {str(e)}"

    def has_backup(self, file_id, lang):
        backup_path = self.get_backup_path(file_id, lang)
        exists = os.path.exists(backup_path)
        DEBUG.log(f"Checking backup for {file_id} ({lang}): {backup_path} - exists: {exists}")
        return exists

    def get_dark_menu_style(self):
        return """
            QMenu {
                background-color: #3c3f41;
                color: #d4d4d4;
                border: 1px solid #555555;
                padding: 2px; 
            }
            QMenu::item {
                padding: 4px 20px 4px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #555555;
                margin: 4px 0px 4px 0px;
            }
        """

    def show_context_menu(self, lang, pos):
        widgets = self.tab_widgets[lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items:
            return
            
        menu = QtWidgets.QMenu()
        if self.settings.data["theme"] == "dark":
            menu.setStyleSheet(self.get_dark_menu_style())
            
        file_items = [item for item in items if item.childCount() == 0 and item.data(0, QtCore.Qt.UserRole)]
        
        if file_items:
            play_action = menu.addAction(self.tr("play_original"))
            play_action.triggered.connect(self.play_current)
            menu.addSeparator()
        
            entry = items[0].data(0, QtCore.Qt.UserRole)
            mod_wem_path = None 

            if entry:
                file_id = entry.get('Id', '')
  
                mod_wem_path = self.get_mod_path(file_id, lang)
                
                if mod_wem_path and os.path.exists(mod_wem_path):
                    play_mod_action = menu.addAction(self.tr("play_mod"))
                    play_mod_action.triggered.connect(lambda: self.play_current(play_mod=True))
                    
                    delete_mod_action = menu.addAction(f" {self.tr('delete_mod_audio')}")
                    delete_mod_action.triggered.connect(lambda: self.delete_mod_audio(entry, lang))
                    menu.addSeparator()
                    
                if len(items) == 1 and items[0].childCount() == 0:
                    entry = items[0].data(0, QtCore.Qt.UserRole)
                    if entry:
                        file_id = entry.get("Id", "")    
                        menu.addSeparator()
                        quick_load_action = menu.addAction(self.tr("quick_load_audio_title"))
                        quick_load_action.setToolTip(self.tr("quick_load_audio_tooltip"))
                        quick_load_action.triggered.connect(
                            lambda: self.quick_load_custom_audio(entry, lang)
                        )
                        if self.has_backup(file_id, lang):
                            menu.addSeparator()
                            restore_action = menu.addAction(self.tr("restore_from_backup_title"))
                            restore_action.setToolTip(self.tr("restore_from_backup_tooltip"))
                            restore_action.triggered.connect(
                                lambda: self.restore_audio_from_backup(entry, lang)
                            )
                volume_original_action = menu.addAction(self.tr("adjust_original_volume_title"))
                volume_original_action.triggered.connect(lambda: self.adjust_wem_volume(entry, lang, False))    
                trim_original_action = menu.addAction(self.tr("trim_original_audio_title"))
                trim_original_action.triggered.connect(lambda: self.trim_audio(entry, lang, False))
                if os.path.exists(mod_wem_path):             
                    if os.path.exists(mod_wem_path):
                        volume_mod_action = menu.addAction(self.tr("adjust_mod_volume_title"))
                        volume_mod_action.triggered.connect(lambda: self.adjust_wem_volume(entry, lang, True))
                        trim_mod_action = menu.addAction(self.tr("trim_mod_audio_title"))
                        trim_mod_action.triggered.connect(lambda: self.trim_audio(entry, lang, True))
                    menu.addSeparator()

            toggle_fx_action = menu.addAction(self.tr("toggle_ingame_effects_title"))
            toggle_fx_action.triggered.connect(self.toggle_ingame_effects)
            edit_action = menu.addAction(f"✏ {self.tr('edit_subtitle')}")
            edit_action.triggered.connect(self.edit_current_subtitle)

            shortname = entry.get("ShortName", "")
            key = os.path.splitext(shortname)[0]
            if key in self.modified_subtitles:
                revert_action = menu.addAction(f"↩ {self.tr('revert_to_original')}")
                revert_action.triggered.connect(self.revert_subtitle)
            
            menu.addSeparator()
            
            export_action = menu.addAction(self.tr("export_as_wav"))
            export_action.triggered.connect(self.save_current_wav)
            menu.addSeparator()
            marking_menu = menu.addMenu(self.tr("marking_menu_title"))
    
            color_menu = marking_menu.addMenu(self.tr("set_color_menu_title"))
            colors = {
                self.tr("color_green"): QtGui.QColor(200, 255, 200),
                self.tr("color_yellow"): QtGui.QColor(255, 255, 200),
                self.tr("color_red"): QtGui.QColor(255, 200, 200),
                self.tr("color_blue"): QtGui.QColor(200, 200, 255),
                self.tr("color_none"): None
            }
            for color_name, color in colors.items():
                action = color_menu.addAction(color_name)
                action.triggered.connect(lambda checked, c=color: self.set_item_color(items, c))
            
            tag_menu = marking_menu.addMenu(self.tr("set_tag_menu_title"))
            tags = [self.tr("tag_important"), self.tr("tag_check"), self.tr("tag_done"), self.tr("tag_review"), "None"]
            for tag in tags:
                action = tag_menu.addAction(tag)
                action.triggered.connect(lambda checked, t=tag: self.set_item_tag(items, t if t != "None" else ""))
            custom_action = tag_menu.addAction(self.tr("tag_custom"))
            custom_action.triggered.connect(lambda: self.set_custom_tag(items))
            
        menu.exec_(tree.viewport().mapToGlobal(pos))

    def trim_audio(self, entry, lang, is_mod=False):
        dialog = AudioTrimDialog(self, entry, lang, is_mod)
        dialog.exec_()

    def set_custom_tag(self, items):
        tag, ok = QtWidgets.QInputDialog.getText(self, self.tr("custom_tag_title"), self.tr("custom_tag_prompt"))
        if ok and tag.strip():
            self.set_item_tag(items, tag.strip())

    def set_item_color(self, items, color):
        for item in items:
            if item.childCount() == 0:
                entry = item.data(0, QtCore.Qt.UserRole)
                if entry:
                    shortname = entry.get("ShortName", "")
                    key = os.path.splitext(shortname)[0]
                    
                    if color is None:
                        self.marked_items.pop(key, None)
                    else:
                        if key not in self.marked_items:
                            self.marked_items[key] = {}
                        self.marked_items[key]['color'] = color
                    
                    for col in range(5):
                        item.setBackground(col, color if color else QtGui.QColor(255, 255, 255))
        
        self.settings.save()

    def set_item_tag(self, items, tag):
        for item in items:
            if item.childCount() == 0: 
                entry = item.data(0, QtCore.Qt.UserRole)
                if entry:
                    shortname = entry.get("ShortName", "")
                    key = os.path.splitext(shortname)[0]
                    if tag == "":
                        if key in self.marked_items and 'tag' in self.marked_items[key]:
                            del self.marked_items[key]['tag']
                            if not self.marked_items[key]:
                                del self.marked_items[key]
                    else:
                        if key not in self.marked_items:
                            self.marked_items[key] = {}
                        self.marked_items[key]['tag'] = tag
                    item.setText(4, tag)
        current_lang = self.get_current_language()
        if current_lang:
            self.update_filter_combo(current_lang)
            self.populate_tree(current_lang)

    def restore_audio_from_backup(self, entry, lang):
        file_id = entry.get("Id", "")
        shortname = entry.get("ShortName", "")
        
        if not self.has_backup(file_id, lang):
            QtWidgets.QMessageBox.information(
                self, "No Backup",
                f"No backup found for {shortname}"
            )
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, "Restore from Backup",
            f"Restore previous version of modified audio for:\n{shortname}\n\n"
            f"This will replace the current modified audio with the backup version.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            success, message = self.restore_from_backup(file_id, lang)
            
            if success:
                self.populate_tree(lang)
                self.status_bar.showMessage(f"Restored {shortname} from backup", 3000)
                QtWidgets.QMessageBox.information(
                    self, "Restored",
                    f"Successfully restored {shortname} from backup!"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Restore Failed",
                    f"Failed to restore {shortname}:\n{message}"
                )

    def quick_load_custom_audio(self, entry, lang, custom_file=None):
        if custom_file:
            audio_file = custom_file
        else:
            audio_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, 
                "Select Audio File",
                "",
                "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a *.aac *.wma *.opus);;All Files (*.*)"
            )
        
        if not audio_file:
            return
        
        if not hasattr(self, 'wav_converter'):
            self.wav_converter = WavToWemConverter(self)
        
        wwise_path = None
        project_path = None
        
        if hasattr(self, 'wwise_path_edit') and hasattr(self, 'converter_project_path_edit'):
            wwise_path = self.wwise_path_edit.text()
            project_path = self.converter_project_path_edit.text()
        
        if not wwise_path or not project_path:
            wwise_path = self.settings.data.get("wav_wwise_path", "")
            project_path = self.settings.data.get("wav_project_path", "")
        
        if not wwise_path or not os.path.exists(wwise_path):
            QtWidgets.QMessageBox.warning(
                self, "Configuration Required",
                "Wwise path not found or invalid.\n\n"
                "Please go to Converter tab and set valid Wwise installation path."
            )
            return
        
        if not project_path:
            QtWidgets.QMessageBox.warning(
                self, "Configuration Required",
                "Project path not set.\n\n"
                "Please go to Converter tab and set project path."
            )
            return
        
        temp_output = tempfile.mkdtemp(prefix="quick_load_")
        
        self.wav_converter.set_paths(wwise_path, project_path, temp_output)
        
        progress = ProgressDialog(self, self.tr("quick_load_audio_title"))
        progress.setWindowFlags(progress.windowFlags() | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        progress.setWindowFlags(progress.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        progress.show()
        
        thread = threading.Thread(
            target=self._quick_load_audio_thread,
            args=(audio_file, entry, lang, progress, temp_output)
        )
        thread.daemon = True
        thread.start()

    def adjust_wem_volume(self, entry, lang, is_mod=False):
        if not hasattr(self, 'wav_converter'):
            self.wav_converter = WavToWemConverter(self)
            
            if hasattr(self, 'wwise_path_edit') and hasattr(self, 'converter_project_path_edit'):
                wwise_path = self.wwise_path_edit.text()
                project_path = self.converter_project_path_edit.text()
                
                if wwise_path and project_path:
                    self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
        
        dialog = WemVolumeEditDialog(self, entry, lang, is_mod)
        dialog.exec_()

    def _quick_load_audio_thread(self, audio_file, entry, lang, progress, temp_output):
        try:
            file_id = entry.get("Id", "")
            shortname = entry.get("ShortName", "")
            original_filename = os.path.splitext(shortname)[0]
            
            audio_ext = os.path.splitext(audio_file)[1].lower()
            if audio_ext != '.wav':
                QtCore.QMetaObject.invokeMethod(
                    progress, "set_progress",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(int, 20),
                    QtCore.Q_ARG(str, "Converting to WAV...")
                )
                
                audio_converter = AudioToWavConverter()
                if not audio_converter.is_available():
                    raise Exception("FFmpeg not found. Please install FFmpeg for non-WAV file support.")
                
                temp_wav = os.path.join(temp_output, f"{original_filename}.wav")
                success, result = audio_converter.convert_to_wav(audio_file, temp_wav)
                
                if not success:
                    raise Exception(f"Audio conversion failed: {result}")
                    
                wav_file = temp_wav
                needs_cleanup = True
            else:
                wav_file = os.path.join(temp_output, f"{original_filename}.wav")
                shutil.copy2(audio_file, wav_file)
                needs_cleanup = True
            
            original_wem = os.path.join(self.wem_root, lang, f"{file_id}.wem")
            if not os.path.exists(original_wem):
                raise Exception(f"Original WEM not found: {original_wem}")
                
            target_size = os.path.getsize(original_wem)
            
            QtCore.QMetaObject.invokeMethod(
                progress, "set_progress",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(int, 50),
                QtCore.Q_ARG(str, "Converting to WEM...")
            )
            
            file_pair = {
                "wav_file": wav_file,
                "target_wem": original_wem,
                "wav_name": f"{original_filename}.wav",
                "target_name": f"{original_filename}.wem",
                "target_size": target_size,
                "language": lang,
                "file_id": file_id
            }
            
            quick_mode = self.settings.data.get("quick_load_mode", "strict")
            self.wav_converter.set_adaptive_mode(quick_mode == "adaptive")
            
            if not self.wav_converter.wwise_path:
                raise Exception("Wwise converter not properly configured")
            
            result = self.wav_converter.convert_single_file_main(file_pair, 1, 1)
            
            if not result.get('success'):
                raise Exception(result.get('error', 'Conversion failed'))
            
            QtCore.QMetaObject.invokeMethod(
                progress, "set_progress",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(int, 80),
                QtCore.Q_ARG(str, "Deploying to MOD_P...")
            )
            
            source_wem = result['output_path']
            
            if lang != "SFX":
                target_dir = os.path.join(
                    self.mod_p_path, "OPP", "Content", "WwiseAudio", 
                    "Windows", "Media", lang
                )
            else:
                target_dir = os.path.join(
                    self.mod_p_path, "OPP", "Content", "WwiseAudio", 
                    "Windows", "Media"
                )
            
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, f"{file_id}.wem")
            
            if os.path.exists(target_path):
                backup_path = self.get_backup_path(file_id, lang)

                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    DEBUG.log(f"Removed old backup: {backup_path}")
                
                shutil.copy2(source_wem, backup_path)
                DEBUG.log(f"Created new backup from loaded audio: {backup_path}")
            
            shutil.copy2(source_wem, target_path)
            
            QtCore.QMetaObject.invokeMethod(
                progress, "set_progress",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(int, 100),
                QtCore.Q_ARG(str, "Complete!")
            )
            
            if needs_cleanup and os.path.exists(wav_file):
                try:
                    os.remove(wav_file)
                except:
                    pass
                    
            if os.path.exists(source_wem) and source_wem != target_path:
                try:
                    os.remove(source_wem)
                except:
                    pass
                    
            if temp_output and os.path.exists(temp_output):
                try:
                    shutil.rmtree(temp_output)
                except:
                    pass
            
            QtCore.QMetaObject.invokeMethod(
                progress, "close",
                QtCore.Qt.QueuedConnection
            )
            
            QtCore.QMetaObject.invokeMethod(
                self, "_quick_load_complete",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, lang),
                QtCore.Q_ARG(str, shortname)
            )
            
        except Exception as e:
  
            QtCore.QMetaObject.invokeMethod(
                progress, "close",
                QtCore.Qt.QueuedConnection
            )
            
            QtCore.QMetaObject.invokeMethod(
                self, "_quick_load_error",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, str(e))
            )

    def batch_adjust_volume(self):
        """Batch adjust volume for multiple selected files"""
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        file_items = [item for item in items if item.childCount() == 0]
        
        if not file_items:
            QtWidgets.QMessageBox.information(
                self, "No Files Selected",
                "Please select audio files to adjust volume."
            )
            return
        
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(self.tr("select_version_title"))
        msg.setText("Which version would you like to adjust?")
        
        original_btn = msg.addButton("Original", QtWidgets.QMessageBox.ActionRole)
        mod_btn = msg.addButton("Mod", QtWidgets.QMessageBox.ActionRole)
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        
        msg.exec_()
        
        is_mod = False
        if msg.clickedButton() == mod_btn:
            is_mod = True
        elif msg.clickedButton() != original_btn:
            return

    def _batch_export_wav_thread(self, file_items, lang, export_mod, directory, progress):
        errors = []
        successful_count = 0
        overwrite_all = False

        for i, item in enumerate(file_items):
            entry = item.data(0, QtCore.Qt.UserRole)
            if not entry:
                continue
                
            id_ = entry.get("Id", "")
            shortname = entry.get("ShortName", "")
            
            QtCore.QMetaObject.invokeMethod(progress, "set_progress", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(int, int((i / len(file_items)) * 100)),
                                            QtCore.Q_ARG(str, f"Converting {shortname}..."))
            
            wem_path = None
            if export_mod:
                mod_wem_path = self.get_mod_path(id_, lang)
                if mod_wem_path and os.path.exists(mod_wem_path):
                    wem_path = mod_wem_path
                else:
                    wem_path = self.get_original_path(id_, lang)
            else:
                wem_path = self.get_original_path(id_, lang)
            
            wav_path = os.path.join(directory, shortname)
            
            if os.path.exists(wav_path) and not overwrite_all:
     
                result = QtCore.QMetaObject.invokeMethod(self, "_ask_overwrite", QtCore.Qt.BlockingQueuedConnection,
                                                         QtCore.Q_ARG(str, shortname))
                
                if result == "No":
                    errors.append(f"{shortname}: Skipped by user")
                    continue
                elif result == "No to All":
                    errors.append(f"{shortname}: Skipped by user (cancelled all)")
                    break 
                elif result == "Yes to All":
                    overwrite_all = True
            
            if wem_path and os.path.exists(wem_path):
                ok, err = self.wem_to_wav_vgmstream(wem_path, wav_path)
                if not ok:
                    errors.append(f"{shortname}: {err}")
                    QtCore.QMetaObject.invokeMethod(progress, "append_details", QtCore.Qt.QueuedConnection,
                                                    QtCore.Q_ARG(str, f"Failed: {shortname}"))
                else:
                    successful_count += 1
            else:
                errors.append(f"{shortname}: Source WEM file not found")

        QtCore.QMetaObject.invokeMethod(self, "_on_batch_export_finished", QtCore.Qt.QueuedConnection,
                                        QtCore.Q_ARG(object, progress),
                                        QtCore.Q_ARG(int, successful_count),
                                        QtCore.Q_ARG(list, errors))

    def batch_export_wav(self, items, lang):
        file_items = [item for item in items if item.childCount() == 0]
        
        if not file_items:
            return
            
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(self.tr("batch_export"))
        msg.setText(self.tr("which_version_export") + f"\n\n({len(file_items)} files selected)")
        
        original_btn = msg.addButton(self.tr("original"), QtWidgets.QMessageBox.ActionRole)
        mod_btn = msg.addButton(self.tr("mod"), QtWidgets.QMessageBox.ActionRole)
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        
        has_any_mod = False
        for item in file_items:
            entry = item.data(0, QtCore.Qt.UserRole)
            if entry:
                mod_path = self.get_mod_path(entry.get("Id", ""), lang)
                if mod_path and os.path.exists(mod_path):
                    has_any_mod = True
                    break
        
        if not has_any_mod:
            mod_btn.setEnabled(False)
            mod_btn.setToolTip("No modified audio files found in selection.")
        
        self.show_dialog(msg)
        
        clicked_button = msg.clickedButton()
        export_mod = False
        
        if clicked_button == original_btn:
            export_mod = False
        elif clicked_button == mod_btn:
            export_mod = True
        else:
            return
            
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("select_output_directory"))
        if not directory:
            return
            
        progress = ProgressDialog(self, self.tr("exporting_files").format(count=len(file_items)))
        progress.show()
        progress.raise_()
        progress.activateWindow()

        thread = threading.Thread(target=self._batch_export_wav_thread, args=(file_items, lang, export_mod, directory, progress))
        thread.daemon = True
        thread.start()
