from ._imports import *

class CoreMixin:
    def show_dialog(self, dialog):
        dialog.setWindowFlags(dialog.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog.exec_()

    def get_mod_path(self, file_id, lang):
        if not self.mod_p_path:
            return None
            
        if lang != "SFX":
            new_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", lang, f"{file_id}.wem")
        else:
            new_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", f"{file_id}.wem")
            
        if os.path.exists(new_path):
            return new_path
       
        if lang != "SFX":
            old_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem")
        else:
            old_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
            
        if os.path.exists(old_path):
            return old_path

        return new_path

    def initialize_profiles_and_ui(self):

        profiles_root = os.path.join(self.base_path, "Profiles")
        legacy_mod_p_path = os.path.join(self.base_path, "MOD_P")
        
        if not os.path.isdir(profiles_root):
            DEBUG.log("Root 'Profiles' folder not found. Running first-time setup or migration.")
            
            if os.path.isdir(legacy_mod_p_path):
                self.handle_legacy_mod_p_migration(legacy_mod_p_path, profiles_root)
            else: 
                self.handle_new_user_setup(profiles_root)
        
        self.load_profiles_from_settings()
        return True

    def handle_new_user_setup(self, profiles_root):
        DEBUG.log("Performing automatic new user setup.")
        try:

            os.makedirs(profiles_root, exist_ok=True)
            
            default_profile_name = "Default"
            profile_path = os.path.join(profiles_root, default_profile_name)
            new_mod_p_path = os.path.join(profile_path, f"{default_profile_name}_P")
            
            os.makedirs(new_mod_p_path, exist_ok=True)
            
            profile_json_path = os.path.join(profile_path, "profile.json")
            profile_info = {
                "author": "New User", "version": "1.0",
                "description": "Default profile created on first launch."
            }
            with open(profile_json_path, 'w', encoding='utf-8') as f:
                json.dump(profile_info, f, indent=2)

            self.settings.data["mod_profiles"] = {default_profile_name: profile_path}
            self.settings.data["active_profile"] = default_profile_name
            self.settings.save()

            self.show_message_box(
                QtWidgets.QMessageBox.Information,
                self.tr("setup_complete_title"),
                self.tr("setup_complete_msg").format(mods_root=profiles_root)
            )
            return True

        except Exception as e:
            self.show_message_box(
                QtWidgets.QMessageBox.Critical,
                self.tr("setup_failed_title"),
                self.tr("setup_failed_msg").format(e=e)
            )
            return False

    def handle_legacy_mod_p_migration(self, legacy_mod_p_path, profiles_root):
        DEBUG.log(f"Performing automatic migration of '{legacy_mod_p_path}'")
        try:
            os.makedirs(profiles_root, exist_ok=True)
            
            default_profile_name = "Default"
            profile_path = os.path.join(profiles_root, default_profile_name)
            new_mod_p_path = os.path.join(profile_path, f"{default_profile_name}_P")
            
            if not os.path.exists(profile_path):
                os.makedirs(profile_path)
            
            shutil.move(legacy_mod_p_path, new_mod_p_path)
            
            profile_json_path = os.path.join(profile_path, "profile.json")
            profile_info = {
                "author": "Migrated", "version": "1.0",
                "description": "This profile was automatically migrated from the legacy MOD_P folder."
            }
            with open(profile_json_path, 'w', encoding='utf-8') as f:
                json.dump(profile_info, f, indent=2)

            self.settings.data["mod_profiles"] = {default_profile_name: profile_path}
            self.settings.data["active_profile"] = default_profile_name
            self.settings.save()

            self.show_message_box(
                QtWidgets.QMessageBox.Information,
                self.tr("migration_complete_title"),
                self.tr("migration_complete_msg").format(mods_root=profiles_root)
            )

        except Exception as e:
            self.show_message_box(
                QtWidgets.QMessageBox.Critical,
                self.tr("migration_failed_title"),
                self.tr("migration_failed_msg").format(e=e)
            )
            if os.path.exists(new_mod_p_path):
                 shutil.move(new_mod_p_path, legacy_mod_p_path)

    def ensure_active_profile(self):
        if self.active_profile_name and self.mod_p_path:
            return True

        reply = self.show_message_box(
            QtWidgets.QMessageBox.Information,
            "No Active Profile",
            "No mod profile is currently active. Please create or activate a profile first.",
            buttons=QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        if reply == QtWidgets.QMessageBox.Ok:
            self.show_profile_manager()
        
        return self.active_profile_name and self.mod_p_path is not None

    def get_original_path(self, file_id, lang):
        standard_path = os.path.join(self.wem_root, lang, f"{file_id}.wem")
        if os.path.exists(standard_path):
            return standard_path
            
        if lang == "SFX":
            media_path = os.path.join(self.wem_root, "Media", f"{file_id}.wem")
        else:
            media_path = os.path.join(self.wem_root, "Media", lang, f"{file_id}.wem")
            
        if os.path.exists(media_path):
            return media_path
            
        if lang == "SFX":
            sfx_path = os.path.join(self.wem_root, "SFX", f"{file_id}.wem")
            if os.path.exists(sfx_path):
                return sfx_path 
                
        return standard_path

    def find_relevant_bnk_files(self, force_all=False):

        bnk_files_info = []
        bnk_paths_set = set()
        wems_root = os.path.join(self.base_path, "Wems")
        if not os.path.exists(wems_root):
            return []

        scan_folders = []
        
        if force_all:
            DEBUG.log("Force all BNKs: Scanning all subdirectories in Wems folder.")
            for item in os.listdir(wems_root):
                path = os.path.join(wems_root, item)
                if os.path.isdir(path):
                    scan_folders.append(path)

        else:
            sfx_path = os.path.join(wems_root, "SFX")
            if os.path.exists(sfx_path):
                scan_folders.append(sfx_path)

            lang_setting = self.settings.data.get("wem_process_language", "english")
            lang_folder_name = "English(US)" if lang_setting == "english" else "Francais"
            lang_path = os.path.join(wems_root, lang_folder_name)
            if os.path.exists(lang_path):
                scan_folders.append(lang_path)
            DEBUG.log(f"Standard scan: looking for BNKs for language '{lang_setting}'.")

        for folder_path in scan_folders:
            bnk_type = 'sfx' if os.path.basename(folder_path) == "SFX" else 'lang'
            try:
                for file in os.listdir(folder_path):
                    if file.lower().endswith('.bnk'):
                        full_path = os.path.join(folder_path, file)
                        if full_path not in bnk_paths_set:
                            bnk_files_info.append((full_path, bnk_type))
                            bnk_paths_set.add(full_path)
            except OSError as e:
                DEBUG.log(f"Can't read folder {folder_path}: {e}", "WARNING")

        mode_str = "FORCE ALL" if force_all else "STANDARD"
        DEBUG.log(f"Found {len(bnk_files_info)} relevant BNK files (Mode: {mode_str}).")
        return bnk_files_info

    def _build_wem_index(self):
        if self.wem_index is not None:
            return 

        DEBUG.log("Building WEM file index (scanning Wems folder)...")
        self.wem_index = {}

        wems_folder = os.path.join(self.base_path, "Wems")
        if not os.path.exists(wems_folder):
            DEBUG.log("Wems folder not found")
            return

        for root, dirs, files in os.walk(wems_folder):
       
            
            for file in files:
                if file.lower().endswith('.wem'):
                    file_id = os.path.splitext(file)[0]
                    file_path = os.path.join(root, file)

                    rel_path = os.path.relpath(root, wems_folder)
                    parts = rel_path.split(os.sep)
                   
                    folder_name = "SFX"
                    
                    if rel_path == ".":
                        folder_name = "SFX"
                    elif parts[0] == "Media":
                        if len(parts) > 1:
                            folder_name = parts[1] # Media/English(US) -> English(US)
                        else:
                            folder_name = "SFX" # Media -> SFX
                    elif parts[0] == "SFX":
                        folder_name = "SFX"
                    else:
                        folder_name = parts[0] # English(US) -> English(US)

                    if file_id not in self.wem_index:
                        self.wem_index[file_id] = {}

                    self.wem_index[file_id][folder_name] = {
                        'path': file_path,
                        'size': os.path.getsize(file_path)
                    }

        DEBUG.log(f"WEM index built: {len(self.wem_index)} unique IDs found.")

    def update_auto_save_timer(self):
        auto_save_setting = self.settings.data.get("auto_save", True)
        
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            DEBUG.log("Auto-save timer stopped")
        

        if auto_save_setting:
            self.auto_save_timer.start(300000) 
            self.auto_save_enabled = True
            DEBUG.log("Auto-save timer started (5 minutes)")
        else:
            self.auto_save_enabled = False
            DEBUG.log("Auto-save disabled")
