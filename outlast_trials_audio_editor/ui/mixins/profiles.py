from ._imports import *

class ProfilesMixin:
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu(self.tr("file_menu"))

        self.save_action = file_menu.addAction(self.tr("save_subtitles"))
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_subtitles_to_file)

        # self.export_action = file_menu.addAction(self.tr("export_subtitles"))
        # self.export_action.triggered.connect(self.export_subtitles)

        # self.import_action = file_menu.addAction(self.tr("import_subtitles"))
        # self.import_action.triggered.connect(self.import_subtitles)

        file_menu.addSeparator()

        self.exit_action = file_menu.addAction(self.tr("exit"))
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu(self.tr("edit_menu"))
        
        self.revert_action = edit_menu.addAction(self.tr("revert_to_original"))
        self.revert_action.setShortcut("Ctrl+R")
        self.revert_action.triggered.connect(self.revert_subtitle)
        
        edit_menu.addSeparator()
        
        
        # Tools menu
        tools_menu = menubar.addMenu(self.tr("tools_menu"))
        
        self.compile_mod_action = tools_menu.addAction(self.tr("compile_mod"))
        self.compile_mod_action.triggered.connect(self.compile_mod)
        
        self.deploy_action = tools_menu.addAction(self.tr("deploy_and_run"))
        self.deploy_action.setShortcut("F5")
        self.deploy_action.triggered.connect(self.deploy_and_run_game)
        tools_menu.addSeparator()

        self.rebuild_bnk_action = tools_menu.addAction(self.tr("rebuild_bnk_index"))
        self.rebuild_bnk_action.setToolTip(self.tr("rebuild_bnk_tooltip"))
        self.rebuild_bnk_action.triggered.connect(self.rebuild_bnk_index)
        tools_menu.addSeparator()
        self.rescan_orphans_action = tools_menu.addAction(self.tr("rescan_orphans_action"))
        self.rescan_orphans_action.setToolTip(self.tr("rescan_orphans_tooltip"))
        self.rescan_orphans_action.triggered.connect(self.perform_blocking_orphan_scan)
        tools_menu.addSeparator()
        self.debug_action = tools_menu.addAction(self.tr("show_debug"))
        self.debug_action.setShortcut("Ctrl+D")
        self.debug_action.triggered.connect(self.show_debug_console)
        
        tools_menu.addSeparator()
        
        self.settings_action = tools_menu.addAction(self.tr("settings"))
        self.settings_action.setShortcut("Ctrl+,")
        self.settings_action.triggered.connect(self.show_settings_dialog)
        
        # Help menu
        help_menu = menubar.addMenu(self.tr("help_menu"))

        # self.documentation_action = help_menu.addAction("📖 Documentation")
        # self.documentation_action.setShortcut("F1")
        # self.documentation_action.triggered.connect(self.show_documentation)

        self.shortcuts_action = help_menu.addAction(self.tr("keyboard_shortcuts"))
        self.shortcuts_action.triggered.connect(self.show_shortcuts)

        help_menu.addSeparator()

        self.check_updates_action = help_menu.addAction(self.tr("check_updates"))
        self.check_updates_action.triggered.connect(self.check_updates)

        self.report_bug_action = help_menu.addAction(self.tr("report_bug"))
        self.report_bug_action.triggered.connect(self.report_bug)

        help_menu.addSeparator()

        self.about_action = help_menu.addAction(self.tr("about"))
        self.about_action.triggered.connect(self.show_about)

    def load_orphans_from_cache_or_scan(self):
        """Loads orphaned files from cache or performs a synchronous scan with a progress dialog."""
        if os.path.exists(self.orphaned_cache_path):
            DEBUG.log(f"Loading orphaned files from cache: {self.orphaned_cache_path}")
            try:
                with open(self.orphaned_cache_path, 'r', encoding='utf-8') as f:
                    self.orphaned_files_cache = json.load(f)
                DEBUG.log(f"Loaded {len(self.orphaned_files_cache)} orphans from cache.")
                self.rebuild_file_list_with_orphans()
            except Exception as e:
                DEBUG.log(f"Error loading orphan cache: {e}. Starting a new scan.", "ERROR")
                self.perform_blocking_orphan_scan()
        else:
            DEBUG.log("Orphan cache not found. Starting initial scan.")
            self.perform_blocking_orphan_scan()

    def perform_blocking_orphan_scan(self):
        """Performs a synchronous scan of the Wems folder with a progress dialog, blocking the UI."""
        self.all_files = [f for f in self.all_files if f.get("Source") != "ScannedFromFileSystem"]
        self.orphaned_files_cache = []
        DEBUG.log("Cleared existing orphan files to perform a full rescan.")

        progress = ProgressDialog(self, self.tr("scan_progress_title"))
        progress.setWindowFlags(progress.windowFlags() | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        progress.setWindowFlags(progress.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        progress.set_progress(0, "Preparing to scan...")
        progress.show()
        QtWidgets.QApplication.processEvents()

        known_ids = {entry.get("Id") for entry in self.load_all_soundbank_files(self.soundbanks_path) if entry.get("Id")}
        
        orphaned_entries = []
        if not os.path.exists(self.wem_root):
            progress.close()
            self.rebuild_file_list_with_orphans()
            return

        all_wem_paths = []
        for root, _, files in os.walk(self.wem_root):
            for file in files:
                if file.lower().endswith('.wem'):
                    all_wem_paths.append(os.path.join(root, file))

        wem_files_to_scan = [
            path for path in all_wem_paths 
            if os.path.splitext(os.path.basename(path))[0] not in known_ids
        ]
        
        total_files = len(wem_files_to_scan)
        if total_files == 0:
            DEBUG.log("No new orphan files found.")
            progress.close()
            self.rebuild_file_list_with_orphans() 
            self.status_bar.showMessage("No new audio files found during scan.", 5000)
            return
            
        progress.set_progress(5, f"Scanning {total_files} new files...")
        QtWidgets.QApplication.processEvents()

        for i, full_path in enumerate(wem_files_to_scan):
            if i % 20 == 0:
                QtWidgets.QApplication.processEvents()
                progress.set_progress(int((i / total_files) * 100), f"Scanning {os.path.basename(full_path)}")

            file_id = os.path.splitext(os.path.basename(full_path))[0]
      
            rel_path = os.path.relpath(os.path.dirname(full_path), self.wem_root)
            parts = rel_path.split(os.sep)
            
            lang = "SFX"
            if rel_path == '.' or rel_path == "SFX":
                lang = "SFX"
            elif parts[0] == "Media":
                if len(parts) > 1:
                    lang = parts[1]
                else:
                    lang = "SFX"
            else:
                lang = rel_path

            short_name = f"{file_id}.wav"
            try:
                analyzer = WEMAnalyzer(full_path)
                if analyzer.analyze():
                    markers = analyzer.get_markers_info()
                    if markers and markers[0]['label']:
                        short_name = f"{markers[0]['label']}.wav"
            except Exception:
                pass

            new_entry = {
                "Id": file_id, "Language": lang, "ShortName": short_name, 
                "Path": os.path.basename(full_path), "Source": "ScannedFromFileSystem"
            }
            orphaned_entries.append(new_entry)

        progress.set_progress(100, "Finalizing...")
        
        self.orphaned_files_cache = orphaned_entries
        try:
            with open(self.orphaned_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.orphaned_files_cache, f, indent=2)
            DEBUG.log(f"Saved {len(orphaned_entries)} orphaned files to cache.")
        except Exception as e:
            DEBUG.log(f"Failed to save orphan cache: {e}", "ERROR")

        progress.close()
        self.rebuild_file_list_with_orphans()
        self.status_bar.showMessage(f"Rescan complete. Found and cached {len(orphaned_entries)} additional audio files.", 5000)

    def start_orphan_scan(self, force=False):
        """Starts the background thread to scan for orphaned WEM files."""
        if self.scanner_thread and self.scanner_thread.isRunning():
            DEBUG.log("Scan is already in progress.", "WARNING")
            if not force:
                return
            else:
                self.scanner_thread.stop()
                self.scanner_thread.wait()

        is_first_scan = not os.path.exists(self.orphaned_cache_path)
        if is_first_scan or force:
            if self.scan_message_box:
                self.scan_message_box.close()

            title = "Initial File Scan" if is_first_scan else "Rescanning Files"
            message = ("The app is scanning your 'Wems' folder to find all available audio files.\n\n"
                       "This may take a moment. You can continue using the main window while this is in progress.")

            self.scan_message_box = QtWidgets.QMessageBox(self)
            self.scan_message_box.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
            self.scan_message_box.setIcon(QtWidgets.QMessageBox.Information)
            self.scan_message_box.setWindowTitle(title)
            self.scan_message_box.setText("<b>Scanning in Background...</b>")
            self.scan_message_box.setInformativeText(message)
            
            hide_button = self.scan_message_box.addButton("Hide", QtWidgets.QMessageBox.ActionRole)
            hide_button.clicked.connect(self.hide_scan_notification)
            
            self.scan_message_box.setModal(False)
            self.scan_message_box.show()

        if force:
            self.all_files = [f for f in self.all_files if f.get("Source") != "ScannedFromFileSystem"]
            self.entries_by_lang = self.group_by_language()
            for lang in self.tab_widgets.keys():
                self.populate_tree(lang)
            self.status_bar.showMessage("Forced rescan started... You can continue working.", 0)
        else:
            self.status_bar.showMessage("Scanning for additional audio files... You can continue working.", 0)

        known_ids = {entry.get("Id") for entry in self.load_all_soundbank_files(self.soundbanks_path) if entry.get("Id")}
        self.scanner_thread = WemScannerThread(self.wem_root, known_ids, self)
        self.scanner_thread.scan_finished.connect(self._on_scan_finished)
        self.scanner_thread.start()

    def hide_scan_notification(self):
        """Safely closes the scanning notification message box if it exists."""
        if self.scan_message_box:
            self.scan_message_box.close()
            self.scan_message_box = None

    def rebuild_file_list_with_orphans(self):
  
        base_files = self.load_all_soundbank_files(self.soundbanks_path)
        self._build_wem_index()

        filtered_base_files = []
        for entry in base_files:
            file_id = entry.get("Id")
      
            if file_id and file_id in self.wem_index:
                filtered_base_files.append(entry)
        
        DEBUG.log(f"Filtered SoundbanksInfo: {len(filtered_base_files)} entries have a physical .wem file (out of {len(base_files)} loaded from JSON).")

        show_orphans = self.settings.data.get("show_orphaned_files", False)
        
       
        if not filtered_base_files and self.orphaned_files_cache:
            DEBUG.log("Main database matched 0 files. Forcing display of scanned orphans.")
            self.all_files = self.orphaned_files_cache
        elif show_orphans and self.orphaned_files_cache:
         
            existing_ids = {entry["Id"] for entry in filtered_base_files}
            unique_orphans = [o for o in self.orphaned_files_cache if o["Id"] not in existing_ids]
            
            DEBUG.log(f"Adding {len(unique_orphans)} unique orphans to the main list.")
            self.all_files = filtered_base_files + unique_orphans
        else:
            self.all_files = filtered_base_files

        DEBUG.log(f"Total files to display: {len(self.all_files)}")

        self.entries_by_lang = self.group_by_language()
        
        active_tabs_to_update = list(self.populated_tabs) 
        for lang in active_tabs_to_update:
             if lang in self.tab_widgets:
                self.populate_tree(lang)
        
        for lang, widgets in self.tab_widgets.items():
            try:
                if widgets["tree"].parent() and widgets["tree"].parent().parent():
                    current_tab_index = self.tabs.indexOf(widgets["tree"].parent().parent())
                    if current_tab_index != -1:
                        total_count = len(self.entries_by_lang.get(lang, []))
                        self.tabs.setTabText(current_tab_index, f"{lang} ({total_count})")
            except:
                pass
        
        self.update_status()

    def show_debug_console(self):
        if self.debug_window is None:
            self.debug_window = DebugWindow(self)
        self.debug_window.show()
        self.debug_window.raise_()

    def get_mods_root_path(self, prompt_if_missing=False):

        mods_root = self.settings.data.get("mods_root_path", "")
        if (not mods_root or not os.path.isdir(mods_root)) and prompt_if_missing:
            QtWidgets.QMessageBox.information(self, "Setup Mods Folder", "Please select a folder where you want to store your mod profiles.")
            folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select a Folder to Store Your Mods")
            if folder:
                self.settings.data["mods_root_path"] = folder
                self.settings.save()
                return folder
            else:
                return None
        return mods_root

    def migrate_or_load_profiles(self):
        mods_root = self.get_mods_root_path()
        legacy_mod_p_path = os.path.join(self.base_path, "MOD_P")

        if not mods_root and os.path.exists(legacy_mod_p_path):
            DEBUG.log("Legacy MOD_P folder found. Initiating migration process.")
            self.handle_legacy_mod_p_migration(legacy_mod_p_path)
        
        self.load_profiles()

    def load_profiles(self):
        self.profiles = {}
        mods_root = self.get_mods_root_path()
        if not mods_root:
            self.update_profile_ui()
            self.set_active_profile(None)
            return

        for profile_name in os.listdir(mods_root):
            profile_path = os.path.join(mods_root, profile_name)
            profile_json_path = os.path.join(profile_path, "profile.json")
            mod_p_path = os.path.join(profile_path, f"{profile_name}_P")
            if os.path.isdir(profile_path) and os.path.exists(profile_json_path) and os.path.isdir(mod_p_path):
                try:
                    with open(profile_json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.profiles[profile_name] = {
                        "path": profile_path,
                        "mod_p_path": mod_p_path,
                        "icon": os.path.join(profile_path, "icon.png"),
                        "data": data
                    }
                except Exception as e:
                    DEBUG.log(f"Failed to load profile '{profile_name}': {e}", "WARNING")

        last_active = self.settings.data.get("active_profile")
        if last_active and last_active in self.profiles:
            self.set_active_profile(last_active)
        elif self.profiles:
            first_profile = sorted(self.profiles.keys())[0]
            self.set_active_profile(first_profile)
        else:

            self.set_active_profile(None)

        self.update_profile_ui()

    def show_profile_manager(self):
        dialog = ProfileManagerDialog(self)
        dialog.profile_changed.connect(self.on_profile_system_changed)
        dialog.exec_()

    def on_profile_system_changed(self):

        self.load_profiles_from_settings()
        self.load_subtitles()

    def load_profiles_from_settings(self):
        profiles = self.settings.data.get("mod_profiles", {})
        active_name = self.settings.data.get("active_profile", "")

        if active_name and active_name in profiles:
            profile_path = profiles[active_name]
            mod_p_path = os.path.join(profile_path, f"{active_name}_P")
            
            if os.path.isdir(mod_p_path):
                self.active_profile_name = active_name
                self.mod_p_path = mod_p_path
                self.setWindowTitle(f"{self.tr('app_title')} - [{active_name}]")
                DEBUG.log(f"Loaded active profile: {active_name}")
            else:
                self.reset_active_profile()
        else:
            self.reset_active_profile()

        self.load_subtitles()

        current_lang = self.get_current_language()
        if current_lang:
            self.populate_tree(current_lang)

    def reset_active_profile(self):
        self.active_profile_name = None
        self.mod_p_path = None
        self.settings.data["active_profile"] = ""
        self.settings.save()
        self.setWindowTitle(self.tr("app_title"))
        DEBUG.log("Active profile was invalid or not set. Resetting.")

    def update_profile_ui(self):
        
        if not hasattr(self, 'profile_combo'):
            if self.active_profile_name:
                self.setWindowTitle(f"{self.tr('app_title')} - [{self.active_profile_name}]")
            else:
                self.setWindowTitle(self.tr("app_title"))
            return

        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        
        if not self.profiles:
            self.profile_combo.addItem("No Profiles Found")
            self.profile_combo.setEnabled(False)
            self.profile_combo.blockSignals(False)
            return

        self.profile_combo.setEnabled(True)
        for profile_name in sorted(self.profiles.keys()):
            icon_path = self.profiles[profile_name]["icon"]
            icon = QtGui.QIcon(icon_path) if os.path.exists(icon_path) else QtGui.QIcon()
            self.profile_combo.addItem(icon, profile_name)
        
        if self.active_profile_name:
            self.profile_combo.setCurrentText(self.active_profile_name)

        self.profile_combo.blockSignals(False)

    def set_active_profile(self, profile_name):
        if profile_name and profile_name in self.profiles:
            self.active_profile_name = profile_name
            self.mod_p_path = self.profiles[profile_name]["mod_p_path"]
            self.settings.data["active_profile"] = profile_name
            self.setWindowTitle(f"{self.tr('app_title')} - [{profile_name}]")
            DEBUG.log(f"Switched to profile: {profile_name}. MOD_P path: {self.mod_p_path}")
        else:
            self.active_profile_name = None
            self.mod_p_path = None
            self.settings.data["active_profile"] = ""
            self.setWindowTitle(self.tr("app_title"))
            DEBUG.log("No active profile.")
        
        self.settings.save()
        current_lang = self.get_current_language()
        if current_lang and current_lang in self.tab_widgets:
            if current_lang not in self.populated_tabs:
                 self.populated_tabs.add(current_lang)
            self.populate_tree(current_lang)

    def switch_profile_by_index(self, index):
        profile_name = self.profile_combo.itemText(index)
        if profile_name in self.profiles:
            self.set_active_profile(profile_name)

    def create_new_profile(self):
        mods_root = self.get_mods_root_path(prompt_if_missing=True)
        if not mods_root:
            return

        dialog = ProfileDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            profile_data = dialog.get_data()
            profile_name = profile_data["name"]
            
            if profile_name in self.profiles:
                QtWidgets.QMessageBox.warning(self, "Error", "A profile with this name already exists.")
                return

            profile_path = os.path.join(mods_root, profile_name)
            mod_p_path = os.path.join(profile_path, f"{profile_name}_P")
            os.makedirs(mod_p_path, exist_ok=True)
            
            if profile_data["icon_path"] and os.path.exists(profile_data["icon_path"]):
                shutil.copy(profile_data["icon_path"], os.path.join(profile_path, "icon.png"))

            profile_json_path = os.path.join(profile_path, "profile.json")
            with open(profile_json_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data["info"], f, indent=2)

            self.load_profiles()
            self.set_active_profile(profile_name) 
            self.update_profile_ui()

    def edit_current_profile(self):
        if not self.active_profile_name or not self.mod_p_path:
            QtWidgets.QMessageBox.warning(self, "No Profile Selected", "Please select or create a profile to edit.")
            return

        current_profile = self.profiles[self.active_profile_name]
        dialog = ProfileDialog(self, existing_data=current_profile)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            profile_data = dialog.get_data()
            
            profile_path = current_profile["path"]
            profile_json_path = os.path.join(profile_path, "profile.json")
            with open(profile_json_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data["info"], f, indent=2)

            icon_dest_path = os.path.join(profile_path, "icon.png")
            if profile_data["icon_path"]:
                 if not os.path.exists(profile_data["icon_path"]):
                     if os.path.exists(icon_dest_path):
                         os.remove(icon_dest_path)
                 else:
                     shutil.copy(profile_data["icon_path"], icon_dest_path)
            
            self.load_profiles()
