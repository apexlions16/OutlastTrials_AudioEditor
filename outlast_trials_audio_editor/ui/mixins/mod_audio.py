from ._imports import *

class ModAudioMixin:
    def auto_save_subtitles(self):
        if not self.auto_save_enabled or not self.settings.data.get("auto_save", True):
            DEBUG.log("Auto-save skipped - disabled")
            return
        
        if not self.modified_subtitles:
            DEBUG.log("Auto-save skipped - no changes")
            return
        
        DEBUG.log(f"Auto-saving {len(self.modified_subtitles)} modified subtitles...")
        
        try:

            self.status_bar.showMessage("Auto-saving...", 2000)
            
            QtCore.QTimer.singleShot(100, self.perform_auto_save)
            
        except Exception as e:
            DEBUG.log(f"Auto-save error: {e}", "ERROR")

    def perform_auto_save(self):
        try:
            self.save_subtitles_to_file()
            DEBUG.log(f"Auto-save completed successfully")
            self.status_bar.showMessage("Auto-saved", 1000)
        except Exception as e:
            DEBUG.log(f"Auto-save failed: {e}", "ERROR")
            self.status_bar.showMessage("Auto-save failed", 2000)

    def delete_mod_audio(self, entry, lang):
        """Delete modified audio file(s) and revert BNK changes"""
        widgets = self.tab_widgets.get(lang) 
        if not widgets:
            DEBUG.log(f"No widgets found for language: {lang}", "WARNING")
            return
        
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if len(items) > 1:
            file_list = []
            for item in items:
                if item.childCount() == 0:
                    entry_data = item.data(0, QtCore.Qt.UserRole)
                    if entry_data:
                        file_id = entry_data.get("Id", "")
                        mod_path = self.get_mod_path(file_id, lang) 
                        if mod_path and os.path.exists(mod_path):
                            file_list.append(entry_data)
            
            if not file_list:
                return
                
            reply = QtWidgets.QMessageBox.question(
                self, "Delete Multiple Mod Audio",
                f"Delete modified audio for {len(file_list)} files?\nThis will also revert changes in BNK files.\n\nThis action cannot be undone.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                deleted_count = 0
                for entry_to_delete in file_list:
                    self._perform_single_delete(entry_to_delete, lang)
                    deleted_count += 1
                
                QtCore.QTimer.singleShot(0, lambda: self.populate_tree(lang))
                self.status_bar.showMessage(f"Deleted {deleted_count} mod audio files", 3000)
            return

        if not items or items[0].childCount() > 0:
            return
            
        entry_to_delete = items[0].data(0, QtCore.Qt.UserRole)
        if not entry_to_delete:
            return
        
        file_id = entry_to_delete.get("Id", "")
        shortname = entry_to_delete.get("ShortName", "")
        
        mod_wem_path = self.get_mod_path(file_id, lang)
        
        if not mod_wem_path or not os.path.exists(mod_wem_path):
            QtWidgets.QMessageBox.information(self, "Info", f"No modified audio found for {shortname}")
            return
            
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Mod Audio",
            f"Delete modified audio for:\n{shortname}\nThis will also revert changes in BNK files.\n\nThis action cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self._perform_single_delete(entry_to_delete, lang)
            QtCore.QTimer.singleShot(0, lambda: self.populate_tree(lang))

    def _perform_single_delete(self, entry, lang):
        file_id = entry.get("Id", "")
        shortname = entry.get("ShortName", "")
        source_id = int(file_id)

        mod_wem_path = self.get_mod_path(file_id, lang)

        try:
          
            if mod_wem_path and os.path.exists(mod_wem_path):
                os.remove(mod_wem_path)
                DEBUG.log(f"Deleted wem audio: {mod_wem_path}")
            
            old_paths = [
                os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem"),
                os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
            ]
            for p in old_paths:
                if os.path.exists(p):
                    os.remove(p)
                    DEBUG.log(f"Deleted legacy wem audio: {p}")

            bnk_reverted_count = 0
            bnk_files_info = self.find_relevant_bnk_files()

            for bnk_path, bnk_type in bnk_files_info:
                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else:
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                
                if not os.path.exists(mod_bnk_path):
                    continue

                original_bnk = BNKEditor(bnk_path)
                original_entries = original_bnk.find_sound_by_source_id(source_id)
                
                if not original_entries:
                    continue
                
                original_entry = original_entries[0]

                mod_bnk_editor = BNKEditor(mod_bnk_path)
               
                if mod_bnk_editor.modify_sound(source_id, 
                                            new_size=original_entry.file_size, 
                                            override_fx=original_entry.override_fx,
                                            find_by_size=None):
                    mod_bnk_editor.save_file()
                    self.invalidate_bnk_cache(source_id)
                    DEBUG.log(f"BNK {os.path.basename(mod_bnk_path)} restored to original values.")
                    bnk_reverted_count += 1
         
            
            if bnk_reverted_count > 0:
                self.status_bar.showMessage(f"Deleted mod audio and restored {bnk_reverted_count} BNK entries for {shortname}", 3000)
            else:
                self.status_bar.showMessage(f"Deleted mod audio for {shortname} (No BNK changes found)", 3000)

        except Exception as e:
            DEBUG.log(f"Error deleting {shortname}: {e}", "ERROR")
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to process deletion for {shortname}: {str(e)}")

    def invalidate_bnk_cache(self, source_id: int):
        source_id_to_invalidate = int(source_id)
        DEBUG.log(f"Invalidating BNK cache for Source ID: {source_id_to_invalidate}")

        for bnk_path in list(self.bnk_cache_mod.keys()):
            if source_id_to_invalidate in self.bnk_cache_mod[bnk_path]:
                del self.bnk_cache_mod[bnk_path][source_id_to_invalidate]
                DEBUG.log(f"  > Removed ID {source_id_to_invalidate} from mod cache for {os.path.basename(bnk_path)}")

        for bnk_path in list(self.bnk_cache_orig.keys()):
            if source_id_to_invalidate in self.bnk_cache_orig[bnk_path]:
                del self.bnk_cache_orig[bnk_path][source_id_to_invalidate]
                DEBUG.log(f"  > Removed ID {source_id_to_invalidate} from original cache for {os.path.basename(bnk_path)}")

    def tr(self, key):
        """Translate key to current language"""
        return self.translations.get(self.current_lang, {}).get(key, key)

    def check_required_files(self):
        """Check if all required files exist"""
        missing_files = []
        
        required_files = [
            (self.unreal_locres_path, "UnrealLocres.exe"),
            (self.repak_path, "repak.exe"),
            (self.vgmstream_path, "vgmstream-cli.exe")
        ]
        
        for file_path, file_name in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_name)
                DEBUG.log(f"Missing required file: {file_path}", "WARNING")
        
        if missing_files:
            msg = f"Missing required files in data folder:\n" + "\n".join(f"• {f}" for f in missing_files)
            msg += "\n\nPlease ensure all files are in the correct location."
            QtWidgets.QMessageBox.warning(None, "Missing Files", msg)
