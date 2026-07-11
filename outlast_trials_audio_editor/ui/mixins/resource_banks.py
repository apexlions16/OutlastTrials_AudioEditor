from ._imports import *

class ResourceBanksMixin:
    def check_soundbanks_info(self):
        sfx_folder = os.path.join(self.wem_root, "SFX")
        
        json_path = os.path.join(sfx_folder, "SoundbanksInfo.json")
        xml_path = os.path.join(sfx_folder, "SoundbanksInfo.xml")

        if os.path.exists(json_path) or os.path.exists(xml_path):
            return 
        DEBUG.log("Neither SoundbanksInfo.json nor .xml found. Prompting user.", "WARNING")
        
        updater_tab_index = -1
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == self.tr("resource_updater_tab"):
                updater_tab_index = i
                break

        if updater_tab_index == -1:
            QtWidgets.QMessageBox.critical(self,
                                        self.tr("critical_file_missing_title"),
                                        self.tr("critical_file_missing_message"))
            return

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(self.tr("soundbanksinfo_missing_title"))
        msg_box.setText(self.tr("soundbanksinfo_missing_message")) 
        msg_box.setInformativeText(self.tr("soundbanksinfo_missing_details"))
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        
        go_btn = msg_box.addButton(self.tr("go_to_updater_btn"), QtWidgets.QMessageBox.AcceptRole)
        later_btn = msg_box.addButton(self.tr("later_btn"), QtWidgets.QMessageBox.RejectRole)
        
        msg_box.exec_()
        
        if msg_box.clickedButton() == go_btn:
            self.tabs.setCurrentIndex(updater_tab_index)

    def check_for_loose_wems(self):
        if not os.path.isdir(self.wem_root):
            return False

        loose_files = []
        for item in os.listdir(self.wem_root):
            item_path = os.path.join(self.wem_root, item)
            if os.path.isfile(item_path):
                loose_files.append(item)

        if not loose_files:
            return False

        DEBUG.log(f"Found {len(loose_files)} loose files in the Wems root directory.", "WARNING")

        sfx_path = os.path.join(self.wem_root, "SFX")
        os.makedirs(sfx_path, exist_ok=True)

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(self.tr("wems_folder_loose_files_title"))

        msg_box.setText(self.tr("wems_folder_loose_files_message").format(count=len(loose_files)).replace(" (.wem/.bnk)", ""))
        msg_box.setInformativeText(self.tr("wems_folder_loose_files_details"))
        msg_box.setIcon(QtWidgets.QMessageBox.Question)
        
        move_btn = msg_box.addButton(self.tr("move_all_files_btn"), QtWidgets.QMessageBox.AcceptRole)
        ignore_btn = msg_box.addButton(self.tr("ignore_btn"), QtWidgets.QMessageBox.RejectRole)
        
        msg_box.exec_()

        if msg_box.clickedButton() == move_btn:
            moved_count = 0
            errors = []
            for filename in loose_files:
                source_path = os.path.join(self.wem_root, filename)
                dest_path = os.path.join(sfx_path, filename)
                try:

                    if os.path.exists(dest_path):
                        errors.append(f"{filename}: File already exists in SFX folder.")
                        DEBUG.log(f"Skipped moving '{filename}', it already exists in SFX.", "WARNING")
                        continue
                    shutil.move(source_path, dest_path)
                    moved_count += 1
                    DEBUG.log(f"Moved '{filename}' to SFX folder.")
                except Exception as e:
                    error_text = str(e)
                    errors.append(f"{filename}: {error_text}")
                    DEBUG.log(f"Error moving '{filename}': {error_text}", "ERROR")
            
            result_message = self.tr("move_complete_message").format(count=moved_count)
            if errors:
                result_message += "\n\n" + self.tr("move_complete_errors").format(count=len(errors), errors="\n".join(errors))
            
            result_message += self.tr("move_complete_restart_note")
            
            QtWidgets.QMessageBox.information(self, self.tr("move_complete_title"), result_message)

        return True

    def check_initial_resources(self):
        updater_tab_index = -1
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == self.tr("resource_updater_tab"):
                updater_tab_index = i
                break
        
        if updater_tab_index == -1:
            return False

        wems_path = os.path.join(self.base_path, "Wems")
        wems_exist = self._wems_folder_is_valid(wems_path)
        
        if not wems_exist:
            DEBUG.log("Wems folder is missing or invalid on startup.", "INFO")
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle(self.tr("initial_setup_title"))
            msg_box.setText(self.tr("wems_folder_missing_message"))
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            go_btn = msg_box.addButton(self.tr("go_to_updater_button"), QtWidgets.QMessageBox.AcceptRole)
            msg_box.addButton(self.tr("cancel"), QtWidgets.QMessageBox.RejectRole)
            msg_box.exec_()
            if msg_box.clickedButton() == go_btn:
                self.tabs.setCurrentIndex(updater_tab_index)
            return True 
        loc_path = os.path.join(self.base_path, "Localization")
        if not os.path.isdir(loc_path) or not any(f.endswith('.locres') for f in os.listdir(loc_path) if os.path.isdir(os.path.join(loc_path, f)) for f in os.listdir(os.path.join(loc_path, f))):
            loc_files_exist = False
            if os.path.exists(loc_path):
                for root, _, files in os.walk(loc_path):
                    if any(f.endswith('.locres') for f in files):
                        loc_files_exist = True
                        break
            
            if not loc_files_exist:
                DEBUG.log("Localization folder has no .locres files on startup.", "INFO")
                msg_box = QtWidgets.QMessageBox(self)
                msg_box.setWindowTitle(self.tr("initial_setup_title"))
                msg_box.setText(self.tr("localization_folder_missing_message"))
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                go_btn = msg_box.addButton(self.tr("go_to_updater_button"), QtWidgets.QMessageBox.AcceptRole)
                msg_box.addButton(self.tr("cancel"), QtWidgets.QMessageBox.RejectRole)
                msg_box.exec_()
                if msg_box.clickedButton() == go_btn:
                    self.tabs.setCurrentIndex(updater_tab_index)
                return True

        return False

    def _wems_folder_is_valid(self, directory):

        if not os.path.isdir(directory):
            return False
            
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.wem'):

                    return True
                    
        return False

    def verify_bnk_sizes(self):
        if not self.ensure_active_profile():
            return

        progress = ProgressDialog(self, "Verifying Mod Integrity...")
        progress.show()
        
        self.verification_thread = threading.Thread(target=self._verify_mod_integrity_thread, args=(progress,))
        self.verification_thread.daemon = True
        self.verification_thread.start()

    def _verify_batch(self, wem_files, id_to_entry_map, bnk_files_info):
        mismatches = []
        bnk_editor_cache = {} 
        
        for wem_path in wem_files:
            wem_name = os.path.basename(wem_path)
            
            try:
                file_id = os.path.splitext(wem_name)[0]
                source_id = int(file_id)
            except ValueError:
                continue

            entry = id_to_entry_map.get(file_id)
            if not entry:
                continue
            
            real_wem_size = os.path.getsize(wem_path)
            
            bnk_info, mod_bnk_path = self._find_bnk_for_entry_with_cache(
                entry, bnk_files_info, bnk_editor_cache
            )

            if bnk_info:
                if bnk_info.file_size != real_wem_size:
                    mismatches.append({
                        "type": "Size Mismatch",
                        "bnk_path": mod_bnk_path,
                        "source_id": source_id,
                        "short_name": entry.get("ShortName", wem_name),
                        "bnk_size": bnk_info.file_size,
                        "wem_size": real_wem_size
                    })
            else:
                source_type = entry.get("Source", "")
                if source_type not in ["StreamedFiles", "MediaFilesNotInAnyBank"]:
                    mismatches.append({
                        "type": "BNK Entry Missing",
                        "bnk_path": "N/A",
                        "source_id": source_id,
                        "short_name": entry.get("ShortName", wem_name),
                        "bnk_size": "N/A",
                        "wem_size": real_wem_size
                    })
        
        return mismatches, len(wem_files)

    def _find_bnk_for_entry_with_cache(self, entry, bnk_files_info, cache):
        source_id = int(entry.get("Id"))
        
        for bnk_path, bnk_type in bnk_files_info:
            if bnk_path not in cache:
                try:
                    cache[bnk_path] = BNKEditor(bnk_path)
                except Exception:
                    continue
            
            original_bnk = cache[bnk_path]
            if not original_bnk.find_sound_by_source_id(source_id):
                continue
            
            if bnk_type == 'sfx':
                rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
            else:
                rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)

            if os.path.exists(mod_bnk_path):
                if mod_bnk_path not in cache:
                    try:
                        cache[mod_bnk_path] = BNKEditor(mod_bnk_path)
                    except Exception:
                        continue
                
                mod_editor = cache[mod_bnk_path]
                entries = mod_editor.find_sound_by_source_id(source_id)
                if entries:
                    return entries[0], mod_bnk_path
        
        return None, None

    def _find_bnk_for_entry_optimized(self, entry, modified_bnks, bnk_editor_cache):
        source_id = int(entry.get("Id"))
        
        for bnk_path, (mod_bnk_path, bnk_type) in modified_bnks.items():

            if bnk_path not in bnk_editor_cache:
                try:
                    bnk_editor_cache[bnk_path] = BNKEditor(bnk_path)
                except Exception:
                    continue
            
            original_bnk = bnk_editor_cache[bnk_path]
            if not original_bnk.find_sound_by_source_id(source_id):
                continue
            
            if mod_bnk_path not in bnk_editor_cache:
                try:
                    bnk_editor_cache[mod_bnk_path] = BNKEditor(mod_bnk_path)
                except Exception:
                    continue
            
            mod_editor = bnk_editor_cache[mod_bnk_path]
            entries = mod_editor.find_sound_by_source_id(source_id)
            if entries:
                return entries[0], mod_bnk_path
        
        return None, None

    def _find_bnk_for_entry(self, entry):
        source_id = int(entry.get("Id"))
        
        bnk_files_info = self.find_relevant_bnk_files()

        for bnk_path, bnk_type in bnk_files_info:
            original_bnk = BNKEditor(bnk_path)
            if not original_bnk.find_sound_by_source_id(source_id):
                continue
            
            if bnk_type == 'sfx':
                rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
            else:
                rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)

            if os.path.exists(mod_bnk_path):
                mod_editor = BNKEditor(mod_bnk_path)
                entries = mod_editor.find_sound_by_source_id(source_id)
                if entries:
                    return entries[0], mod_bnk_path
        
        return None, None

    def rebuild_bnk_index(self, confirm=True):
        if not self.ensure_active_profile():
            return

        if confirm:
            reply = QtWidgets.QMessageBox.question(
                self, 
                self.tr("rebuild_bnk_confirm_title"), 
                self.tr("rebuild_bnk_confirm_text"), 
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.No:
                return

        progress = ProgressDialog(self, self.tr("rebuilding_mod_bnk"))
        progress.show()
        
        self.rebuild_thread = threading.Thread(target=self._rebuild_bnk_thread, args=(progress,))
        self.rebuild_thread.daemon = True
        self.rebuild_thread.start()

    def find_all_original_bnks(self):
        all_bnks = []
        wems_root = os.path.join(self.base_path, "Wems")
        if not os.path.exists(wems_root):
            return []
        for root, _, files in os.walk(wems_root):
            for file in files:
                if file.lower().endswith('.bnk'):
                    bnk_type = 'sfx' if os.path.basename(root) == "SFX" else 'lang'
                    all_bnks.append((os.path.join(root, file), bnk_type))
        return all_bnks

    def _rebuild_bnk_thread(self, progress):
        try:
            DEBUG.log("--- Starting BNK Rebuild (Robust Mode) ---")
            QtCore.QMetaObject.invokeMethod(progress, "set_progress", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(int, 5), QtCore.Q_ARG(str, "Scanning modified audio files..."))

            mod_audio_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows")
            modified_wem_files = {}
            
            if os.path.exists(mod_audio_path):
                for root, _, files in os.walk(mod_audio_path):
                    for file in files:
                        if file.lower().endswith('.wem'):
                            file_id = os.path.splitext(file)[0]
                           
                            if file_id.isdigit():
                                full_path = os.path.join(root, file)
                                modified_wem_files[file_id] = os.path.getsize(full_path)

            if not modified_wem_files:
                raise FileNotFoundError("No modified audio files (IDs) found in MOD_P to rebuild.")

            total_wems = len(modified_wem_files)
            progress.details_updated.emit(f"Found {total_wems} modified WEM files.")
            
            all_original_bnks = self.find_all_original_bnks()
            
            bnk_update_map = {}
            
            bnk_editor_cache = {}

            for i, (file_id, new_size) in enumerate(modified_wem_files.items()):
                progress_percent = 10 + int((i / total_wems) * 30)
                if i % 10 == 0:
                    QtCore.QMetaObject.invokeMethod(progress, "set_progress", QtCore.Qt.QueuedConnection,
                                                    QtCore.Q_ARG(int, progress_percent),
                                                    QtCore.Q_ARG(str, f"Mapping ID {file_id}..."))
                
                found_parent = False
                source_id_int = int(file_id)

                for original_bnk_path, bnk_type in all_original_bnks:
                    try:
                        if original_bnk_path not in bnk_editor_cache:
                           bnk_editor_cache[original_bnk_path] = BNKEditor(original_bnk_path)
                        
                        editor = bnk_editor_cache[original_bnk_path]
                        
                        if editor.find_sound_by_source_id(source_id_int):
                            if original_bnk_path not in bnk_update_map:
                                bnk_update_map[original_bnk_path] = {'type': bnk_type, 'wems': {}}
                            
                            bnk_update_map[original_bnk_path]['wems'][file_id] = new_size
                            found_parent = True
                       
                            break 
                    except Exception as e:
                        DEBUG.log(f"Error reading BNK {os.path.basename(original_bnk_path)}: {e}", "WARNING")
                
                if not found_parent:
                    DEBUG.log(f"Warning: ID {file_id} not found in any known SoundBank.", "WARNING")

            updated_count = 0
            created_count = 0
            total_bnks = len(bnk_update_map)
            
            for i, (original_bnk_path, data) in enumerate(bnk_update_map.items()):
                bnk_type = data['type']
                wems_to_update = data['wems'] # {id_str: size}
                
                progress_percent = 40 + int((i / total_bnks) * 60)
                bnk_name = os.path.basename(original_bnk_path)
                QtCore.QMetaObject.invokeMethod(progress, "set_progress", QtCore.Qt.QueuedConnection,
                                                QtCore.Q_ARG(int, progress_percent),
                                                QtCore.Q_ARG(str, f"Updating {bnk_name}..."))

                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(original_bnk_path, os.path.join(self.wem_root, "SFX"))
               
                    if rel_path.startswith(".."): rel_path = os.path.basename(original_bnk_path)
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else:
                    rel_path = os.path.relpath(original_bnk_path, self.wem_root)
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)

                old_fx_flags = {}
                if os.path.exists(mod_bnk_path):
                    try:
                        old_mod_editor = BNKEditor(mod_bnk_path)
                        for entry in old_mod_editor.find_all_sounds():
                            old_fx_flags[str(entry.source_id)] = entry.override_fx
                        os.remove(mod_bnk_path) 
                    except Exception: 
                        pass
                
                os.makedirs(os.path.dirname(mod_bnk_path), exist_ok=True)
                shutil.copy2(original_bnk_path, mod_bnk_path)
                created_count += 1

                new_mod_editor = BNKEditor(mod_bnk_path)
                
                file_modified = False
                
                for file_id_str, new_size in wems_to_update.items():
                    source_id = int(file_id_str)
                    
                    fx_flag = old_fx_flags.get(file_id_str) 
                    
                    if new_mod_editor.modify_sound(source_id, new_size=new_size, override_fx=fx_flag):
                        updated_count += 1
                        file_modified = True
                        DEBUG.log(f"Updated {bnk_name}: ID {source_id} -> {new_size} bytes")
                    else:
                        DEBUG.log(f"FAILED to update {bnk_name}: ID {source_id} not found in binary scan!", "ERROR")

                if file_modified:
                    new_mod_editor.save_file()
                    
                    for file_id_str in wems_to_update.keys():
                        self.invalidate_bnk_cache(int(file_id_str))
                else:
                    DEBUG.log(f"No changes made to {bnk_name}, keeping original copy.", "WARNING")

            self.bnk_cache_mod.clear()
            
            QtCore.QMetaObject.invokeMethod(progress, "close", QtCore.Qt.QueuedConnection)
            
            final_message = (f"Rebuild Complete!\n\n"
                             f"Processed {len(modified_wem_files)} modified audio files.\n"
                             f"Re-created {created_count} BNK files.\n"
                             f"Updated {updated_count} size entries.")

            QtCore.QMetaObject.invokeMethod(self, "show_message_box", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(int, QtWidgets.QMessageBox.Information),
                                            QtCore.Q_ARG(str, self.tr("rebuild_complete_title")),
                                            QtCore.Q_ARG(str, final_message))
            
            current_lang = self.get_current_language()
            if current_lang:
                QtCore.QMetaObject.invokeMethod(self, "populate_tree", QtCore.Qt.QueuedConnection,
                                                QtCore.Q_ARG(str, current_lang))

        except Exception as e:
            import traceback
            DEBUG.log(f"BNK Rebuild Critical Error: {e}\n{traceback.format_exc()}", "ERROR")
            QtCore.QMetaObject.invokeMethod(progress, "close", QtCore.Qt.QueuedConnection)
            QtCore.QMetaObject.invokeMethod(self, "_show_bnk_verification_error", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(str, str(e)))

    def fix_bnk_mismatches(self, mismatches):

        progress = ProgressDialog(self, "Fixing Mod Issues...")
        progress.show()
        
        fixable_mismatches = [item for item in mismatches if item['type'] == 'Size Mismatch']

        if not fixable_mismatches:
            progress.close()
            QtWidgets.QMessageBox.information(self, "Fix Complete", "No automatically fixable issues were found (e.g., 'BNK Entry Missing').")
            return
        
        fixed_count = 0
        error_count = 0
        
        fixes_by_bnk = {}
        for item in fixable_mismatches:
            bnk_path = item['bnk_path']
            if bnk_path not in fixes_by_bnk:
                fixes_by_bnk[bnk_path] = []
            fixes_by_bnk[bnk_path].append(item)
            
        total_bnks_to_fix = len(fixes_by_bnk)
        
        for i, (bnk_path, items_to_fix) in enumerate(fixes_by_bnk.items()):
            bnk_name = os.path.basename(bnk_path)
            progress_percent = int((i / total_bnks_to_fix) * 100)
            QtCore.QMetaObject.invokeMethod(progress, "set_progress", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(int, progress_percent), QtCore.Q_ARG(str, f"Fixing {bnk_name}..."))
            
            try:
                editor = BNKEditor(bnk_path)
                modified = False
                for item in items_to_fix:
                    if editor.modify_sound(item['source_id'], new_size=item['wem_size']):
                        fixed_count += 1
                        modified = True
                
                if modified:
                    editor.save_file()
   
                    for item in items_to_fix:
                        self.invalidate_bnk_cache(item['source_id'])

            except Exception as e:
                error_count += len(items_to_fix)
                DEBUG.log(f"Error fixing {bnk_name}: {e}", "ERROR")

        progress.close()
        
        message = f"Fixed {fixed_count} size mismatch issues."
        if error_count > 0:
            message += f"\nFailed to fix {error_count} entries. See debug console for details."
            
        QtWidgets.QMessageBox.information(self, "Fix Complete", message)
