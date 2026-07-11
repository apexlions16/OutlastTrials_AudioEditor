from .mixins._imports import *
from .mixins import (
    ResourceBanksMixin,
    CoreMixin,
    ModAudioMixin,
    LocalizationMixin,
    AudioLibraryMixin,
    ProfilesMixin,
    AudioActionsMixin,
    AppearanceMixin,
    ConversionMixin,
    CleanupMixin,
    LanguageTabsMixin,
    HelpAboutMixin,
)

class WemSubtitleApp(ResourceBanksMixin, CoreMixin, ModAudioMixin, LocalizationMixin, AudioLibraryMixin, ProfilesMixin, AudioActionsMixin, AppearanceMixin, ConversionMixin, CleanupMixin, LanguageTabsMixin, HelpAboutMixin, QtWidgets.QMainWindow):
    log_signal = QtCore.pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        DEBUG.log("=== OutlastTrials AudioEditor Starting ===")
        if getattr(sys, 'frozen', False):

            self.base_path = os.path.dirname(sys.executable)
        else:

            self.base_path = str(APP_ROOT)
        DEBUG.setup_logging(self.base_path)
        self.wem_index = None
        self.settings = AppSettings()
        self.translations = TRANSLATIONS
        self.current_lang = self.settings.data["ui_language"]
        
        self.setWindowTitle(self.tr("app_title"))
        icon_path = os.path.join(self.base_path, "data", "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
            DEBUG.log(f"Application icon not found at {icon_path}, using default.", "WARNING")
        
        
        
        DEBUG.log(f"Base path: {self.base_path}")
        
        self.data_path = os.path.join(self.base_path, "data")
        self.libs_path = os.path.join(self.base_path, "libs")   
        
        self.unreal_locres_path = os.path.join(self.data_path, "UnrealLocres.exe")
        self.repak_path = os.path.join(self.data_path, "repak.exe")
        self.vgmstream_path = os.path.join(self.data_path, "vgmstream", "vgmstream-cli.exe")
        
        
        self.wem_root = os.path.join(self.base_path, "Wems")
        json_path = os.path.join(self.wem_root, "SFX", "SoundbanksInfo.json")
        xml_path = os.path.join(self.wem_root, "SFX", "SoundbanksInfo.xml")
        if os.path.exists(json_path):
            self.soundbanks_path = json_path
        elif os.path.exists(xml_path):
            self.soundbanks_path = xml_path
        else:
            self.soundbanks_path = json_path 
        self.active_profile_name = None
        self.mod_p_path = None
        self.orphaned_cache_path = os.path.join(self.base_path, "orphaned_files_cache.json")
        self.check_required_files()
        self.orphaned_files_cache = []
        DEBUG.log(f"Paths configured:")
        DEBUG.log(f"  data_path: {self.data_path}")
        DEBUG.log(f"  unreal_locres_path: {self.unreal_locres_path}")
        DEBUG.log(f"  repak_path: {self.repak_path}")
        DEBUG.log(f"  vgmstream_path: {self.vgmstream_path}")

        self.locres_manager = UnrealLocresManager(self.unreal_locres_path)
        self.subtitles = {}
        self.original_subtitles = {}
        self.all_subtitle_files = {}
        self.key_to_file_map = {}
        self.all_files = self.load_all_soundbank_files(self.soundbanks_path)
        self.entries_by_lang = self.group_by_language()
        self.show_orphans_checkbox = QtWidgets.QCheckBox("Show Scanned Files")
        self.show_orphans_checkbox.setToolTip("Show/hide audio files found by scanning the 'Wems' folder that are not in the main database.")
        self.show_orphans_checkbox.setChecked(self.settings.data.get("show_orphaned_files", False))
        self.show_orphans_checkbox.stateChanged.connect(self.on_show_orphans_toggled)
        self.audio_player = AudioPlayer()
        self.temp_wav = None
        self.currently_playing_item = None
        self.is_playing_mod = False
        self.original_duration = 0
        self.mod_duration = 0
        self.original_size = 0
        self.mod_size = 0
        self.populated_tabs = set()
        self.modified_subtitles = set()
        self.dirty_subtitle_files = set()
        self.marked_items = {}
        if "marked_items" in self.settings.data:
            for key, data in self.settings.data["marked_items"].items():
                self.marked_items[key] = {
                    'color': QtGui.QColor(data['color']) if 'color' in data else None,
                    'tag': data.get('tag', '')
                }
        self.current_file_duration = 0

        self.debug_window = None
        self.updater_thread = None
        self.first_show_check_done = False
        self.auto_save_timer = QtCore.QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_subtitles)
        self.auto_save_enabled = False  
        self.bnk_cache_orig = {}
        self.bnk_cache_mod = {}
        self.bnk_loader_thread = None
        self.first_show_check_done = False
        self.current_bnk_request_id = 0
        self.search_timer = QtCore.QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(400) 
        self.search_timer.timeout.connect(self.perform_delayed_search)
        self.tree_loader_timer = QtCore.QTimer()
        self.tree_loader_timer.setInterval(0) 
        self.tree_loader_timer.timeout.connect(self._process_tree_batch)
        self.tree_loader_generator = None
        self.current_loading_lang = None
        self.create_ui()
        # QtCore.QTimer.singleShot(100, self.load_orphans_from_cache_or_scan) 
        self.apply_settings()
        self.restore_window_state()


        self.update_auto_save_timer()
        
        self.log_signal.connect(self.append_to_log_widget)
        DEBUG.log("=== OutlastTrials AudioEditor Started Successfully ===")

    def showEvent(self, event):
        super().showEvent(event)
        
        if not self.first_show_check_done:
            self.first_show_check_done = True
            DEBUG.log("Application window shown for the first time. Scheduling initial checks.")
            
            def run_all_startup_checks():
    
                if self.check_initial_resources():
                    return
                
                loose_files_found = self.check_for_loose_wems()
            
                if not loose_files_found:
                    self.check_soundbanks_info()

                QtCore.QTimer.singleShot(1500, self.check_updates_on_startup)

            QtCore.QTimer.singleShot(100, run_all_startup_checks)

    @QtCore.pyqtSlot(list)
    def _show_bnk_verification_report(self, mismatches):

        if not mismatches:
            QtWidgets.QMessageBox.information(self, "Verification Complete", "All modified audio files are consistent with their BNK entries. No issues found!")
            return

        report_text = f"Found {len(mismatches)} issues in your mod.\n\n"
        report_text += "These problems can cause sounds to not play correctly in the game.\n\n"
        report_text += "Do you want to automatically fix these entries?"

        dialog = QtWidgets.QMessageBox(self)
        dialog.setWindowTitle("Mod Integrity Issues Found")
        dialog.setText(report_text)
        
        detailed_report = ""
        for item in mismatches:
            if item['type'] == 'Size Mismatch':
                bnk_name = os.path.basename(item['bnk_path'])
                detailed_report += (
                    f"Type: {item['type']} in {bnk_name}\n"
                    f"  Sound: {item['short_name']} (ID: {item['source_id']})\n"
                    f"  - BNK Size: {item['bnk_size']} bytes\n"
                    f"  - WEM Size: {item['wem_size']} bytes\n\n"
                )
            elif item['type'] == 'BNK Entry Missing':
                 detailed_report += (
                    f"Type: {item['type']}\n"
                    f"  Sound: {item['short_name']} (ID: {item['source_id']})\n"
                    f"  - A .wem file exists, but no corresponding entry was found in any modified .bnk file.\n\n"
                )
        dialog.setDetailedText(detailed_report)
        
        fix_btn = dialog.addButton("Fix All", QtWidgets.QMessageBox.AcceptRole)
        cancel_btn = dialog.addButton(QtWidgets.QMessageBox.Cancel)
        dialog.setDefaultButton(fix_btn)
        
        self.show_dialog(dialog)
        
        if dialog.clickedButton() == fix_btn:
            self.fix_bnk_mismatches(mismatches)

    @QtCore.pyqtSlot(str)
    def _show_bnk_verification_error(self, error_message):

        QtWidgets.QMessageBox.critical(self, "Verification Error", f"An error occurred during verification:\n\n{error_message}")

    @QtCore.pyqtSlot(int, str, str)    
    def show_message_box(self, icon, title, text, informative_text="", detailed_text="", buttons=QtWidgets.QMessageBox.Ok):
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        if informative_text:
            msg.setInformativeText(informative_text)
        if detailed_text:
            msg.setDetailedText(detailed_text)
        msg.setStandardButtons(buttons)
        msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint) 
        msg.show() 
        msg.raise_() 
        msg.activateWindow() 
        return msg.exec_()

    @QtCore.pyqtSlot(dict)
    def _add_orphaned_entry(self, entry):

        self.all_files.append(entry)
        lang = entry.get("Language", "SFX")
        self.entries_by_lang.setdefault(lang, []).append(entry)

        if lang in self.tab_widgets:
            widgets = self.tab_widgets[lang]
            tree = widgets["tree"]
            
            scanned_group_name = "Scanned From Filesystem"
            items = tree.findItems(scanned_group_name, QtCore.Qt.MatchStartsWith, 0)
            group_item = items[0] if items else None
            
            if not group_item:
                group_item = QtWidgets.QTreeWidgetItem(tree, [scanned_group_name, "", "", "", ""])
                group_item.setExpanded(True)
            
            self.add_tree_item(group_item, entry, lang)
            group_item.setText(0, f"{scanned_group_name} ({group_item.childCount()})")
            
            current_tab_index = self.tabs.indexOf(widgets["tree"].parent().parent())
            if current_tab_index != -1:
                total_count = len(self.entries_by_lang.get(lang, []))
                self.tabs.setTabText(current_tab_index, f"{lang} ({total_count})")

    @QtCore.pyqtSlot(str)
    def populate_tree(self, lang):
        DEBUG.log(f"Populating tree for language: {lang}")
        
        if lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[lang]
        tree = widgets["tree"]
        
        if self.tree_loader_timer.isActive():
            self.tree_loader_timer.stop()
            self.tree_loader_generator = None
   
            if self.current_loading_lang and self.current_loading_lang in self.tab_widgets:
                self.tab_widgets[self.current_loading_lang]["tree"].setUpdatesEnabled(True)

        selected_keys = []
        try:
            for item in tree.selectedItems():
                if item.childCount() == 0:
                    entry = item.data(0, QtCore.Qt.UserRole)
                    if entry:
                        shortname = entry.get("ShortName", "")
                        key = os.path.splitext(shortname)[0]
                        selected_keys.append(key)
        except RuntimeError:
            pass
        
        tree.clear()
        
        filter_text = widgets["filter_combo"].currentText()
        filter_type = widgets["filter_combo"].currentIndex()
        sort_type = widgets["sort_combo"].currentIndex() 
        search_text = self.global_search.text().lower()
        
        filtered_entries = []
        source_entries = self.entries_by_lang.get(lang, [])
        
        search_terms = []
        if search_text:
           
            search_terms = [term.strip() for term in search_text.split() if term.strip()]
        
        if filter_text.startswith("With Tag: "):
            selected_tag = filter_text.split(": ", 1)[1]
            for entry in source_entries:
                key = os.path.splitext(entry.get("ShortName", ""))[0]
                
                if self.marked_items.get(key, {}).get('tag') != selected_tag:
                    continue
                    
                if search_terms:
                    
                    content_to_search = f"{entry.get('Id', '')} {entry.get('ShortName', '')} {self.subtitles.get(key, '')}".lower()
                    
                    if not all(term in content_to_search for term in search_terms):
                        continue
                        
                filtered_entries.append({'_orig': entry, 'has_mod_audio': False})
        else:
            for entry in source_entries:
                key = os.path.splitext(entry.get("ShortName", ""))[0]
                subtitle = self.subtitles.get(key, "")
                
                has_mod_audio = False
                if filter_type == 4: 
                    mod_path = self.get_mod_path(entry.get("Id", ""), lang)
                    has_mod_audio = os.path.exists(mod_path) if mod_path else False
                
                if filter_type == 1 and not subtitle: continue          # With Subtitles
                elif filter_type == 2 and subtitle: continue            # Without Subtitles
                elif filter_type == 3 and key not in self.modified_subtitles: continue # Modified
                elif filter_type == 4 and not has_mod_audio: continue   # Modded (Audio)
                
                if search_terms:
                    content_to_search = f"{entry.get('Id', '')} {entry.get('ShortName', '')} {subtitle}".lower()
                    
                    match = True
                    for term in search_terms:
                        if term not in content_to_search:
                            match = False
                            break
                    if not match:
                        continue
                
                if filter_type != 4:
                     mod_path = self.get_mod_path(entry.get("Id", ""), lang)
                     has_mod_audio = os.path.exists(mod_path) if mod_path else False

                entry_wrapper = {'_orig': entry, 'has_mod_audio': has_mod_audio}
                filtered_entries.append(entry_wrapper)

        if sort_type == 4: # Recent First
            mod_times_cache = {}
            for wrapper in filtered_entries:
                entry = wrapper['_orig']
                file_id = entry.get("Id", "")
                mod_wem_path = self.get_mod_path(file_id, lang)
                if os.path.exists(mod_wem_path):
                    try: mod_times_cache[file_id] = os.path.getmtime(mod_wem_path)
                    except OSError: mod_times_cache[file_id] = 0
                else: mod_times_cache[file_id] = 0
            
            filtered_entries.sort(key=lambda x: mod_times_cache.get(x['_orig'].get("Id", ""), 0), reverse=True)
        elif sort_type == 0: filtered_entries.sort(key=lambda x: x['_orig'].get("ShortName", "").lower())
        elif sort_type == 1: filtered_entries.sort(key=lambda x: x['_orig'].get("ShortName", "").lower(), reverse=True)
        elif sort_type == 2: filtered_entries.sort(key=lambda x: int(x['_orig'].get("Id", "0")))
        elif sort_type == 3: filtered_entries.sort(key=lambda x: int(x['_orig'].get("Id", "0")), reverse=True)

        subtitle_count = sum(1 for w in filtered_entries if self.subtitles.get(os.path.splitext(w['_orig'].get("ShortName", ""))[0], ""))
        total_lang_entries = len(source_entries)
        stats_text = self.tr("stats_label_text").format(
            filtered_count=len(filtered_entries),
            total_count=total_lang_entries,
            subtitle_count=subtitle_count
        )
        widgets["stats_label"].setText(stats_text)

        self.current_loading_lang = lang
        is_flat_view = bool(search_text or sort_type == 4)
        
        self.tree_loader_generator = self._tree_populate_generator(
            tree, filtered_entries, lang, is_flat_view, selected_keys
        )
        
        self.tree_loader_timer.start()

    @QtCore.pyqtSlot(bool, str, str, str)
    def _play_converted(self, ok, wav_path, error, lang):
        if ok:
            self.temp_wav = wav_path
            self.audio_player.play(wav_path)
            source_type = "MOD" if self.is_playing_mod else "Original"
            self.status_bar.showMessage(f"Playing {source_type} audio...", 2000)
            

            if lang in self.tab_widgets:
                widgets = self.tab_widgets[lang]
                
                try:
                    self.audio_player.positionChanged.disconnect()
                    self.audio_player.durationChanged.disconnect()
                except:
                    pass
                    
                self.audio_player.positionChanged.connect(
                    lambda pos: self.update_audio_position(pos, widgets))
                self.audio_player.durationChanged.connect(
                    lambda dur: self.update_audio_duration(dur, widgets))
        else:
            self.status_bar.showMessage(f"Conversion failed: {error}", 3000)

    @QtCore.pyqtSlot(bool, str, str, object)
    def _on_single_export_finished(self, ok, save_path, error_message, progress_dialog):
        progress_dialog.close() 

        if ok:
            self.status_bar.showMessage(f"Saved: {save_path}", 3000)
            self.show_message_box(
                QtWidgets.QMessageBox.Information,
                self.tr("export_complete"),
                f"File successfully exported to:\n{save_path}"
            )
        else:
            self.show_message_box(
                QtWidgets.QMessageBox.Warning,
                "Error",
                f"Conversion failed: {error_message}"
            )

    @QtCore.pyqtSlot(list)
    def _on_scan_finished(self, orphaned_files):
        """Handles the completion of the background WEM scan."""
        self.hide_scan_notification()

        count = len(orphaned_files)
        DEBUG.log(f"Orphan scan finished. Found {count} additional files.")
        
        self.orphaned_files_cache = orphaned_files
        try:
            with open(self.orphaned_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.orphaned_files_cache, f, indent=2)
            DEBUG.log(f"Saved {count} orphaned files to cache.")
        except Exception as e:
            DEBUG.log(f"Failed to save orphan cache: {e}", "ERROR")

        self.rebuild_file_list_with_orphans()
        
        self.status_bar.showMessage(f"Scan complete. Found and cached {count} additional audio files.", 5000)

    @QtCore.pyqtSlot(str, str)
    def _quick_load_complete(self, lang, shortname):
        self.populate_tree(lang)
        self.status_bar.showMessage(f"Successfully imported custom audio for {shortname}", 3000)
        QtWidgets.QMessageBox.information(
            self, "Success",
            f"Custom audio imported successfully!\n\nFile: {shortname}\n\nThe mod audio is now in MOD_P"
        )

    @QtCore.pyqtSlot(str)
    def _quick_load_error(self, error):
        QtWidgets.QMessageBox.critical(
            self, "Import Error",
            f"Failed to import custom audio:\n\n{error}"
        )

    @QtCore.pyqtSlot(str, result=str)
    def _ask_overwrite(self, shortname):
        reply_box = QtWidgets.QMessageBox(self)
        reply_box.setWindowTitle("File Exists")
        reply_box.setText(f"The file '{shortname}' already exists in the destination folder.")
        reply_box.setInformativeText("Do you want to overwrite it?")
        yes_btn = reply_box.addButton("Yes", QtWidgets.QMessageBox.YesRole)
        no_btn = reply_box.addButton("No", QtWidgets.QMessageBox.NoRole)
        yes_all_btn = reply_box.addButton("Yes to All", QtWidgets.QMessageBox.YesRole)
        no_all_btn = reply_box.addButton("No to All", QtWidgets.QMessageBox.NoRole)
        
        self.show_dialog(reply_box)
        clicked = reply_box.clickedButton()

        if clicked == yes_btn: return "Yes"
        if clicked == no_btn: return "No"
        if clicked == yes_all_btn: return "Yes to All"
        if clicked == no_all_btn: return "No to All"
        return "No"

    @QtCore.pyqtSlot(result=bool)
    def _ask_convert_old_mod_structure(self):
        """Asks the user if they want to convert old mod structure to new Media/ format."""
        title = self.translations.get(self.current_lang, {}).get(
            "outdated_mod_structure_title", "Outdated Mod Structure"
        )
        
        msg = self.translations.get(self.current_lang, {}).get(
            "outdated_mod_structure_msg", 
            "The mod you are importing uses the old file structure (pre-update).\n\n"
            "The game now requires audio files to be in a 'Media' subfolder.\n"
            "Do you want to automatically reorganize the files to the new format?"
        )

        reply = QtWidgets.QMessageBox.question(
            self,
            title,
            msg,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        return reply == QtWidgets.QMessageBox.Yes

    @QtCore.pyqtSlot(object, int, list)
    def _on_batch_export_finished(self, progress, successful_count, errors):
        progress.close()
        
        self.show_message_box(
            QtWidgets.QMessageBox.Information,
            self.tr("export_complete"),
            self.tr("export_results").format(
                successful=successful_count,
                errors=len(errors)
            ),
            informative_text="\n".join(errors) if errors else ""
        )
        
        if successful_count > 0:
            self.status_bar.showMessage(f"Exported {successful_count} files successfully", 3000)

    @QtCore.pyqtSlot(str, str)
    def append_to_log_widget(self, message, level):

        if hasattr(self, 'conversion_logs'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] {message}"
            color_map = {
                "INFO": "#d4d4d4" if self.settings.data["theme"] == "dark" else "#1e1e1e",
                "WARNING": "#FFC107",
                "ERROR": "#F44336",
                "SUCCESS": "#4CAF50"
            }
            color = color_map.get(level.upper(), color_map["INFO"])
            html_entry = f"<span style='color:{color};'>{log_entry}</span>"
            self.conversion_logs.append(html_entry)
            scrollbar = self.conversion_logs.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    @QtCore.pyqtSlot(str, result=str)
    def _ask_for_update(self, filename):

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("File Already Added")
        msg.setText(f"File '{filename}' is already in the conversion list.\n\nDo you want to update its settings?")
        update_btn = msg.addButton("Update", QtWidgets.QMessageBox.YesRole)
        skip_btn = msg.addButton("Skip", QtWidgets.QMessageBox.NoRole)
        msg.setDefaultButton(skip_btn)
        self.show_dialog(msg)
        return "Update" if msg.clickedButton() == update_btn else "Skip"

    @QtCore.pyqtSlot(str, str, str, bool, result=str)
    def _ask_for_replace(self, file_id, existing_name, new_name, auto_mode):

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Duplicate Target WEM")
        msg.setText(f"Target WEM '{file_id}.wem' is already assigned to:\n\nCurrent: {existing_name}\nNew: {new_name}\n\nDo you want to replace it?")
        replace_btn = msg.addButton("Replace", QtWidgets.QMessageBox.YesRole)
        skip_btn = msg.addButton("Skip", QtWidgets.QMessageBox.NoRole)
        if auto_mode:
            msg.addButton("Replace All", QtWidgets.QMessageBox.YesRole)
            msg.addButton("Skip All", QtWidgets.QMessageBox.NoRole)
        msg.setDefaultButton(skip_btn)
        self.show_dialog(msg)
        return msg.clickedButton().text()

    @QtCore.pyqtSlot(str, str, str, bool)
    def _show_update_available(self, latest_version, download_url, release_notes, silent=False):
        """Show update available dialog"""
        self.statusBar().showMessage("Update available!")
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Update Available")
        msg.setIcon(QtWidgets.QMessageBox.Information)
        
        text = f"""New version available: v{latest_version}
    Current version: {current_version}

    Release Notes:
    {release_notes[:300]}{'...' if len(release_notes) > 300 else ''}

    Do you want to download the update?"""
        
        msg.setText(text)
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        
        if msg.exec_() == QtWidgets.QMessageBox.Yes:
            import webbrowser
            webbrowser.open(download_url)

    @QtCore.pyqtSlot()
    def _show_up_to_date(self):
        """Show up to date message"""
        self.statusBar().showMessage("You are running the latest version.")
        
        QtWidgets.QMessageBox.information(
            self, "Check for Updates",
            "You are running OutlastTrials AudioEditor " + current_version + "\n\n"
            "This is the latest version!"
        )

    @QtCore.pyqtSlot(str)
    def _show_network_error(self, error):
        """Show network error"""
        self.statusBar().showMessage("Failed to check for updates.")
        
        QtWidgets.QMessageBox.warning(
            self, "Update Check Failed",
            f"Failed to check for updates.\n\n"
            f"Please check your internet connection and try again.\n\n"
            f"Error: {error}\n\n"
            f"You can manually check for updates at:\n"
            f"https://github.com/Bezna/OutlastTrials_AudioEditor"
        )

    @QtCore.pyqtSlot(str)
    def _show_error(self, error):
        """Show general error"""
        self.statusBar().showMessage("Error checking for updates.")
        
        QtWidgets.QMessageBox.critical(
            self, "Error",
            f"An error occurred while checking for updates:\n\n{error}"
        )

    @QtCore.pyqtSlot(str)
    def _update_status_silent(self, message):
        """Silently update status bar"""
        if message:
            self.statusBar().showMessage(message)
        else:
            self.statusBar().clearMessage()

    def closeEvent(self, event):
        DEBUG.log("=== Application Closing ===")

        if hasattr(self, 'updater_thread') and self.updater_thread and self.updater_thread.isRunning():
            reply = QtWidgets.QMessageBox.question(
                self, 
                self.tr("update_in_progress_title"),
                self.tr("confirm_exit_during_update_message"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.No:
                event.ignore()
                return
            else:
                self.updater_thread.cancel()
                self.updater_thread.wait(5000)
                DEBUG.log("Update process cancelled due to application exit.")
        
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            DEBUG.log("Auto-save timer stopped on close")
        
        self.settings.data["window_geometry"] = self.saveGeometry().toHex().data().decode()
        saved_markings = {}
        for key, data in self.marked_items.items():
            saved_data = {}
            if 'color' in data and data['color']:
                saved_data['color'] = data['color'].name()
            if 'tag' in data:
                saved_data['tag'] = data['tag']
            if saved_data:
                saved_markings[key] = saved_data
        self.settings.data["marked_items"] = saved_markings
        self.settings.save()
        
        if self.modified_subtitles:
            reply = QtWidgets.QMessageBox.question(
                self, self.tr("save_changes_question"),
                self.tr("unsaved_changes_message"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QtWidgets.QMessageBox.Yes:
                self.save_subtitles_to_file()
        self.save_converter_file_list()        
        self.stop_audio()
        self.audio_player.stop()
        if hasattr(self, 'wav_converter'):
             self.wav_converter.stop_conversion()

        for f in getattr(self, 'temp_files_to_cleanup', []):
            try: os.remove(f)
            except: pass
        event.accept()
