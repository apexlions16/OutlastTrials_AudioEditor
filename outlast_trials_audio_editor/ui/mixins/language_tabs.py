from ._imports import *

class LanguageTabsMixin:
    def create_language_tab(self, lang):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        
        
        controls = QtWidgets.QWidget()
        controls.setMaximumHeight(40)
        controls_layout = QtWidgets.QHBoxLayout(controls)
        controls_layout.setContentsMargins(5, 5, 5, 5)

        filter_combo = QtWidgets.QComboBox()
        filter_combo.addItems([
            self.tr("all_files"), 
            self.tr("with_subtitles"), 
            self.tr("without_subtitles"), 
            self.tr("modified"),
            self.tr("modded")
        ])
        filter_combo.currentIndexChanged.connect(lambda: self.populate_tree(lang))

        sort_combo = QtWidgets.QComboBox()
        sort_combo.addItems([
            self.tr("name_a_z"), 
            self.tr("name_z_a"), 
            self.tr("id_asc"), 
            self.tr("id_desc"), 
            self.tr("recent_first")
        ])
        sort_combo.currentIndexChanged.connect(lambda: self.populate_tree(lang))
        show_orphans_checkbox = QtWidgets.QCheckBox(self.tr("show_scanned_files_check"))
        show_orphans_checkbox.setToolTip(self.tr("show_scanned_files_tooltip"))
        show_orphans_checkbox.setChecked(self.settings.data.get("show_orphaned_files", False))
        show_orphans_checkbox.stateChanged.connect(self.on_show_orphans_toggled)
        controls_layout.addWidget(QtWidgets.QLabel(self.tr("filter")))
        controls_layout.addWidget(filter_combo)
        controls_layout.addWidget(QtWidgets.QLabel(self.tr("sort")))
        controls_layout.addWidget(sort_combo)
        controls_layout.addWidget(show_orphans_checkbox)
        controls_layout.addStretch()

        stats_label = QtWidgets.QLabel()
        controls_layout.addWidget(stats_label)
        
        layout.addWidget(controls)
        
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        tree = AudioTreeWidget(wem_app=self, lang=lang)
        tree.setUniformRowHeights(True)
        tree.setAcceptDrops(True)
        tree.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
        tree.viewport().setAcceptDrops(True)
        tree.setColumnCount(5) 
        tree.setHeaderLabels([self.tr("name"), self.tr("id"), self.tr("subtitle"), self.tr("status"), "Tag"])
        tree.setColumnWidth(0, 350)
        tree.setColumnWidth(1, 100)
        tree.setColumnWidth(2, 400)
        tree.setColumnWidth(3, 80)
        tree.setColumnWidth(4, 100)
        tree.setAlternatingRowColors(True)
        tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(lambda pos: self.show_context_menu(lang, pos))
        tree.itemSelectionChanged.connect(lambda: self.on_selection_changed(lang))
        tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        splitter.addWidget(tree)
        

        details_panel = QtWidgets.QWidget()
        details_layout = QtWidgets.QVBoxLayout(details_panel)
        

        player_widget = QtWidgets.QWidget()
        player_layout = QtWidgets.QVBoxLayout(player_widget)
        

        audio_progress = ClickableProgressBar()
        audio_progress.setTextVisible(False)
        audio_progress.setMaximumHeight(10)
        player_layout.addWidget(audio_progress)
        

        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        

        play_btn = QtWidgets.QPushButton("▶")
        play_btn.setMaximumWidth(40)
        play_btn.clicked.connect(lambda: self.play_current())
        audio_progress.clicked.connect(self.audio_player.set_position)
        play_mod_btn = QtWidgets.QPushButton(f"▶ {self.tr('mod')}")
        play_mod_btn.setMaximumWidth(60)
        play_mod_btn.setToolTip("Play modified audio if available")
        play_mod_btn.clicked.connect(lambda: self.play_current(play_mod=True))
        play_mod_btn.hide()  
        
        stop_btn = QtWidgets.QPushButton("■")
        stop_btn.setMaximumWidth(40)
        stop_btn.clicked.connect(self.stop_audio)
        

        time_label = QtWidgets.QLabel("00:00 / 00:00")
        time_label.setAlignment(QtCore.Qt.AlignCenter)
        

        size_warning = QtWidgets.QLabel()
        size_warning.setStyleSheet("color: red; font-weight: bold;")
        size_warning.hide()
        
        controls_layout.addWidget(play_btn)
        controls_layout.addWidget(play_mod_btn)
        controls_layout.addWidget(stop_btn)
        controls_layout.addWidget(time_label)
        controls_layout.addWidget(size_warning)
        controls_layout.addStretch()
        
        player_layout.addWidget(controls_widget)
        details_layout.addWidget(player_widget)
        

        subtitle_group = QtWidgets.QGroupBox(self.tr("subtitle_preview"))
        subtitle_layout = QtWidgets.QVBoxLayout(subtitle_group)
        subtitle_group.setMaximumHeight(150)
        subtitle_group.setMaximumWidth(800)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(80) 
        scroll_area.setMaximumHeight(150) 

        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)

        subtitle_text = QtWidgets.QTextEdit()
        subtitle_text.setReadOnly(True)
        subtitle_text.setMinimumHeight(60)
        scroll_layout.addWidget(subtitle_text)

        original_subtitle_label = QtWidgets.QLabel()
        original_subtitle_label.setWordWrap(True)
        original_subtitle_label.setStyleSheet("color: #666; font-style: italic;")
        original_subtitle_label.hide()
        scroll_layout.addWidget(original_subtitle_label)

        scroll_layout.addStretch() 

        scroll_area.setWidget(scroll_content)
        subtitle_layout.addWidget(scroll_area)
        

        original_subtitle_label = QtWidgets.QLabel()
        original_subtitle_label.setWordWrap(True)
        original_subtitle_label.setStyleSheet("color: #666; font-style: italic;")
        original_subtitle_label.hide()
        subtitle_layout.addWidget(original_subtitle_label)
        
        details_layout.addWidget(subtitle_group)
        

        info_group = QtWidgets.QGroupBox(self.tr("file_info"))
        info_layout = QtWidgets.QVBoxLayout(info_group)

        basic_info_widget = QtWidgets.QWidget()
        basic_info_layout = QtWidgets.QFormLayout(basic_info_widget)

        info_labels = {
            "id": QtWidgets.QLabel(),
            "name": QtWidgets.QLabel(),
            "path": QtWidgets.QLabel(),
            "source": QtWidgets.QLabel(),
            "tag": QtWidgets.QLabel()
        }

        basic_info_layout.addRow(f"{self.tr('id')}:", info_labels["id"])
        basic_info_layout.addRow(f"{self.tr('name')}:", info_labels["name"])
        basic_info_layout.addRow(f"{self.tr('path')}:", info_labels["path"])
        basic_info_layout.addRow(f"{self.tr('source')}:", info_labels["source"])
        info_layout.addWidget(basic_info_widget)


        comparison_group = QtWidgets.QGroupBox(self.tr("audio_comparison"))
        comparison_group.setMaximumHeight(220) 
        comparison_group.setMinimumHeight(220) 
        comparison_layout = QtWidgets.QHBoxLayout(comparison_group)

      
        original_widget = QtWidgets.QWidget()
        original_layout = QtWidgets.QVBoxLayout(original_widget)
        original_header = QtWidgets.QLabel(self.tr("original_audio"))
        original_header.setStyleSheet("font-weight: bold; color: #2196F3; padding: 5px;")
        original_layout.addWidget(original_header)

        original_info_layout = QtWidgets.QFormLayout()
        original_info_labels = {
            "duration": QtWidgets.QLabel(),
            "size": QtWidgets.QLabel(),
            "sample_rate": QtWidgets.QLabel(),
            "bitrate": QtWidgets.QLabel(),
            "channels": QtWidgets.QLabel(),
            "bnk_size": QtWidgets.QLabel(),
            "override_fx": QtWidgets.QLabel(),
            "modified_date": QtWidgets.QLabel()
        }

        original_info_layout.addRow(self.tr("duration"), original_info_labels["duration"])
        original_info_layout.addRow(self.tr("size"), original_info_labels["size"])
        original_info_layout.addRow(self.tr("sample_rate"), original_info_labels["sample_rate"])
        original_info_layout.addRow(self.tr("bitrate"), original_info_labels["bitrate"])
        original_info_layout.addRow(self.tr("channels"), original_info_labels["channels"])
        original_info_layout.addRow(self.tr("bnk_size_label"), original_info_labels["bnk_size"])
        original_info_layout.addRow(self.tr("in_game_effects_label"), original_info_labels["override_fx"])
        original_info_layout.addRow(" ", QtWidgets.QWidget())
        original_layout.addLayout(original_info_layout)

     
        modified_widget = QtWidgets.QWidget()
        modified_layout = QtWidgets.QVBoxLayout(modified_widget)
        modified_header = QtWidgets.QLabel(self.tr("modified_audio"))
        modified_header.setStyleSheet("font-weight: bold; color: #4CAF50; padding: 5px;")
        modified_layout.addWidget(modified_header)

        modified_info_layout = QtWidgets.QFormLayout()
        modified_info_labels = {
            "duration": QtWidgets.QLabel(),
            "size": QtWidgets.QLabel(),
            "sample_rate": QtWidgets.QLabel(),
            "bitrate": QtWidgets.QLabel(),
            "channels": QtWidgets.QLabel(), 
            "bnk_size": QtWidgets.QPushButton("N/A"),
            "override_fx": QtWidgets.QLabel(),
            "modified_date": QtWidgets.QLabel()
        }

        modified_info_layout.addRow(f"{self.tr("duration")}", modified_info_labels["duration"])
        modified_info_layout.addRow(f"{self.tr("size")}", modified_info_labels["size"])
        modified_info_layout.addRow(f"{self.tr("sample_rate")}", modified_info_labels["sample_rate"])
        modified_info_layout.addRow(f"{self.tr("bitrate")}", modified_info_labels["bitrate"])
        modified_info_layout.addRow(f"{self.tr("channels")}", modified_info_labels["channels"])
        modified_info_layout.addRow(self.tr("bnk_size_label"), modified_info_labels["bnk_size"])
        modified_info_layout.addRow(self.tr("in_game_effects_label"), modified_info_labels["override_fx"]),
        modified_info_layout.addRow(self.tr("last_modified_label"), modified_info_labels["modified_date"])
        modified_layout.addLayout(modified_info_layout)
        bnk_size_button = modified_info_labels["bnk_size"]
        bnk_size_button.setFlat(True)
        bnk_size_button.setStyleSheet("QPushButton { text-align: left; padding: 0; color: #000; border: none; background: transparent; }")
        bnk_size_button.setCursor(QtCore.Qt.ArrowCursor)
        bnk_size_button.setEnabled(False)
     
        comparison_layout.addWidget(original_widget)

   
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #cccccc; }")
        comparison_layout.addWidget(separator)

        comparison_layout.addWidget(modified_widget)

        info_layout.addWidget(comparison_group)


        markers_group = QtWidgets.QGroupBox(self.tr("audio_markers"))
        markers_layout = QtWidgets.QVBoxLayout(markers_group)

 
        markers_comparison = QtWidgets.QHBoxLayout()


        original_markers_widget = QtWidgets.QWidget()
        original_markers_layout = QtWidgets.QVBoxLayout(original_markers_widget)

        original_markers_header = QtWidgets.QLabel(self.tr("original_markers"))
        original_markers_header.setStyleSheet("font-weight: bold; color: #2196F3; padding: 2px;")
        original_markers_layout.addWidget(original_markers_header)

        original_markers_list = QtWidgets.QListWidget()
        original_markers_list.setMaximumHeight(120)
        original_markers_list.setAlternatingRowColors(True)
        original_markers_layout.addWidget(original_markers_list)


        modified_markers_widget = QtWidgets.QWidget()
        modified_markers_layout = QtWidgets.QVBoxLayout(modified_markers_widget)

        modified_markers_header = QtWidgets.QLabel(self.tr("modified_markers"))
        modified_markers_header.setStyleSheet("font-weight: bold; color: #4CAF50; padding: 2px;")
        modified_markers_layout.addWidget(modified_markers_header)

        modified_markers_list = QtWidgets.QListWidget()
        modified_markers_list.setMaximumHeight(120)
        modified_markers_list.setAlternatingRowColors(True)
        modified_markers_layout.addWidget(modified_markers_list)

        markers_comparison.addWidget(original_markers_widget)

 
        markers_separator = QtWidgets.QFrame()
        markers_separator.setFrameShape(QtWidgets.QFrame.VLine)
        markers_separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        markers_separator.setStyleSheet("QFrame { color: #cccccc; }")
        markers_comparison.addWidget(markers_separator)

        markers_comparison.addWidget(modified_markers_widget)

        markers_layout.addLayout(markers_comparison)
        info_layout.addWidget(markers_group)

        details_layout.addWidget(info_group)
        details_layout.addStretch()
        
        splitter.addWidget(details_panel)
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)
        

        self.tab_widgets[lang] = {
            "filter_combo": filter_combo,
            "show_orphans_checkbox": show_orphans_checkbox,
            "sort_combo": sort_combo,
            "tree": tree,
            "stats_label": stats_label,
            "subtitle_text": subtitle_text,
            "original_subtitle_label": original_subtitle_label,
            "info_labels": info_labels,
            "original_info_labels": original_info_labels,
            "modified_info_labels": modified_info_labels,
            "original_markers_list": original_markers_list,
            "modified_markers_list": modified_markers_list,
            "details_panel": details_panel,
            "audio_progress": audio_progress,
            "time_label": time_label,
            "play_btn": play_btn,
            "play_mod_btn": play_mod_btn,
            "stop_btn": stop_btn,
            "size_warning": size_warning
        }
        
        self.tabs.addTab(tab, f"{lang} ({len(self.entries_by_lang.get(lang, []))})")
        basic_info_layout.addRow("Tag:", info_labels["tag"])

    def on_show_orphans_toggled(self, state):
        """Handles toggling the 'Show Scanned Files' checkbox."""
        is_checked = (state == QtCore.Qt.Checked)
        
        if self.settings.data.get("show_orphaned_files", True) == is_checked:
            return
        
        self.settings.data["show_orphaned_files"] = is_checked
        self.settings.save()
        DEBUG.log(f"Show orphaned files setting changed to: {is_checked}")

        for lang, widgets in self.tab_widgets.items():
            checkbox = widgets.get("show_orphans_checkbox")
            if checkbox:
                checkbox.blockSignals(True)
                checkbox.setChecked(is_checked)
                checkbox.blockSignals(False)

        self.rebuild_file_list_with_orphans()

    def get_wem_audio_info_with_markers(self, wem_path):
        """Get detailed audio information including markers from WEM file"""
        info = self.get_wem_audio_info(wem_path)
        
        if info is None:
            return None
        

        try:
            analyzer = WEMAnalyzer(wem_path)
            if analyzer.analyze():
                info['markers'] = analyzer.get_markers_info()
       
                if analyzer.sample_rate > 0:
                    info['sample_rate'] = analyzer.sample_rate
            else:
                info['markers'] = []
        except Exception as e:
            DEBUG.log(f"Error analyzing markers: {e}", "ERROR")
            info['markers'] = []
        
        return info

    def format_markers_for_display(self, markers):

        formatted_markers = []
        
        for marker in markers:
   
            if marker['position'] == 0:
                time_str = "Sample 0"
            else:
    
                time_seconds = marker['time_seconds']
                if time_seconds >= 1.0:

                    minutes = int(time_seconds // 60)
                    seconds = time_seconds % 60
                    time_str = f"{minutes:02d}:{seconds:06.3f}"
                else:

                    time_str = f"{time_seconds:.3f}s"
            

            label = marker['label']
            
    
            if label and label != "No label":
                display_text = f"#{marker['id']}: {time_str} - {label}"
            else:
                display_text = f"#{marker['id']}: {time_str}"
            
            formatted_markers.append(display_text)
        
        return formatted_markers

    def get_wem_audio_info(self, wem_path):
        """Get detailed audio information from WEM file"""
        try:
            result = subprocess.run(
                [self.vgmstream_path, "-m", wem_path],
                capture_output=True,
                text=True,
                timeout=10,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                info = {
                    'sample_rate': 0,
                    'channels': 0,
                    'samples': 0,
                    'duration_ms': 0,
                    'bitrate': 0,
                    'format': 'Unknown'
                }
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    
                    if "sample rate:" in line:
                        try:
                            info['sample_rate'] = int(line.split(':')[1].strip().split()[0])
                        except:
                            pass
                            
                    elif "channels:" in line:
                        try:
                            info['channels'] = int(line.split(':')[1].strip().split()[0])
                        except:
                            pass
                            
                    elif "stream total samples:" in line:
                        try:
                            info['samples'] = int(line.split(':')[1].strip().split()[0])
                        except:
                            pass
                            
                    elif "encoding:" in line:
                        try:
                            info['format'] = line.split(':')[1].strip()
                        except:
                            pass
                

                if info['sample_rate'] > 0 and info['samples'] > 0:
                    info['duration_ms'] = int((info['samples'] / info['sample_rate']) * 1000)
                    

                    file_size = os.path.getsize(wem_path)
                    if info['duration_ms'] > 0:
                        info['bitrate'] = int((file_size * 8) / (info['duration_ms'] / 1000))
                
                return info
                
        except Exception as e:
            DEBUG.log(f"Error getting audio info: {e}", "ERROR")
            
        return None

    def format_audio_info(self, info, label_suffix=""):
        """Format audio info for display"""
        if not info:
            return {
                f'duration{label_suffix}': "N/A",
                f'size{label_suffix}': "N/A", 
                f'sample_rate{label_suffix}': "N/A",
                f'bitrate{label_suffix}': "N/A",
                f'channels{label_suffix}': "N/A"
            }
        
        # Format duration
        duration_ms = info.get('duration_ms', 0)
        if duration_ms > 0:
            minutes = int(duration_ms // 60000)
            seconds = (duration_ms % 60000) / 1000.0
            duration_str = f"{minutes:02d}:{seconds:05.2f}"
        else:
            duration_str = "Unknown"
        
        # Format sample rate
        sample_rate = info.get('sample_rate', 0)
        if sample_rate > 0:
            if sample_rate >= 1000:
                sample_rate_str = f"{sample_rate/1000:.1f} kHz"
            else:
                sample_rate_str = f"{sample_rate} Hz"
        else:
            sample_rate_str = "Unknown"
        
        # Format bitrate
        bitrate = info.get('bitrate', 0)
        if bitrate > 0:
            if bitrate >= 1000:
                bitrate_str = f"{bitrate/1000:.1f} kbps"
            else:
                bitrate_str = f"{bitrate} bps"
        else:
            bitrate_str = "Unknown"
        
        # Format channels
        channels = info.get('channels', 0)
        if channels == 1:
            channels_str = "Mono"
        elif channels == 2:
            channels_str = "Stereo"
        elif channels > 2:
            channels_str = f"{channels} channels"
        else:
            channels_str = "Unknown"
        
        return {
            f'duration{label_suffix}': duration_str,
            f'sample_rate{label_suffix}': sample_rate_str,
            f'bitrate{label_suffix}': bitrate_str,
            f'channels{label_suffix}': channels_str
        }
