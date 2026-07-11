from ._imports import *

class AudioLibraryMixin:
    def update_status(self):
        total_files = len(self.all_files)
        total_subtitles = len(self.subtitles)
        modified = len(self.modified_subtitles)
        
        status_text = f"Files: {total_files} | Subtitles: {total_subtitles}"
        if modified > 0:
            status_text += f" | Modified: {modified}"
            
        self.status_bar.showMessage(status_text)

    def load_all_soundbank_files(self, path=None):
        DEBUG.log(f"Loading soundbank files from: {path}")
        all_files = []
        
        if not path or not os.path.exists(path):
            DEBUG.log("SoundbanksInfo file not found.", "WARNING")
            return []

        try:
            ext = os.path.splitext(path)[1].lower()
            
            if ext == '.json':
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                soundbanks_info = data.get("SoundBanksInfo") or data.get("SoundbanksInfo") or data
                
                if not soundbanks_info:
                    DEBUG.log("ERROR: Could not find SoundBanksInfo block.", "ERROR")
                    return []
                
                streamed_files = soundbanks_info.get("StreamedFiles", [])
                for file_entry in streamed_files:
                    file_entry["Source"] = "StreamedFiles"
                    if "Path" in file_entry:
                        file_entry["Path"] = file_entry["Path"].replace("Media/", "").replace("Media\\", "")
                all_files.extend(streamed_files)
                
                media_not_in_bank = soundbanks_info.get("MediaFilesNotInAnyBank", [])
                for file_entry in media_not_in_bank:
                    file_entry["Source"] = "MediaFilesNotInAnyBank"
                    if "Path" in file_entry:
                        file_entry["Path"] = file_entry["Path"].replace("Media/", "").replace("Media\\", "")
                all_files.extend(media_not_in_bank)

                soundbanks_list = soundbanks_info.get("SoundBanks", [])
                
                unique_files_map = {f["Id"]: f for f in all_files}
                
                for sb in soundbanks_list:
                 
                    bnk_name = sb.get("ShortName", "UnknownBank")
                    
                    media_list = sb.get("Media", [])
                    for media_entry in media_list:
                        file_id = media_entry.get("Id")
                        
                        if file_id and file_id not in unique_files_map:
                      
                            if "Path" in media_entry:
                                media_entry["Path"] = media_entry["Path"].replace("Media/", "").replace("Media\\", "")
                            
                            media_entry["Source"] = f"Bank: {bnk_name}"
                            
                            unique_files_map[file_id] = media_entry
                            all_files.append(media_entry)
                
                DEBUG.log(f"Loaded {len(streamed_files)} StreamedFiles, {len(media_not_in_bank)} LooseMedia, and {len(all_files) - len(streamed_files) - len(media_not_in_bank)} files from SoundBanks Media.")

            elif ext == '.xml':
          
                tree = ET.parse(path)
                root = tree.getroot()
                
                streamed_files_elem = root.find("StreamedFiles")
                if streamed_files_elem is not None:
                    for file_elem in streamed_files_elem.findall("File"):
                        raw_path = file_elem.find("Path").text if file_elem.find("Path") is not None else ""
                        clean_path = raw_path.replace("Media/", "").replace("Media\\", "")
                        
                        file_entry = { 
                            "Id": file_elem.get("Id"), 
                            "Language": file_elem.get("Language"), 
                            "ShortName": file_elem.find("ShortName").text if file_elem.find("ShortName") is not None else "", 
                            "Path": clean_path, 
                            "Source": "StreamedFiles" 
                        }
                        all_files.append(file_entry)
                
                media_files_elem = root.find("MediaFilesNotInAnyBank")
                if media_files_elem is not None:
                    for file_elem in media_files_elem.findall("File"):
                        raw_path = file_elem.find("Path").text if file_elem.find("Path") is not None else ""
                        clean_path = raw_path.replace("Media/", "").replace("Media\\", "")

                        file_entry = { 
                            "Id": file_elem.get("Id"), 
                            "Language": file_elem.get("Language"), 
                            "ShortName": file_elem.find("ShortName").text if file_elem.find("ShortName") is not None else "", 
                            "Path": clean_path, 
                            "Source": "MediaFilesNotInAnyBank" 
                        }
                        all_files.append(file_entry)
                        
                soundbanks_elem = root.find("SoundBanks")
                if soundbanks_elem is not None:
                    for sb_elem in soundbanks_elem.findall("SoundBank"):
                        bnk_name = sb_elem.find("ShortName").text if sb_elem.find("ShortName") is not None else "Unknown"
                        media_elem = sb_elem.find("Media")
                        if media_elem is not None:
                            for file_elem in media_elem.findall("File"):
                                file_id = file_elem.get("Id")
                       
                                raw_path = file_elem.find("Path").text if file_elem.find("Path") is not None else ""
                                clean_path = raw_path.replace("Media/", "").replace("Media\\", "")
                                
                                file_entry = {
                                    "Id": file_id,
                                    "Language": file_elem.get("Language"),
                                    "ShortName": file_elem.find("ShortName").text if file_elem.find("ShortName") is not None else "",
                                    "Path": clean_path,
                                    "Source": f"Bank: {bnk_name}"
                                }
                                all_files.append(file_entry)

            else:
                raise ValueError(f"Unsupported file format: {ext}")
            
            unique_files = {}
            for f in all_files:
                fid = f.get("Id")
                if fid and fid not in unique_files:
                    unique_files[fid] = f
            
            final_list = list(unique_files.values())
            DEBUG.log(f"Total unique files loaded from SoundbanksInfo: {len(final_list)}")
            return final_list
            
        except Exception as e:
            DEBUG.log(f"Error loading soundbank: {e}", "ERROR")
            import traceback
            DEBUG.log(traceback.format_exc(), "ERROR")
            return []

    def _scan_and_add_orphaned_wems(self, known_ids):
        """Scans the Wems directory to find and add files not listed in SoundbanksInfo."""
        orphaned_entries = []
        if not os.path.exists(self.wem_root):
            DEBUG.log(f"Wems directory not found at {self.wem_root}, skipping scan.", "WARNING")
            return orphaned_entries

        for root, _, files in os.walk(self.wem_root):
            for file in files:
                if not file.lower().endswith('.wem'):
                    continue

                file_id = os.path.splitext(file)[0]
                if file_id in known_ids:
                    continue

                full_path = os.path.join(root, file)
                
                rel_path = os.path.relpath(root, self.wem_root)
                lang = "SFX" if rel_path == '.' else rel_path

                short_name = f"{file_id}.wav"
                try:
                    analyzer = WEMAnalyzer(full_path)
                    if analyzer.analyze():
                        markers = analyzer.get_markers_info()
                        if markers and markers[0]['label']:
                            short_name = f"{markers[0]['label']}.wav"
                            DEBUG.log(f"Orphaned file '{file}' named from marker: '{short_name}'")
                except Exception as e:
                    DEBUG.log(f"Could not analyze markers for orphaned file {file}: {e}", "WARNING")

                new_entry = {
                    "Id": file_id,
                    "Language": lang,
                    "ShortName": short_name,
                    "Path": file, 
                    "Source": "ScannedFromFileSystem"
                }
                orphaned_entries.append(new_entry)

        if orphaned_entries:
            DEBUG.log(f"Added {len(orphaned_entries)} orphaned WEM files found on disk.")
        else:
            DEBUG.log("No orphaned WEM files found on disk.")
            
        return orphaned_entries

    def group_by_language(self):
        entries_by_lang = {}
        for entry in self.all_files:
            lang = entry.get("Language", "SFX") 
            entries_by_lang.setdefault(lang, []).append(entry)
            
        DEBUG.log(f"Files grouped by language: {list(entries_by_lang.keys())}")
        for lang, entries in entries_by_lang.items():
            DEBUG.log(f"  {lang}: {len(entries)} files")
            
        return entries_by_lang

    def get_current_language(self):
   
        current_index = self.tabs.currentIndex()
        if current_index >= 0 and current_index < len(self.tab_widgets):
            languages = list(self.tab_widgets.keys())
            if current_index < len(languages):
                return languages[current_index]
        return None

    def _tree_populate_generator(self, tree, filtered_wrappers, lang, is_flat_view, selected_keys):

        
        root_groups = {}
        id_only_category = "Numeric ID Files"
        id_only_item = None
        
        
        for i, wrapper in enumerate(filtered_wrappers):
            entry = wrapper['_orig']
            has_mod = wrapper['has_mod_audio']
            
            if is_flat_view:
        
                parent_item = tree.invisibleRootItem()
                item = self.add_tree_item(parent_item, entry, lang, has_mod)
            else:
             
                shortname = entry.get("ShortName", "")
                name_without_ext = shortname.rsplit('.', 1)[0]
                
                if name_without_ext.isdigit():
                    if id_only_item is None:
                        id_only_item = QtWidgets.QTreeWidgetItem(tree, [f"{id_only_category}"])
                    
                    self.add_tree_item(id_only_item, entry, lang, has_mod)
                else:
                    parts = name_without_ext.split("_")[:3]
                    
                    if not parts:
                        self.add_tree_item(tree.invisibleRootItem(), entry, lang, has_mod)
                        continue

                    current_parent_dict = root_groups
                    current_parent_item = tree.invisibleRootItem()

                    for level_idx, part in enumerate(parts):
                        if part not in current_parent_dict:
                            display_name = "VO (Voice)" if level_idx == 0 and part.upper() == "VO" else part
                            new_item = QtWidgets.QTreeWidgetItem(current_parent_item, [display_name])
                            
                            if level_idx == 0 and part.upper() == "VO":
                                new_item.setExpanded(True)
                            
                            current_parent_dict[part] = {"__item__": new_item, "__children__": {}}
                        
                        current_parent_item = current_parent_dict[part]["__item__"]
                        current_parent_dict = current_parent_dict[part]["__children__"]

                    self.add_tree_item(current_parent_item, entry, lang, has_mod)

            if selected_keys:
                key = os.path.splitext(entry.get("ShortName", ""))[0]
                if key in selected_keys:

                    pass 

            if i % 50 == 0:
                yield

        if not is_flat_view:
            self._update_group_counts_recursive(tree.invisibleRootItem(), id_only_category)
            if id_only_item:
                id_only_item.setText(0, f"{id_only_category} ({id_only_item.childCount()})")

        if selected_keys:
            self.restore_tree_selection(tree, selected_keys)
        
        yield

    def _process_tree_batch(self):
      
        if not self.tree_loader_generator or not self.current_loading_lang:
            self.tree_loader_timer.stop()
            return

        widgets = self.tab_widgets.get(self.current_loading_lang)
        if not widgets:
            self.tree_loader_timer.stop()
            return
            
        tree = widgets["tree"]
        
        tree.setUpdatesEnabled(False)
        
        start_time = time.time()
        try:
          
            while (time.time() - start_time) < 0.015:
                next(self.tree_loader_generator)
                
        except StopIteration:
            
            self.tree_loader_timer.stop()
            self.tree_loader_generator = None
            tree.setUpdatesEnabled(True)
            # DEBUG.log("Tree population complete")
        except Exception as e:
            DEBUG.log(f"Error in tree population: {e}", "ERROR")
            self.tree_loader_timer.stop()
            self.tree_loader_generator = None
            tree.setUpdatesEnabled(True)
        finally:
        
            tree.setUpdatesEnabled(True)

    def _update_group_counts_recursive(self, item, id_category_name):
       
        count = 0
        for i in range(item.childCount()):
            child = item.child(i)
           
            if child.text(0).startswith(id_category_name):
                continue
                
            if child.childCount() > 0:
                count += self._update_group_counts_recursive(child, id_category_name)
            else:
                count += 1
        
        if item.parent() is not None and item.childCount() > 0:
            current_text = item.text(0)
            if "(" not in current_text:
                item.setText(0, f"{current_text} ({count})")
        
        return count

    def add_tree_item(self, parent_item, entry, lang, has_mod_audio):
        """Adds a single entry as an item to the tree."""
        shortname = entry.get("ShortName", "")
        key = os.path.splitext(shortname)[0]
        subtitle = self.subtitles.get(key, "")
        
        mod_status = ""
        if has_mod_audio:
            mod_status = "♪"
        
        item = QtWidgets.QTreeWidgetItem(parent_item, [
            shortname,
            entry.get("Id", ""),
            subtitle,
            "✓" + mod_status if key in self.modified_subtitles else mod_status,
            ""  
        ])

        marking = self.marked_items.get(key, {})
        if 'color' in marking and marking['color'] is not None:
            for col in range(5):
                item.setBackground(col, marking['color'])
        
        if 'tag' in marking:
            item.setText(4, marking['tag'])
        
        item.setData(0, QtCore.Qt.UserRole, entry)
        
        if not subtitle:
            item.setForeground(2, QtGui.QBrush(QtGui.QColor(128, 128, 128)))
            
        if entry.get("Source") == "MediaFilesNotInAnyBank":
            item.setForeground(0, QtGui.QBrush(QtGui.QColor(100, 100, 200)))
            
        return item

    def restore_tree_selection(self, tree, target_keys):
        """Restore tree selection after refresh"""
        def search_and_select(parent_item):
            for i in range(parent_item.childCount()):
                try:
                    item = parent_item.child(i)
                    if item.childCount() == 0:
                        entry = item.data(0, QtCore.Qt.UserRole)
                        if entry:
                            shortname = entry.get("ShortName", "")
                            key = os.path.splitext(shortname)[0]
                            if key in target_keys:
                                item.setSelected(True)
                                tree.setCurrentItem(item)
                                return True
                    else:
                        if search_and_select(item):
                            return True
                except RuntimeError:
                    continue
            return False
        
        try:
            root = tree.invisibleRootItem()
            search_and_select(root)
        except RuntimeError:
            pass

    def on_selection_changed(self, lang):
        """Updated selection handler without summary"""
        if not self.mod_p_path:
            return

        widgets = self.tab_widgets[lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        file_items = [item for item in items if item.childCount() == 0 and item.data(0, QtCore.Qt.UserRole)]
        if hasattr(self, 'volume_adjust_action'):
            if len(file_items) == 0:
                self.volume_adjust_action.setToolTip(self.tr("volume_adjust_tooltip_no_selection"))
                self.volume_adjust_action.setEnabled(False)
            elif len(file_items) == 1:
                entry = file_items[0].data(0, QtCore.Qt.UserRole)
                filename = entry.get('ShortName', 'file') if entry else 'file'
                self.volume_adjust_action.setToolTip(self.tr("volume_adjust_tooltip_single").format(filename=filename))
                self.volume_adjust_action.setEnabled(True)
            else:
                self.volume_adjust_action.setToolTip(self.tr("volume_adjust_tooltip_batch").format(count=len(file_items)))
                self.volume_adjust_action.setEnabled(True)
        if not items:
            widgets["play_mod_btn"].hide()
            return
            
        item = items[0]
        if item.childCount() > 0:
            widgets["play_mod_btn"].hide()
            return
            
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            widgets["play_mod_btn"].hide()
            return

        shortname = entry.get("ShortName", "")
        key = os.path.splitext(shortname)[0]
        subtitle = self.subtitles.get(key, "")
        original_subtitle = self.original_subtitles.get(key, "")
        marking = self.marked_items.get(key, {})
        tag = marking.get('tag', 'None')
        widgets["info_labels"]["tag"].setText(tag)
        widgets["subtitle_text"].setPlainText(subtitle)

        if original_subtitle and original_subtitle != subtitle:
            widgets["original_subtitle_label"].setText(f"{self.tr('original')}: {original_subtitle}")
            widgets["original_subtitle_label"].show()
        else:
            widgets["original_subtitle_label"].hide()
        
        widgets["info_labels"]["id"].setText(entry.get("Id", ""))
        widgets["info_labels"]["name"].setText(shortname)
        widgets["info_labels"]["path"].setText(entry.get("Path", ""))
        widgets["info_labels"]["source"].setText(entry.get("Source", ""))
        
        file_id = entry.get("Id", "")
        mod_wem_path = self.get_mod_path(file_id, lang)
        
        has_mod = os.path.exists(mod_wem_path) if mod_wem_path else False
        widgets["play_mod_btn"].setVisible(has_mod)
        
        self.load_audio_comparison_info(file_id, lang, widgets)

    def load_audio_comparison_info(self, file_id, lang, widgets):
        self.current_bnk_request_id += 1
        request_id = self.current_bnk_request_id

        original_wem_path = self.get_original_path(file_id, lang)
        mod_wem_path = self.get_mod_path(file_id, lang)
        
        date_format = "%Y-%m-%d %H:%M:%S"

        original_info = self.get_wem_audio_info_with_markers(original_wem_path) if os.path.exists(original_wem_path) else None
        if original_info:
            original_info['file_size'] = os.path.getsize(original_wem_path)

        modified_info = self.get_wem_audio_info_with_markers(mod_wem_path) if os.path.exists(mod_wem_path) else None

        if modified_info:
            modified_info['file_size'] = os.path.getsize(mod_wem_path)
            try:
                mtime = os.path.getmtime(mod_wem_path)
                modified_info['modified_date'] = datetime.fromtimestamp(mtime).strftime(date_format)
            except OSError:
                modified_info['modified_date'] = "N/A"
        
        if original_info:
            formatted_original = self.format_audio_info(original_info)
            for key, label in widgets["original_info_labels"].items():
                if key in formatted_original: label.setText(formatted_original[key])
            size_kb = original_info['file_size'] / 1024
            widgets["original_info_labels"]["size"].setText(f"{size_kb/1024:.1f} KB" if size_kb >= 1024 else f"{size_kb:.1f} KB")
            widgets["original_info_labels"]["modified_date"].setText(original_info.get('modified_date', 'N/A'))
            widgets["original_markers_list"].clear()
            original_markers = self.format_markers_for_display(original_info.get('markers', []))
            widgets["original_markers_list"].addItems(original_markers or ["No markers found"])
        else:
            for label_key in ["duration", "size", "sample_rate", "bitrate", "channels", "modified_date"]: 
                widgets["original_info_labels"][label_key].setText("N/A")
            widgets["original_markers_list"].clear()
            widgets["original_markers_list"].addItem("File not available")

        if modified_info:
            formatted_modified = self.format_audio_info(modified_info)
            for key, label in widgets["modified_info_labels"].items():
                if key in formatted_modified: label.setText(formatted_modified[key])
            size_kb = modified_info['file_size'] / 1024
            size_text = f"{size_kb/1024:.1f} MB" if size_kb >= 1024 else f"{size_kb:.1f} KB"
            widgets["modified_info_labels"]["size"].setStyleSheet("")
            widgets["modified_info_labels"]["size"].setText(size_text)
            widgets["modified_info_labels"]["modified_date"].setText(modified_info.get('modified_date', 'N/A'))
            widgets["modified_markers_list"].clear()
            modified_markers = self.format_markers_for_display(modified_info.get('markers', []))
            widgets["modified_markers_list"].addItems(modified_markers or ["No markers found"])
        else:
            for label_key in ["duration", "size", "sample_rate", "bitrate", "channels", "modified_date"]:
                widgets["modified_info_labels"][label_key].setText("N/A")
                widgets["modified_info_labels"][label_key].setStyleSheet("")
            widgets["modified_markers_list"].clear()
            widgets["modified_markers_list"].addItem("No modified audio")

        for label in ["bnk_size", "override_fx"]:
            widgets["original_info_labels"][label].setText("<i>Loading...</i>")
            widgets["modified_info_labels"][label].setText("<i>Loading...</i>")
        
        if self.bnk_loader_thread and self.bnk_loader_thread.isRunning():
            self.bnk_loader_thread.terminate()
            self.bnk_loader_thread.wait()

        try:
            source_id = int(file_id)
        except (ValueError, TypeError):
            DEBUG.log(f"Invalid file_id for BNK search: {file_id}", "ERROR")
            for label in ["bnk_size", "override_fx"]:
                widgets["original_info_labels"][label].setText("<span style='color:red;'>Error</span>")
                widgets["modified_info_labels"][label].setText("<span style='color:red;'>Error</span>")
            return
            
        bnk_files_info = self.find_relevant_bnk_files() 
        
        self.bnk_loader_thread = BnkInfoLoader(self, source_id, bnk_files_info, self.mod_p_path, os.path.join(self.base_path, "Wems"))
        
        real_original_wem_size = original_info['file_size'] if original_info else 0
        real_modified_wem_size = modified_info['file_size'] if modified_info else 0

        self.bnk_loader_thread.info_loaded.connect(
            lambda sid, orig_info, mod_info: self.update_bnk_info_ui(
                request_id, sid, widgets, orig_info, mod_info, 
                real_original_wem_size, real_modified_wem_size
            )
        )

        self.bnk_loader_thread.start()

    def fix_bnk_size(self, file_id, lang, new_size):
        """Updates the BNK file with the correct WEM file size."""
        DEBUG.log(f"Attempting to fix BNK size for ID {file_id} in lang {lang} to new size {new_size}")
        
        try:
            source_id = int(file_id)
            bnk_fixed = False
            
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
                
                editor = BNKEditor(mod_bnk_path)
                
                if editor.modify_sound(source_id, new_size=new_size, find_by_size=None):
                    editor.save_file()
                    self.invalidate_bnk_cache(source_id)
                    
                    DEBUG.log(f"Successfully fixed size in {os.path.basename(mod_bnk_path)}.")
                    bnk_fixed = True
                    break

            if bnk_fixed:
                QtWidgets.QMessageBox.information(self, "Success", "BNK file size has been successfully updated!")
                self.on_selection_changed(lang)
            else:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not find an entry for ID {file_id} in any modded BNK file to fix.")
        
        except Exception as e:
            DEBUG.log(f"Error fixing BNK size: {e}", "ERROR")
            QtWidgets.QMessageBox.critical(self, "Error", f"An unexpected error occurred while fixing the BNK file:\n{str(e)}")

    def update_bnk_info_ui(self, request_id, source_id, widgets, original_bnk_info, modified_bnk_info, real_original_wem_size, real_modified_wem_size):
        if request_id != self.current_bnk_request_id:
            return

        try:
            widgets["original_info_labels"]["bnk_size"].isVisible()
        except RuntimeError:
            DEBUG.log("Widgets were deleted, BNK UI update cancelled.", "WARNING")
            return

        bnk_size_button = widgets["modified_info_labels"]["bnk_size"]
        
        try:
            bnk_size_button.clicked.disconnect()
        except TypeError:
            pass
        bnk_size_button.setEnabled(False)
        bnk_size_button.setCursor(QtCore.Qt.ArrowCursor)

        is_dark = self.settings.data.get("theme", "light") == "dark"
        text_color = "#d4d4d4" if is_dark else "#000000"  

        bnk_size_button.setStyleSheet(f"QPushButton {{ text-align: left; padding: 0; border: none; background: transparent; color: {text_color}; }}")

        if original_bnk_info:
            widgets["original_info_labels"]["bnk_size"].setText(f"{original_bnk_info.file_size / 1024:.1f} KB")
            fx_status = "Disabled" if original_bnk_info.override_fx else "Enabled"
            fx_color = "#F44336" if original_bnk_info.override_fx else "#4CAF50"
            widgets["original_info_labels"]["override_fx"].setText(f"<b style='color:{fx_color};'>{fx_status}</b>")
        else:
            widgets["original_info_labels"]["bnk_size"].setText("N/A")
            widgets["original_info_labels"]["override_fx"].setText("N/A")
            
        file_id = str(source_id)
        current_lang = self.get_current_language()
        
        mod_wem_exists = real_modified_wem_size > 0

        if modified_bnk_info:
            expected_bnk_size = modified_bnk_info.file_size
            
            if mod_wem_exists:
                actual_wem_size = real_modified_wem_size 
                
                if actual_wem_size == expected_bnk_size:
                    bnk_size_button.setText(f"{expected_bnk_size / 1024:.1f} KB")
                    bnk_size_button.setToolTip("OK: Actual file size matches the BNK record.")
            
                    bnk_size_button.setStyleSheet("QPushButton { text-align: left; padding: 0; border: none; color: green; font-weight: bold; background: transparent; }")
                else:
                    bnk_size_button.setText(f"Mismatch! Click to fix")
                    bnk_size_button.setToolTip(f"BNK expects {expected_bnk_size:,} bytes, but file is {actual_wem_size:,} bytes.\nClick to update the BNK record.")
               
                    bnk_size_button.setStyleSheet("QPushButton { text-align: left; padding: 0; border: none; color: red; font-weight: bold; text-decoration: underline; background: transparent; }")
                    bnk_size_button.setCursor(QtCore.Qt.PointingHandCursor)
                    bnk_size_button.setEnabled(True)
                    bnk_size_button.clicked.connect(lambda: self.fix_bnk_size(file_id, current_lang, actual_wem_size))
            else:
                if original_bnk_info and expected_bnk_size != original_bnk_info.file_size:
                    bnk_size_button.setText("Missing WEM! Click to revert")
                    bnk_size_button.setToolTip(f"BNK record was modified, but the WEM file is missing.\nClick to revert the BNK record to its original state.")
                 
                    bnk_size_button.setStyleSheet("QPushButton { text-align: left; padding: 0; border: none; color: red; font-weight: bold; text-decoration: underline; background: transparent; }")
                    bnk_size_button.setCursor(QtCore.Qt.PointingHandCursor)
                    bnk_size_button.setEnabled(True)
                    bnk_size_button.clicked.connect(lambda: self.revert_single_bnk_entry(file_id, current_lang))
                else:
            
                    bnk_size_button.setText(f"{expected_bnk_size / 1024:.1f} KB")
                    bnk_size_button.setStyleSheet(f"QPushButton {{ text-align: left; padding: 0; border: none; color: {text_color}; background: transparent; }}")

            fx_status = "Disabled" if modified_bnk_info.override_fx else "Enabled"
            fx_color = "#F44336" if modified_bnk_info.override_fx else "#4CAF50"
            widgets["modified_info_labels"]["override_fx"].setText(f"<b style='color:{fx_color};'>{fx_status}</b>")
        
        else:
            bnk_size_button.setText("N/A")
            widgets["modified_info_labels"]["override_fx"].setText("N/A")

    def revert_single_bnk_entry(self, file_id, lang):
        """Reverts BNK entry to original values in ALL matching BNK files."""
        DEBUG.log(f"Reverting BNK entries for ID {file_id}")
        try:
            source_id = int(file_id)
            reverted_count = 0
            
            bnk_files_info = self.find_relevant_bnk_files()

            for bnk_path, bnk_type in bnk_files_info:
               
                original_bnk = BNKEditor(bnk_path)
                original_entries = original_bnk.find_sound_by_source_id(source_id)
                if not original_entries:
                    continue
                
                original_entry = original_entries[0]

                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else:
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                
                if os.path.exists(mod_bnk_path):
                    mod_editor = BNKEditor(mod_bnk_path)
                    
                    if mod_editor.modify_sound(source_id, 
                                               new_size=original_entry.file_size, 
                                               override_fx=original_entry.override_fx):
                        mod_editor.save_file()
                        self.invalidate_bnk_cache(source_id)
                        reverted_count += 1
                        DEBUG.log(f"Reverted entry in {os.path.basename(mod_bnk_path)}")

            if reverted_count > 0:
                QtWidgets.QMessageBox.information(self, "Success", f"Reverted {reverted_count} BNK entries.")
                self.on_selection_changed(lang)
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "No BNK entries needed reverting.")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def get_file_durations(self, file_id, lang, widgets):

        wem_path = os.path.join(self.wem_root, lang, f"{file_id}.wem")
        self.original_duration = 0
        
        if os.path.exists(wem_path):
            duration = self.get_wem_duration(wem_path)
            if duration > 0:
                self.original_duration = duration
                minutes = int(duration // 60000)
                seconds = (duration % 60000) / 1000.0
                widgets["info_labels"]["duration"].setText(f"{minutes:02d}:{seconds:05.2f}")
            else:
                widgets["info_labels"]["duration"].setText("Unknown")
        else:
            widgets["info_labels"]["duration"].setText("N/A")
            

        mod_wem_path = self.get_mod_path(file_id, lang)
        self.mod_duration = 0
        
        if os.path.exists(mod_wem_path):
            duration = self.get_wem_duration(mod_wem_path)
            if duration > 0:
                self.mod_duration = duration
                minutes = int(duration // 60000)
                seconds = (duration % 60000) / 1000.0
                widgets["info_labels"]["mod_duration"].setText(f"{minutes:02d}:{seconds:05.2f}")
                
            else:
                widgets["info_labels"]["mod_duration"].setText("Unknown")
        else:
            widgets["info_labels"]["mod_duration"].setText("N/A")

    def get_wem_duration(self, wem_path):

        try:
            result = subprocess.run(
                [self.vgmstream_path, "-m", wem_path],
                capture_output=True,
                text=True,
                timeout=5,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                samples = None
                sample_rate = 48000 
                
                for line in result.stdout.split('\n'):
                    if "stream total samples:" in line:
                        samples = int(line.split(':')[1].strip().split()[0])
                    elif "sample rate:" in line:
                        sample_rate = int(line.split(':')[1].strip().split()[0])
                
                if samples:
                    duration_ms = int((samples / sample_rate) * 1000)
                    return duration_ms
                    
        except Exception as e:
            DEBUG.log(f"Error getting duration: {e}", "ERROR")
            
        return 0

    def get_file_size(self, file_id, lang, widgets):
   
        wem_path = os.path.join(self.wem_root, lang, f"{file_id}.wem")
        if os.path.exists(wem_path):
            self.original_size = os.path.getsize(wem_path)
            widgets["info_labels"]["size"].setText(f"{self.original_size / 1024:.1f} KB")
        else:
            self.original_size = 0
            widgets["info_labels"]["size"].setText("N/A")
            
        mod_wem_path = self.get_mod_path(file_id, lang)
        
        if os.path.exists(mod_wem_path):
            self.mod_size = os.path.getsize(mod_wem_path)
            widgets["info_labels"]["mod_size"].setText(f"{self.mod_size / 1024:.1f} KB")
            
            
        else:
            self.mod_size = 0
            widgets["info_labels"]["mod_size"].setText("N/A")
            widgets["size_warning"].hide()

    def play_current(self, play_mod=False):
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items or items[0].childCount() > 0:
            return
        self.stop_audio()    
        item = items[0]
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            return
            
        id_ = entry.get("Id", "")
        
        if play_mod:

            if current_lang != "SFX":
                wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", current_lang, f"{id_}.wem")
            else:
                wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", f"{id_}.wem")
          
            
            if not os.path.exists(wem_path):
             
                old_wem_path_lang = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", current_lang, f"{id_}.wem")
                old_wem_path_sfx = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{id_}.wem")
                
                if os.path.exists(old_wem_path_lang):
                    wem_path = old_wem_path_lang
                elif os.path.exists(old_wem_path_sfx):
                    wem_path = old_wem_path_sfx
                else:
                    self.status_bar.showMessage(f"Mod audio not found: {wem_path}", 3000)
                    DEBUG.log(f"Mod audio not found at: {wem_path}", "WARNING")
                    return
            self.is_playing_mod = True
        else:
      
            wem_path = self.get_original_path(id_, current_lang)
            
            if not os.path.exists(wem_path):
                self.status_bar.showMessage(f"File not found: {wem_path}", 3000)
                return
            self.is_playing_mod = False
            
        source_type = "MOD" if play_mod else "Original"
        self.status_bar.showMessage(f"Converting {source_type} to WAV...")
        QtWidgets.QApplication.processEvents()
        
        try:
            temp_file_handle = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav = temp_file_handle.name
            temp_file_handle.close()
            DEBUG.log(f"Generated unique temp WAV path: {temp_wav}")
        except Exception as e:
            DEBUG.log(f"Failed to create temp file: {e}", "ERROR")
            self.status_bar.showMessage("Error creating temporary file", 3000)
            return
        
        thread = threading.Thread(target=self._convert_and_play, args=(wem_path, temp_wav, current_lang))
        thread.start()

    def _convert_and_play(self, wem_path, wav_path, lang):
        ok, err = self.wem_to_wav_vgmstream(wem_path, wav_path)
        
        QtCore.QMetaObject.invokeMethod(self, "_play_converted", 
                                       QtCore.Qt.QueuedConnection,
                                       QtCore.Q_ARG(bool, ok),
                                       QtCore.Q_ARG(str, wav_path),
                                       QtCore.Q_ARG(str, err),
                                       QtCore.Q_ARG(str, lang))

    def update_audio_position(self, position, widgets):
        widgets["audio_progress"].setValue(position)
        self.update_time_label(widgets)

    def update_audio_duration(self, duration, widgets):
        widgets["audio_progress"].setMaximum(duration)
        self.update_time_label(widgets)

    def update_time_label(self, widgets):
        position = self.audio_player.player.position()
        duration = self.audio_player.player.duration()
        pos_min = position // 60000
        pos_sec = (position % 60000) / 1000
        pos_str = f"{pos_min:02d}:{pos_sec:06.3f}" 

        dur_min = duration // 60000
        dur_sec = (duration % 60000) / 1000
        dur_str = f"{dur_min:02d}:{dur_sec:06.3f}"

        source_type = " [MOD]" if self.is_playing_mod else ""
        
        time_text = f"{pos_str} / {dur_str} {source_type}"
        
        widgets["time_label"].setText(time_text)

    def stop_audio(self):
        self.audio_player.stop()
        if self.temp_wav and os.path.exists(self.temp_wav):
            try:
                os.remove(self.temp_wav)
            except:
                pass
        self.temp_wav = None
        self.is_playing_mod = False

    def edit_current_subtitle(self):
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
            
        shortname = entry.get("ShortName", "")
        key = os.path.splitext(shortname)[0]
        current_subtitle = self.subtitles.get(key, "")
        original_subtitle = self.original_subtitles.get(key, "")
        
        DEBUG.log(f"Editing subtitle for: {key} from main audio tab")
        
        editor = SubtitleEditor(self, key, current_subtitle, original_subtitle)
        if editor.exec_() == QtWidgets.QDialog.Accepted:
            new_subtitle = editor.get_text()
            self.subtitles[key] = new_subtitle
        
            if key in self.key_to_file_map:
                file_info = self.key_to_file_map[key]
                self.dirty_subtitle_files.add(file_info['path'])
                DEBUG.log(f"Marked file as dirty from main tab edit: {file_info['path']}")

            if new_subtitle != original_subtitle:
                self.modified_subtitles.add(key)
            else:
                self.modified_subtitles.discard(key)
            
            try:
                if not self.is_item_deleted(item):
                    item.setText(2, new_subtitle)
                    current_status = item.text(3).replace("✓", "")
                    if key in self.modified_subtitles:
                        item.setText(3, "✓" + current_status)
                    else:
                        item.setText(3, current_status)
                    
                    widgets["subtitle_text"].setPlainText(new_subtitle)
                    if original_subtitle and original_subtitle != new_subtitle:
                        widgets["original_subtitle_label"].setText(f"{self.tr('original')}: {original_subtitle}")
                        widgets["original_subtitle_label"].show()
                    else:
                        widgets["original_subtitle_label"].hide()
            except RuntimeError:
                DEBUG.log("Item was deleted during update from main tab, refreshing tree.", "WARNING")
                self.populate_tree(current_lang)

            self.status_bar.showMessage("Subtitle updated", 2000)
            self.update_status()

    def find_tree_item_by_key(self, tree, target_key, target_entry):

        def search_items(parent_item):
            for i in range(parent_item.childCount()):
                item = parent_item.child(i)
                
                if item.childCount() == 0: 
                    try:
                        entry = item.data(0, QtCore.Qt.UserRole)
                        if entry:
                            shortname = entry.get("ShortName", "")
                            key = os.path.splitext(shortname)[0]
                            
                            if key == target_key:
                                return item
                    except RuntimeError:
                  
                        continue
                else:
           
                    result = search_items(item)
                    if result:
                        return result
            return None
        
        try:
            root = tree.invisibleRootItem()
            return search_items(root)
        except RuntimeError:
            return None

    def is_item_deleted(self, item):
        """Check if QTreeWidgetItem is still valid"""
        try:
 
            _ = item.text(0)
            return False
        except RuntimeError:
            return True

    def revert_subtitle(self):
        """Revert selected subtitle to original"""
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
            
        shortname = entry.get("ShortName", "")
        key = os.path.splitext(shortname)[0]
        
        if key in self.original_subtitles:
            original = self.original_subtitles[key]
            self.subtitles[key] = original
            self.modified_subtitles.discard(key)
            

            item.setText(2, original)
            current_status = item.text(3).replace("✓", "")
            item.setText(3, current_status)
            
            widgets["subtitle_text"].setPlainText(original)
            widgets["original_subtitle_label"].hide()
            
            self.status_bar.showMessage("Subtitle reverted to original", 2000)
            self.update_status()

    def import_custom_subtitles(self):
        """Import custom subtitles from another locres file"""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, self.tr("import_custom_subtitles"), "", "Locres Files (*.locres)"
        )
        
        if not path:
            return
            
        DEBUG.log(f"Importing custom subtitles from: {path}")
        
        try:

            custom_subtitles = self.locres_manager.export_locres(path)
            
            if not custom_subtitles:
                QtWidgets.QMessageBox.warning(self, "Import Error", "No subtitles found in the selected file")
                return
                
            DEBUG.log(f"Found {len(custom_subtitles)} subtitles in custom file")
            
            conflicts = {}
            for key, new_value in custom_subtitles.items():
                if key in self.subtitles and self.subtitles[key]:
                    conflicts[key] = {
                        "existing": self.subtitles[key],
                        "new": new_value
                    }
            
            if conflicts:

                conflict_list = []
                for key, values in list(conflicts.items())[:10]: 
                    conflict_list.append(f"{key}:\n  Existing: {values['existing'][:50]}...\n  New: {values['new'][:50]}...")
                
                if len(conflicts) > 10:
                    conflict_list.append(f"\n... and {len(conflicts) - 10} more conflicts")
                
                msg = QtWidgets.QMessageBox()
                msg.setWindowTitle(self.tr("conflict_detected"))
                msg.setText(self.tr("conflict_message").format(conflicts="\n\n".join(conflict_list)))
                
                use_existing_btn = msg.addButton(self.tr("use_existing"), QtWidgets.QMessageBox.ActionRole)
                use_new_btn = msg.addButton(self.tr("use_new"), QtWidgets.QMessageBox.ActionRole)
                merge_btn = msg.addButton(self.tr("merge_all"), QtWidgets.QMessageBox.ActionRole)
                msg.addButton(QtWidgets.QMessageBox.Cancel)
                
                msg.exec_()
                
                if msg.clickedButton() == use_existing_btn:

                    for key, value in custom_subtitles.items():
                        if key not in self.subtitles or not self.subtitles[key]:
                            self.subtitles[key] = value
                            if key not in self.original_subtitles:
                                self.original_subtitles[key] = ""
                            self.modified_subtitles.add(key)
                elif msg.clickedButton() == use_new_btn:

                    for key, value in custom_subtitles.items():
                        self.subtitles[key] = value
                        if key not in self.original_subtitles:
                            self.original_subtitles[key] = ""
                        if value != self.original_subtitles.get(key, ""):
                            self.modified_subtitles.add(key)
                elif msg.clickedButton() == merge_btn:

                    for key, value in custom_subtitles.items():
                        if key not in self.subtitles or not self.subtitles[key]:
                            self.subtitles[key] = value
                            if key not in self.original_subtitles:
                                self.original_subtitles[key] = ""
                            self.modified_subtitles.add(key)
                else:
                    return  
            else:
                
                for key, value in custom_subtitles.items():
                    self.subtitles[key] = value
                    if key not in self.original_subtitles:
                        self.original_subtitles[key] = ""
                    if value != self.original_subtitles.get(key, ""):
                        self.modified_subtitles.add(key)
            
            current_lang = self.get_current_language()
            if current_lang and current_lang in self.tab_widgets:
                self.populate_tree(current_lang)
                
            self.update_status()
            self.status_bar.showMessage(f"Imported {len(custom_subtitles)} subtitles", 3000)
            
        except Exception as e:
            DEBUG.log(f"Error importing custom subtitles: {str(e)}", "ERROR")
            QtWidgets.QMessageBox.warning(self, "Import Error", str(e))

    def deploy_and_run_game(self):
        """Deploy mod to game and run it"""
        game_path = self.settings.data.get("game_path", "")
        
        if not game_path or not os.path.exists(game_path):
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("no_game_path"))
            return
            
        mod_file = f"{self.mod_p_path}.pak"
        
        if not os.path.exists(mod_file):
            reply = QtWidgets.QMessageBox.question(
                self, self.tr("compile_mod"), 
                self.tr("mod_not_found_compile"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self.compile_mod()
                
                import time
                for i in range(10):
                    if os.path.exists(mod_file):
                        break
                    time.sleep(1)
                    
                if not os.path.exists(mod_file):
                    QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("mod_compilation_failed"))
                    return
            else:
                return
        

        try:
            paks_path = os.path.join(game_path, "OPP", "Content", "Paks")
            os.makedirs(paks_path, exist_ok=True)
            
            target_mod_path = os.path.join(paks_path, os.path.basename(mod_file))
            
            DEBUG.log(f"Deploying mod from {mod_file} to {target_mod_path}")
            shutil.copy2(mod_file, target_mod_path)
            
            self.status_bar.showMessage(self.tr("mod_deployed"), 3000)
            
            exe_files = []
            for file in os.listdir(game_path):
                if file.endswith(".exe") and "Shipping" in file:
                    exe_files.append(file)
                    
            if not exe_files:

                for file in os.listdir(game_path):
                    if file.endswith(".exe"):
                        exe_files.append(file)
                        
            if exe_files:
                game_exe = os.path.join(game_path, exe_files[0])
                DEBUG.log(f"Launching game: {game_exe}")
                self.status_bar.showMessage(self.tr("game_launching"), 3000)
                subprocess.Popen(
                    [game_exe],
                    startupinfo=startupinfo,
                    creationflags=CREATE_NO_WINDOW
                )
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Game executable not found")
                
        except Exception as e:
            DEBUG.log(f"Error deploying mod: {str(e)}", "ERROR")
            QtWidgets.QMessageBox.warning(self, "Error", str(e))

    def export_subtitles_for_game(self):
        """Export modified subtitles to game mod structure with language filtering"""
        DEBUG.log("=== Export Subtitles for Game (Fixed Language Filter) ===")
        
        if not self.modified_subtitles:
            QtWidgets.QMessageBox.information(self, "No Changes", "No modified subtitles to export")
            return
        
        current_language = self.settings.data["subtitle_lang"]
        DEBUG.log(f"Exporting for language: {current_language}")
        
        progress = ProgressDialog(self, "Exporting Subtitles for Game")
        progress.show()
        

        self.subtitle_export_status.clear()
        self.subtitle_export_status.append("=== Starting Export ===")
        self.subtitle_export_status.append(f"Language: {current_language}")
        self.subtitle_export_status.append(f"Modified subtitles: {len(self.modified_subtitles)}")
        self.subtitle_export_status.append("")
        
        try:
            exported_files = 0
            
            subtitle_files_to_update = {}
            
            for modified_key in self.modified_subtitles:
                found_in_file = None
                
                for file_key, file_info in self.all_subtitle_files.items():
                    if file_info['language'] != current_language:
                        continue
                        
                    working_path = file_info['path'].replace('.locres', '_working.locres')
                    check_path = working_path if os.path.exists(working_path) else file_info['path']
                    
                    file_subtitles = self.locres_manager.export_locres(check_path)
                    if modified_key in file_subtitles:
                        found_in_file = file_info
                        break
                
                if found_in_file:
                    file_path = found_in_file['path']
                    if file_path not in subtitle_files_to_update:
                        working_path = file_path.replace('.locres', '_working.locres')
                        source_path = working_path if os.path.exists(working_path) else file_path
                        
                        subtitle_files_to_update[file_path] = {
                            'file_info': found_in_file,
                            'all_subtitles': self.locres_manager.export_locres(source_path),
                            'working_path': working_path
                        }

                    subtitle_files_to_update[file_path]['all_subtitles'][modified_key] = self.subtitles[modified_key]
                else:
                    DEBUG.log(f"Warning: Could not find source file for modified key: {modified_key}", "WARNING")
            
            DEBUG.log(f"Found {len(subtitle_files_to_update)} files to save for language {current_language}")
            
            if not subtitle_files_to_update:
                QtWidgets.QMessageBox.warning(
                    self, "Export Error", 
                    f"No subtitle files found for language '{current_language}'.\n"
                    f"Please check that you have the correct subtitle files in your Localization folder."
                )
                progress.close()
                return

            for i, (file_path, data) in enumerate(subtitle_files_to_update.items()):
                file_info = data['file_info']
                all_subtitles = data['all_subtitles']
                
                progress.set_progress(
                    int((i / len(subtitle_files_to_update)) * 100),
                    f"Processing {file_info['filename']} ({current_language})..."
                )
                
                target_dir = os.path.join(
                    self.mod_p_path, "OPP", "Content", 
                    "Localization", file_info['category'], current_language
                )
                os.makedirs(target_dir, exist_ok=True)
                
                target_file = os.path.join(target_dir, file_info['filename'])
                
                DEBUG.log(f"Exporting to: {target_file}")
                
                shutil.copy2(file_path, target_file)
                
                modified_subs = {k: v for k, v in all_subtitles.items() if k in self.modified_subtitles}
                
             
                success = self.locres_manager.import_locres(target_file, all_subtitles)
                
                if success:
                    exported_files += 1
                    self.subtitle_export_status.append(f"✓ {file_info['relative_path']} ({len(modified_subs)} subtitles)")
                    DEBUG.log(f"Successfully exported {file_info['filename']} with {len(modified_subs)} modified subtitles")
                else:
                    self.subtitle_export_status.append(f"✗ {file_info['relative_path']} - FAILED")
                    DEBUG.log(f"Failed to export {file_info['filename']}", "ERROR")
            
            progress.set_progress(100, "Export complete!")
            
            self.subtitle_export_status.append("")
            self.subtitle_export_status.append("=== Export Complete ===")
            self.subtitle_export_status.append(f"Files exported: {exported_files}")
            self.subtitle_export_status.append(f"Location: {os.path.join(self.mod_p_path, 'OPP', 'Content', 'Localization')}")
            
            QtWidgets.QMessageBox.information(
                self, "Success", 
                f"Subtitles exported successfully!\n\n"
                f"Language: {current_language}\n"
                f"Files exported: {exported_files}\n"
                f"Modified subtitles: {len(self.modified_subtitles)}\n\n"
                f"Location: {os.path.join(self.mod_p_path, 'OPP', 'Content', 'Localization')}"
            )
            
        except Exception as e:
            DEBUG.log(f"Export error: {str(e)}", "ERROR")
            self.subtitle_export_status.append(f"ERROR: {str(e)}")
            QtWidgets.QMessageBox.warning(self, "Export Error", str(e))
            
        progress.close()
        DEBUG.log("=== Export Complete ===")

    def save_current_wav(self):
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items:
            return

        if len(items) > 1:
            self.batch_export_wav(items, current_lang)
            return
            
        item = items[0]
        if item.childCount() > 0:
            return
            
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            return
            
        id_ = entry.get("Id", "")
        shortname = entry.get("ShortName", "")

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(self.tr("export_audio"))
        msg.setText(self.tr("which_version_export"))
        
        original_btn = msg.addButton(self.tr("original"), QtWidgets.QMessageBox.ActionRole)
        mod_btn = None
        
        mod_wem_path = self.get_mod_path(id_, current_lang)
        if mod_wem_path and os.path.exists(mod_wem_path):
            mod_btn = msg.addButton(self.tr("mod"), QtWidgets.QMessageBox.ActionRole)
            
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        self.show_dialog(msg)
        
        clicked_button = msg.clickedButton()
        wem_path = None

        if clicked_button == original_btn:
            wem_path = self.get_original_path(id_, current_lang)
        elif mod_btn and clicked_button == mod_btn:
            wem_path = mod_wem_path
        else:
            return
            
        if not wem_path or not os.path.exists(wem_path):
            self.status_bar.showMessage(f"Source file not found: {wem_path}", 3000)
            return
            
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("save_as_wav"), shortname, 
            f"{self.tr('wav_files')} (*.wav)"
        )
        
        if save_path:
            if os.path.exists(save_path):
                reply = self.show_message_box(
                    QtWidgets.QMessageBox.Question,
                    "File Exists",
                    f"The file '{os.path.basename(save_path)}' already exists.",
                    "Do you want to overwrite it?",
                    buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.No:
                    return

            progress = ProgressDialog(self, f"Exporting {shortname}...")
            progress.show()
            progress.raise_()
            progress.activateWindow()

            thread = threading.Thread(
                target=self._export_single_wav_thread, 
                args=(wem_path, save_path, progress)
            )
            thread.daemon = True
            thread.start()

    def _export_single_wav_thread(self, wem_path, save_path, progress_dialog):
        try:
            ok, err = self.wem_to_wav_vgmstream(wem_path, save_path)
            
            QtCore.QMetaObject.invokeMethod(
                self, "_on_single_export_finished", QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, ok),
                QtCore.Q_ARG(str, save_path),
                QtCore.Q_ARG(str, err),
                QtCore.Q_ARG(object, progress_dialog)
            )
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(
                self, "_on_single_export_finished", QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, False),
                QtCore.Q_ARG(str, save_path),
                QtCore.Q_ARG(str, str(e)),
                QtCore.Q_ARG(object, progress_dialog)
            )

    def wem_to_wav_vgmstream(self, wem_path, wav_path):
        try:
            result = subprocess.run(
                [self.vgmstream_path, wem_path, "-o", wav_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stderr.decode()
        except Exception as e:
            return False, str(e)

    def toggle_ingame_effects(self):
        current_lang = self.get_current_language()
        if not current_lang:
            return

        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        file_items = [item for item in tree.selectedItems() if item.childCount() == 0]

        if not file_items:
            return

        bnk_files = self.find_relevant_bnk_files()
        if not bnk_files:
            QtWidgets.QMessageBox.warning(self, "Error", "No BNK files found for modification.")
            return
            
        modified_count = 0
        for item in file_items:
            entry = item.data(0, QtCore.Qt.UserRole)
            if not entry:
                continue

            source_id = int(entry.get("Id", ""))
            shortname = entry.get("ShortName", "")
            
            bnk_files_info = self.find_relevant_bnk_files()
            for bnk_path, bnk_type in bnk_files_info:
                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else: # 'lang'
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)

                original_editor = BNKEditor(bnk_path)
                if not original_editor.find_sound_by_source_id(source_id):
                    continue 

                if not os.path.exists(mod_bnk_path):
                    os.makedirs(os.path.dirname(mod_bnk_path), exist_ok=True)
                    shutil.copy2(bnk_path, mod_bnk_path)
                
                editor = BNKEditor(mod_bnk_path)
                current_entries = editor.find_sound_by_source_id(source_id)

                if current_entries:
                    current_state = current_entries[0].override_fx
                    new_state = not current_state
                    
                    if editor.modify_sound(source_id, override_fx=new_state, find_by_size=None):
                        editor.save_file()
                        self.invalidate_bnk_cache(source_id)
                        DEBUG.log(f"FX for {shortname} (ID: {source_id}) changed from {current_state} to {new_state} in {os.path.basename(mod_bnk_path)}")
                        modified_count += 1
                        bnk_found_and_modified = True
                        break 
            
            if not bnk_found_and_modified:
                DEBUG.log(f"Could not find or modify record for {shortname} (ID: {source_id}) in any BNK file.", "WARNING")

        self.populate_tree(current_lang)
        self.status_bar.showMessage(f"In-Game Effects changed for {modified_count} files.", 3000)
