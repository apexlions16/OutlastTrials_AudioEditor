from .common import *
from .debug import DEBUG
from .ui.widgets import ProgressDialog

class ProfileDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, existing_data=None, translator=None):
        super().__init__(parent)
        self.parent_app = parent
        self.is_edit_mode = existing_data is not None
        self.tr = translator if translator else lambda key: key
        self.setWindowTitle(self.tr("edit_profile") if self.is_edit_mode else self.tr("create_profile"))
        self.setMinimumWidth(400)

        self.layout = QtWidgets.QFormLayout(self)
        
        self.name_edit = QtWidgets.QLineEdit()
        self.author_edit = QtWidgets.QLineEdit()
        self.version_edit = QtWidgets.QLineEdit()
        self.description_edit = QtWidgets.QTextEdit()
        self.description_edit.setFixedHeight(80)
        
        self.icon_path = ""
        self.icon_preview = QtWidgets.QLabel(self.tr("no_icon_selected"))
        self.icon_preview.setFixedSize(64, 64)
        self.icon_preview.setStyleSheet("border: 1px solid #ccc; text-align: center;")
        self.icon_preview.setAlignment(QtCore.Qt.AlignCenter)
        
        icon_button = QtWidgets.QPushButton(self.tr("browse"))
        icon_button.clicked.connect(self.select_icon)
        
        icon_layout = QtWidgets.QHBoxLayout()
        icon_layout.addWidget(self.icon_preview)
        icon_layout.addWidget(icon_button)
        icon_layout.addStretch()

        if self.is_edit_mode:
            profile_name = os.path.basename(existing_data["path"])
            self.name_edit.setText(profile_name)
            self.name_edit.setReadOnly(True) 
            
            info = existing_data["data"]
            self.author_edit.setText(info.get("author", ""))
            self.version_edit.setText(info.get("version", "1.0"))
            self.description_edit.setPlainText(info.get("description", ""))
            
            self.icon_path = existing_data["icon"]
            if os.path.exists(self.icon_path):
                pixmap = QtGui.QPixmap(self.icon_path)
                self.icon_preview.setPixmap(pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio))

        self.layout.addRow(self.tr("profile_name"), self.name_edit)
        self.layout.addRow(self.tr("author"), self.author_edit)
        self.layout.addRow(self.tr("version"), self.version_edit)
        self.layout.addRow(self.tr("description"), self.description_edit)
        self.layout.addRow(self.tr("icon_png"), icon_layout)

        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def select_icon(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, self.tr("select_icon"), "", f"{self.tr('png_images')} (*.png)")
        if path:
            self.icon_path = path
            pixmap = QtGui.QPixmap(path)
            self.icon_preview.setPixmap(pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio))

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "icon_path": self.icon_path,
            "info": {
                "author": self.author_edit.text().strip(),
                "version": self.version_edit.text().strip(),
                "description": self.description_edit.toPlainText().strip()
            }
        }
    
    def accept(self):
        if not self.name_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, self.tr("validation_error"), self.tr("profile_name_empty"))
            return
        super().accept()

class ImportModThread(QtCore.QThread):
    finished = QtCore.pyqtSignal(bool, str) # success, message

    def __init__(self, parent_app, pak_path, profile_name):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.tr = parent_app.tr
        self.pak_path = pak_path
        self.profile_name = profile_name
        self.temp_extract_path = os.path.join(tempfile.gettempdir(), f"mod_import_{profile_name}")

    def run(self):
        try:
           
            if os.path.exists(self.temp_extract_path):
                shutil.rmtree(self.temp_extract_path)
            os.makedirs(self.temp_extract_path, exist_ok=True)
            
            command = [self.parent_app.repak_path, "unpack", self.pak_path, "-o", self.temp_extract_path]
            result = subprocess.run(
                command, capture_output=True, text=True, startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW, encoding='utf-8', errors='ignore'
            )
            if result.returncode != 0:
                raise Exception(f"Repak failed to unpack: {result.stderr}")

            profiles_root = os.path.join(self.parent_app.base_path, "Profiles")
            profile_path = os.path.join(profiles_root, self.profile_name)
            mod_p_path = os.path.join(profile_path, f"{self.profile_name}_P")
            os.makedirs(mod_p_path, exist_ok=True)

            unpacked_opp_path = os.path.join(self.temp_extract_path, "OPP")
            if not os.path.exists(unpacked_opp_path):
                raise Exception("Unpacked mod does not contain an 'OPP' folder.")
            
            windows_audio_path = os.path.join(unpacked_opp_path, "Content", "WwiseAudio", "Windows")
            
            if os.path.exists(windows_audio_path):
                needs_conversion = False
                
                for item in os.listdir(windows_audio_path):
                    item_path = os.path.join(windows_audio_path, item)
                    if os.path.isfile(item_path) and item.lower().endswith(".wem"):
                        needs_conversion = True
                        break
                
                if not needs_conversion:
                    for item in os.listdir(windows_audio_path):
                        item_path = os.path.join(windows_audio_path, item)
                        if os.path.isdir(item_path) and item != "Media":
                            for sub_item in os.listdir(item_path):
                                if sub_item.lower().endswith(".wem"):
                                    needs_conversion = True
                                    break
                        if needs_conversion: break

                if needs_conversion:
                   
                    should_convert = QtCore.QMetaObject.invokeMethod(
                        self.parent_app, 
                        "_ask_convert_old_mod_structure", 
                        QtCore.Qt.BlockingQueuedConnection,
                        QtCore.Q_RETURN_ARG(bool)
                    )
                    
                    if should_convert:
                        self.convert_structure_to_media(windows_audio_path)
                    else:
                        DEBUG.log("User declined structure conversion.")

            destination_opp_path = os.path.join(mod_p_path, "OPP")
            if os.path.exists(destination_opp_path):
                shutil.rmtree(destination_opp_path)
            shutil.copytree(unpacked_opp_path, destination_opp_path)

            bnk_deleted_count = 0
            for root, dirs, files in os.walk(destination_opp_path):
                for file in files:
                    if file.lower().endswith(".bnk"):
                        os.remove(os.path.join(root, file))
                        bnk_deleted_count += 1
            if bnk_deleted_count > 0:
                DEBUG.log(f"Removed {bnk_deleted_count} outdated BNK files from imported mod to prevent conflicts.")

            watermark_path = os.path.join(destination_opp_path, "CreatedByAudioEditor.txt")
            if os.path.exists(watermark_path):
                os.remove(watermark_path)

            profile_info = {
                "author": "Imported",
                "version": "1.0",
                "description": f"This profile was imported from '{os.path.basename(self.pak_path)}'."
            }
            with open(os.path.join(profile_path, "profile.json"), 'w', encoding='utf-8') as f:
                json.dump(profile_info, f, indent=2)
            
            self.parent_app.settings.data["mod_profiles"][self.profile_name] = profile_path
            self.parent_app.settings.save()
            
            self.finished.emit(True, self.tr("import_successful_message").format(
                pak_name=os.path.basename(self.pak_path),
                profile_name=self.profile_name
            ))

        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            if os.path.exists(self.temp_extract_path):
                shutil.rmtree(self.temp_extract_path)

    def convert_structure_to_media(self, windows_path):
        """Moves .wem files into a 'Media' subfolder structure."""
        DEBUG.log("Converting old mod structure to new 'Media' format...")
        
        media_root = os.path.join(windows_path, "Media")
        os.makedirs(media_root, exist_ok=True)
        
        items = list(os.listdir(windows_path))
        
        for item in items:
            item_path = os.path.join(windows_path, item)
            
            if item == "Media":
                continue
                
            if os.path.isfile(item_path) and item.lower().endswith(".wem"):
                dest_path = os.path.join(media_root, item)
                try:
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    shutil.move(item_path, dest_path)
                    DEBUG.log(f"Moved {item} to Media root")
                except Exception as e:
                    DEBUG.log(f"Failed to move {item}: {e}", "ERROR")
                
            elif os.path.isdir(item_path):
                lang_folder_name = item
                lang_source_path = item_path
                
                has_wems = any(f.lower().endswith(".wem") for f in os.listdir(lang_source_path))
                
                if has_wems:
                    lang_media_dest = os.path.join(media_root, lang_folder_name)
                    os.makedirs(lang_media_dest, exist_ok=True)
                    
                    for sub_item in os.listdir(lang_source_path):
                        sub_item_path = os.path.join(lang_source_path, sub_item)
                        if os.path.isfile(sub_item_path) and sub_item.lower().endswith(".wem"):
                            dest_sub_path = os.path.join(lang_media_dest, sub_item)
                            try:
                                if os.path.exists(dest_sub_path):
                                    os.remove(dest_sub_path)
                                shutil.move(sub_item_path, dest_sub_path)
                                DEBUG.log(f"Moved {sub_item} to Media/{lang_folder_name}")
                            except Exception as e:
                                DEBUG.log(f"Failed to move {sub_item}: {e}", "ERROR")
                    
                    if not os.listdir(lang_source_path):
                        try:
                            os.rmdir(lang_source_path)
                        except OSError:
                            pass 
                    
        DEBUG.log("Structure conversion complete.")

class ProfileManagerDialog(QtWidgets.QDialog):
    profile_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.settings = parent.settings
        self.tr = parent.tr if hasattr(parent, 'tr') else lambda key: key
        
        self.setWindowTitle(self.tr("profile_manager_title"))
        self.setMinimumSize(850, 550) 

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        left_panel = QtWidgets.QFrame()
        left_panel.setFrameShape(QtWidgets.QFrame.StyledPanel)
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        self.profile_list = QtWidgets.QListWidget()
        self.profile_list.currentItemChanged.connect(self.display_profile_info)
        self.profile_list.setSpacing(3)
        self.profile_list.setIconSize(QtCore.QSize(32, 32)) 
        left_layout.addWidget(self.profile_list)

        left_button_layout = QtWidgets.QGridLayout()
        add_new_btn = QtWidgets.QPushButton(self.tr("create_new_profile_btn"))
        add_existing_btn = QtWidgets.QPushButton(self.tr("add_existing_profile_btn"))
        import_pak_btn = QtWidgets.QPushButton(self.tr("import_mod_from_pak"))
        remove_btn = QtWidgets.QPushButton(self.tr("remove_from_list_btn"))
        
        add_new_btn.clicked.connect(self.create_new_profile)
        add_existing_btn.clicked.connect(self.add_existing_profile)
        import_pak_btn.clicked.connect(self.import_mod_from_pak)
        remove_btn.clicked.connect(self.remove_selected_profile)

        left_button_layout.addWidget(add_new_btn, 0, 0)
        left_button_layout.addWidget(add_existing_btn, 0, 1)
        left_button_layout.addWidget(import_pak_btn, 1, 0, 1, 2)
        left_button_layout.addWidget(remove_btn, 2, 0, 1, 2)
        left_layout.addLayout(left_button_layout)
        
        main_layout.addWidget(left_panel, 2)

        right_panel = QtWidgets.QGroupBox()
        right_panel.setStyleSheet("QGroupBox { padding-top: 10px; }")
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        
        header_layout = QtWidgets.QHBoxLayout()
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setStyleSheet("border: 1px solid #888; border-radius: 5px;")
        self.icon_label.setAlignment(QtCore.Qt.AlignCenter)
        
        title_layout = QtWidgets.QVBoxLayout()
        self.name_label = QtWidgets.QLabel(self.tr("select_a_profile"))
        self.name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.path_label = QtWidgets.QLabel()
        self.path_label.setStyleSheet("color: #888;")
        self.path_label.setWordWrap(True)
        title_layout.addWidget(self.name_label)
        title_layout.addWidget(self.path_label)
        
        header_layout.addWidget(self.icon_label)
        header_layout.addLayout(title_layout)
        right_layout.addLayout(header_layout)

        self.details_tabs = QtWidgets.QTabWidget()
        right_layout.addWidget(self.details_tabs)

        info_tab = QtWidgets.QWidget()
        info_layout = QtWidgets.QVBoxLayout(info_tab)
        
        details_layout = QtWidgets.QFormLayout()
        details_layout.setContentsMargins(10, 15, 10, 15)
        details_layout.setSpacing(10)
        self.author_label = QtWidgets.QLabel()
        self.version_label = QtWidgets.QLabel()
        details_layout.addRow(f"<b>{self.tr('author')}:</b>", self.author_label)
        details_layout.addRow(f"<b>{self.tr('version')}:</b>", self.version_label)
        info_layout.addLayout(details_layout)
        
        self.description_text = QtWidgets.QTextBrowser()
        self.description_text.setOpenExternalLinks(True)
        info_layout.addWidget(self.description_text)
        self.details_tabs.addTab(info_tab, self.tr("info"))
        
        stats_tab = QtWidgets.QWidget()
        stats_layout = QtWidgets.QVBoxLayout(stats_tab)
        
        general_group = QtWidgets.QGroupBox(self.tr("general_stats_group"))
        general_layout = QtWidgets.QFormLayout(general_group)
        self.audio_files_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        self.subtitle_files_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        self.mod_size_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        general_layout.addRow(self.tr("total_audio_files"), self.audio_files_label)
        general_layout.addRow(self.tr("total_subtitle_files"), self.subtitle_files_label)
        general_layout.addRow(self.tr("total_mod_size"), self.mod_size_label)
        stats_layout.addWidget(general_group)
        
        subtitle_group = QtWidgets.QGroupBox(self.tr("subtitle_stats_group"))
        subtitle_layout = QtWidgets.QFormLayout(subtitle_group)
        self.modified_subs_label = QtWidgets.QLabel()
        subtitle_layout.addRow(self.tr("modified_subtitle_entries"), self.modified_subs_label)
        stats_layout.addWidget(subtitle_group)
        
        stats_layout.addStretch()
        self.details_tabs.addTab(stats_tab, self.tr("project_statistics_title"))

        self.activate_btn = QtWidgets.QPushButton()
        self.edit_btn = QtWidgets.QPushButton(f"{self.tr('edit_details_btn')}")
        self.edit_btn.clicked.connect(self.edit_profile)
        
        bottom_button_layout = QtWidgets.QHBoxLayout()
        bottom_button_layout.addWidget(self.edit_btn)
        bottom_button_layout.addStretch()
        bottom_button_layout.addWidget(self.activate_btn)
        right_layout.addLayout(bottom_button_layout)

        main_layout.addWidget(right_panel, 3)

        self.populate_profile_list()
    def import_mod_from_pak(self):
        pak_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("select_pak_to_import"),
            self.settings.data.get("game_path", ""),
            f"{self.tr('pak_files')} (*.pak)"
        )

        if not pak_path:
            return

        default_profile_name = os.path.splitext(os.path.basename(pak_path))[0]
        if default_profile_name.upper().endswith("_P"):
            default_profile_name = default_profile_name[:-2]

        profile_name, ok = QtWidgets.QInputDialog.getText(
            self,
            self.tr("import_mod_title"),
            self.tr("enter_profile_name_for_pak"),
            QtWidgets.QLineEdit.Normal,
            default_profile_name
        )

        if not ok or not profile_name.strip():
            return
            
        profile_name = profile_name.strip()

        if profile_name in self.settings.data.get("mod_profiles", {}):
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("profile_exists_error"))
            return
        self.profile_name_for_import = profile_name
        self.progress_dialog = ProgressDialog(self.parent_app, self.tr("importing_mod_progress"))
        self.progress_dialog.progress.setRange(0, 0)
        self.progress_dialog.show()

        self.import_thread = ImportModThread(self.parent_app, pak_path, profile_name)
        self.import_thread.finished.connect(self.on_import_mod_finished)
        self.import_thread.start()

    def on_import_mod_finished(self, success, message):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        if success:
            profile_name = getattr(self, 'profile_name_for_import', None)
            
            if profile_name:

                profiles_root = self.settings.data.get("mods_root_path")
                if not profiles_root:
                    
                    profiles_root = os.path.join(self.parent_app.base_path, "Profiles")

                new_profile_path = os.path.join(profiles_root, profile_name)
                new_mod_p_path = os.path.join(new_profile_path, f"{profile_name}_P")

                if not hasattr(self.parent_app, 'profiles'):
                    self.parent_app.profiles = {}
                
                self.parent_app.profiles[profile_name] = {
                    "path": new_profile_path,
                    "mod_p_path": new_mod_p_path,
                    "icon": os.path.join(new_profile_path, "icon.png"),
                    "data": {"author": "Imported", "version": "1.0", "description": "Imported from .pak"}
                }

                self.settings.data.get("mod_profiles", {})[profile_name] = new_profile_path
                
                self.parent_app.set_active_profile(profile_name)
                
                if self.parent_app.active_profile_name != profile_name:
                    self.parent_app.active_profile_name = profile_name
                    self.parent_app.mod_p_path = new_mod_p_path
                    self.parent_app.setWindowTitle(f"{self.parent_app.tr('app_title')} - [{profile_name}]")
                    self.settings.data["active_profile"] = profile_name
                    self.settings.save()
                    
                    if hasattr(self.parent_app, 'update_profile_ui'):
                        self.parent_app.update_profile_ui()

            self.populate_profile_list()
            self.profile_changed.emit()

            reply = QtWidgets.QMessageBox.question(
                self,
                self.tr("import_successful_title"),
                f"{message}\n\n"
                f"It is highly recommended to rebuild the BNK index for imported mods.\n"
                f"Do you want to proceed with the rebuild now?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.Yes:
                self.close() 
                QtCore.QTimer.singleShot(300, lambda: self.parent_app.rebuild_bnk_index(confirm=False))
            
        else:
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("import_failed_title"),
                message
            )
            DEBUG.log(f"Mod import failed: {message}", "ERROR")
    def populate_profile_list(self):
        self.profile_list.clear()
        profiles = self.settings.data.get("mod_profiles", {})
        active_profile = self.settings.data.get("active_profile", "")

        for name, path in sorted(profiles.items()):
            item = QtWidgets.QListWidgetItem(name)
            
            icon_path = os.path.join(path, "icon.png")
            if os.path.exists(icon_path):
                item.setIcon(QtGui.QIcon(icon_path))
            else:
           
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))

            if name == active_profile:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))

            self.profile_list.addItem(item)
        
        if self.profile_list.count() > 0:
            self.profile_list.setCurrentRow(0)

    def display_profile_info(self, current, previous):
        if not current:
            self.name_label.setText(self.parent_app.tr("select_a_profile"))
            self.icon_label.clear()
            self.author_label.clear()
            self.version_label.clear()
            self.path_label.clear()
            self.description_text.clear()
            self.activate_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            return

        self.activate_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)
        profile_name = current.text()
        active_profile = self.settings.data.get("active_profile", "")
        
     
        try:
            self.activate_btn.clicked.disconnect()
        except TypeError:
            pass

        if profile_name == active_profile:
            self.activate_btn.setText(self.parent_app.tr("active_profile_btn"))
            self.activate_btn.setEnabled(False)
            self.activate_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        else:
            self.activate_btn.setText(self.parent_app.tr("activate_profile_btn"))
            self.activate_btn.setEnabled(True)
            self.activate_btn.setStyleSheet("") 
            self.activate_btn.clicked.connect(self.activate_profile)

        profiles = self.settings.data.get("mod_profiles", {})
        profile_path = profiles.get(profile_name)

        self.name_label.setText(profile_name)
        self.path_label.setText(profile_path)
        
        icon_path = os.path.join(profile_path, "icon.png")
        if os.path.exists(icon_path):
            pixmap = QtGui.QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        else:
            self.icon_label.setText(self.parent_app.tr("no_icon_selected").replace(" ", "\n"))
            self.icon_label.setPixmap(QtGui.QPixmap())

        json_path = os.path.join(profile_path, "profile.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f: data = json.load(f)
                self.author_label.setText(data.get("author", "N/A"))
                self.version_label.setText(data.get("version", "N/A"))
                self.description_text.setMarkdown(data.get("description", "<i>No description.</i>"))
            except Exception:
                self.author_label.setText(self.parent_app.tr("error_author"))
                self.description_text.setText(self.parent_app.tr("error_reading_profile"))
        self.calculate_statistics_for_profile(profile_name)
    def calculate_statistics_for_profile(self, profile_name):
        self.clear_stats_labels() 
        
        profiles = self.settings.data.get("mod_profiles", {})
        profile_path = profiles.get(profile_name)
        if not profile_path: return
        
        mod_p_path = os.path.join(profile_path, f"{profile_name}_P")
        if not os.path.isdir(mod_p_path): return
        
        self.stats_thread = threading.Thread(target=self._calculate_stats_thread, args=(mod_p_path, profile_name))
        self.stats_thread.daemon = True
        self.stats_thread.start()

    def _calculate_stats_thread(self, mod_p_path, profile_name):
        audio_files = 0
        subtitle_files = 0
        total_size = 0

        for root, dirs, files in os.walk(mod_p_path):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    if file.endswith(".wem"):
                        audio_files += 1
                    elif file.endswith(".locres"):
                        subtitle_files += 1
                except OSError:
                    continue
        if total_size > 1024 * 1024:
            size_str = f"{total_size / (1024*1024):.2f} MB"
        else:
            size_str = f"{total_size / 1024:.2f} KB"
            
        QtCore.QMetaObject.invokeMethod(self, "update_stats_labels", QtCore.Qt.QueuedConnection,
                                        QtCore.Q_ARG(int, audio_files),
                                        QtCore.Q_ARG(int, subtitle_files),
                                        QtCore.Q_ARG(str, size_str),
                                        QtCore.Q_ARG(str, profile_name))
    
    @QtCore.pyqtSlot(int, int, str, str)
    def update_stats_labels(self, audio_count, subtitle_count, size_str, profile_name):

        current_item = self.profile_list.currentItem()
        if not current_item or current_item.text() != profile_name:
            return

        self.audio_files_label.setText(str(audio_count))
        self.subtitle_files_label.setText(str(subtitle_count))
        self.mod_size_label.setText(size_str)
        
        if self.parent_app.active_profile_name == profile_name:
            modified_count = len(self.parent_app.modified_subtitles)
            self.modified_subs_label.setText(str(modified_count))
        else:
            self.modified_subs_label.setText("N/A (profile not active)")

    def clear_stats_labels(self):
        self.audio_files_label.setText(self.tr("calculating_stats"))
        self.subtitle_files_label.setText(self.tr("calculating_stats"))
        self.mod_size_label.setText(self.tr("calculating_stats"))
        self.modified_subs_label.setText(self.tr("calculating_stats"))
    def edit_profile(self):
        current = self.profile_list.currentItem()
        if not current: return
        
        profile_name = current.text()
        profiles = self.settings.data.get("mod_profiles", {})
        profile_path = profiles.get(profile_name)
        
        existing_data = {
            "path": profile_path,
            "icon": os.path.join(profile_path, "icon.png")
        }
        try:
            with open(os.path.join(profile_path, "profile.json"), 'r', encoding='utf-8') as f:
                existing_data["data"] = json.load(f)
        except:
             existing_data["data"] = {}
        
        dialog = ProfileDialog(self, existing_data=existing_data, translator=self.parent_app.tr)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            profile_data = dialog.get_data()
            
            with open(os.path.join(profile_path, "profile.json"), 'w', encoding='utf-8') as f:
                json.dump(profile_data["info"], f, indent=2)

            icon_dest_path = os.path.join(profile_path, "icon.png")
            if profile_data["icon_path"] and os.path.exists(profile_data["icon_path"]):
                shutil.copy(profile_data["icon_path"], icon_dest_path)
            elif not profile_data["icon_path"] and os.path.exists(icon_dest_path):

                os.remove(icon_dest_path)

            self.display_profile_info(current, None)
            self.profile_changed.emit()

    def create_new_profile(self):
        dialog = ProfileDialog(self, translator=self.parent_app.tr)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            name = data["name"]

            if name in self.settings.data.get("mod_profiles", {}):
                QtWidgets.QMessageBox.warning(self, self.parent_app.tr("error"), self.parent_app.tr("profile_exists_error"))
                return

            profiles_root = os.path.join(self.parent_app.base_path, "Profiles")
            profile_path = os.path.join(profiles_root, name)
            mod_p_path = os.path.join(profile_path, f"{name}_P")
            
            try:
                os.makedirs(profiles_root, exist_ok=True)
                
                os.makedirs(mod_p_path, exist_ok=True)
                if data["icon_path"]:
                    shutil.copy(data["icon_path"], os.path.join(profile_path, "icon.png"))
                
                with open(os.path.join(profile_path, "profile.json"), 'w', encoding='utf-8') as f:
                    json.dump(data["info"], f, indent=2)

                self.settings.data["mod_profiles"][name] = profile_path
                self.settings.save()
                self.populate_profile_list()
                self.profile_changed.emit()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, self.parent_app.tr("error"), self.parent_app.tr("create_profile_error").format(e=e))

    def add_existing_profile(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, self.parent_app.tr("select_existing_profile"))
        if not folder:
            return
        
        profile_name = os.path.basename(folder)
        mod_p_folder = f"{profile_name}_P"
        
        if not os.path.exists(os.path.join(folder, mod_p_folder)):
            QtWidgets.QMessageBox.warning(self, self.parent_app.tr("invalid_profile_folder"), self.parent_app.tr("invalid_profile_folder").format(folder=mod_p_folder))
            return

        if profile_name in self.settings.data.get("mod_profiles", {}):
            QtWidgets.QMessageBox.warning(self, self.parent_app.tr("error"), self.parent_app.tr("profile_already_added"))
            return

        self.settings.data["mod_profiles"][profile_name] = folder
        self.settings.save()
        self.populate_profile_list()
        self.profile_changed.emit()

    def remove_selected_profile(self):
        current = self.profile_list.currentItem()
        if not current:
            return

        name = current.text()
        reply = QtWidgets.QMessageBox.question(self, self.parent_app.tr("remove_profile_title"), self.parent_app.tr("remove_profile_text").format(name=name), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            if self.settings.data["active_profile"] == name:
                self.settings.data["active_profile"] = ""
            
            del self.settings.data["mod_profiles"][name]
            self.settings.save()
            self.populate_profile_list()
            self.profile_changed.emit()

    def activate_profile(self):
        current = self.profile_list.currentItem()
        if not current:
            return
        
        name = current.text()
        self.settings.data["active_profile"] = name
        self.settings.save()
        self.populate_profile_list()
        self.profile_changed.emit()
        QtWidgets.QMessageBox.information(self, self.parent_app.tr("profile_activated_title"), self.parent_app.tr("profile_activated_text").format(name=name))
