from ._imports import *

class HelpAboutMixin:
    def export_subtitles(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Subtitles", "subtitles_export.json", 
            "JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if path:
            if path.endswith(".json"):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"Subtitles": self.subtitles}, f, ensure_ascii=False, indent=2)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    for key, subtitle in sorted(self.subtitles.items()):
                        f.write(f"{key}: {subtitle}\n")
                        
            self.status_bar.showMessage(f"Exported to {path}", 3000)

    def import_subtitles(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Subtitles", "", "JSON Files (*.json)"
        )
        
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                imported = data.get("Subtitles", {})
                count = len(imported)
                
                reply = QtWidgets.QMessageBox.question(
                    self, "Import Subtitles",
                    f"Import {count} subtitles?\nThis will overwrite existing subtitles.",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.Yes:
                    self.subtitles.update(imported)
                    
                    for key, value in imported.items():
                        if key in self.original_subtitles and self.original_subtitles[key] != value:
                            self.modified_subtitles.add(key)
                        else:
                            self.modified_subtitles.discard(key)

                    current_lang = self.get_current_language()
                    if current_lang and current_lang in self.tab_widgets:
                        self.populate_tree(current_lang)
                        
                    self.status_bar.showMessage(f"Imported {count} subtitles", 3000)
                    self.update_status()
                    
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Import Error", str(e))

    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_text = f"""
        <h2>{self.tr("keyboard_shortcuts")}</h2>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
        <tr style="background-color: #f0f0f0;">
            <th>{self.tr("shortcuts_table_action")}</th>
            <th>{self.tr("shortcuts_table_shortcut")}</th>
            <th>{self.tr("shortcuts_table_description")}</th>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_edit_subtitle")}</b></td>
            <td>F2</td>
            <td>{self.tr("shortcut_edit_selected")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_save_subtitles")}</b></td>
            <td>Ctrl+S</td>
            <td>{self.tr("shortcut_save_all_changes")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_export_audio")}</b></td>
            <td>Ctrl+E</td>
            <td>{self.tr("shortcut_export_selected")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_revert_original")}</b></td>
            <td>Ctrl+R</td>
            <td>{self.tr("shortcut_revert_selected")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_deploy_run")}</b></td>
            <td>F5</td>
            <td>{self.tr("shortcut_deploy_launch")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_debug_console")}</b></td>
            <td>Ctrl+D</td>
            <td>{self.tr("shortcut_show_debug")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_settings")}</b></td>
            <td>Ctrl+,</td>
            <td>{self.tr("shortcut_open_settings")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_exit")}</b></td>
            <td>Ctrl+Q</td>
            <td>{self.tr("shortcut_close_app")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_play_original_action")}</b></td>
            <td>Space</td>
            <td>{self.tr("shortcut_play_original_desc")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_play_mod_action")}</b></td>
            <td>Ctrl+Space</td>
            <td>{self.tr("shortcut_play_mod_desc")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_delete_mod_action")}</b></td>
            <td>Delete</td>
            <td>{self.tr("shortcut_delete_mod_desc")}</td>
        </tr>
        </table>

        <h3>{self.tr("mouse_actions")}</h3>
        <ul>
            <li>{self.tr("mouse_double_subtitle")}</li>
            <li>{self.tr("mouse_double_file")}</li>
            <li>{self.tr("mouse_right_click")}</li>
        </ul>
        """
        
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(shortcuts_text)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def check_updates_on_startup(self):
        thread = threading.Thread(target=self._check_updates_thread, args=(True,))
        thread.daemon = True
        thread.start()

    def check_updates(self):
        self.statusBar().showMessage("Checking for updates...")
        
        thread = threading.Thread(target=self._check_updates_thread, args=(False,))
        thread.daemon = True
        thread.start()

    def _check_updates_thread(self, silent=False):
        try:
            repo_url = "https://api.github.com/repos/Bezna/OutlastTrials_AudioEditor/releases/latest"
            
            response = requests.get(repo_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')
            download_url = release_data['html_url']
            release_notes = release_data.get('body', 'No release notes available.')

            if version.parse(latest_version) > version.parse(current_version):
                QtCore.QMetaObject.invokeMethod(
                    self, "_show_update_available",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, latest_version),
                    QtCore.Q_ARG(str, download_url),
                    QtCore.Q_ARG(str, release_notes),
                    QtCore.Q_ARG(bool, silent)
                )
            else:
                if not silent:
                    QtCore.QMetaObject.invokeMethod(
                        self, "_show_up_to_date",
                        QtCore.Qt.QueuedConnection
                    )
                else:

                    QtCore.QMetaObject.invokeMethod(
                        self, "_update_status_silent",
                        QtCore.Qt.QueuedConnection,
                        QtCore.Q_ARG(str, "")
                    )
                    
        except requests.exceptions.RequestException as e:

            if not silent:
                QtCore.QMetaObject.invokeMethod(
                    self, "_show_network_error",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, str(e))
                )
            else:
                QtCore.QMetaObject.invokeMethod(
                    self, "_update_status_silent",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, "")
                )
        except Exception as e:
 
            if not silent:
                QtCore.QMetaObject.invokeMethod(
                    self, "_show_error",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, str(e))
                )
            else:
                QtCore.QMetaObject.invokeMethod(
                    self, "_update_status_silent",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, "")
                )

    def report_bug(self):
        """Show bug report dialog"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(self.tr("report_bug"))
        dialog.setMinimumSize(500, 400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        info_label = QtWidgets.QLabel(self.tr("bug_report_info"))
        layout.addWidget(info_label)
        
        desc_label = QtWidgets.QLabel(f"{self.tr('description')}:")
        layout.addWidget(desc_label)
        
        desc_text = QtWidgets.QTextEdit()
        desc_text.setPlaceholderText(
            "Please describe:\n"
            "1. What you were trying to do\n"
            "2. What happened instead\n"
            "3. Steps to reproduce the issue"
        )
        layout.addWidget(desc_text)
        
        email_label = QtWidgets.QLabel(f"{self.tr('email_optional')}:")
        layout.addWidget(email_label)
        
        email_edit = QtWidgets.QLineEdit()
        email_edit.setPlaceholderText("your@email.com")
        layout.addWidget(email_edit)
        
        btn_layout = QtWidgets.QHBoxLayout()
        
        copy_btn = QtWidgets.QPushButton(self.tr("copy_report_clipboard"))
        send_btn = QtWidgets.QPushButton(self.tr("open_github_issues"))
        cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
        
        def copy_report():
            report = f"""
    BUG REPORT - OutlastTrials AudioEditor {current_version}
    ==========================================
    Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Email: {email_edit.text() or 'Not provided'}

    Description:
    {desc_text.toPlainText()}

    System Info:
    - OS: {sys.platform}
    - Python: {sys.version.split()[0]}
    - PyQt5: {QtCore.PYQT_VERSION_STR}

    Debug Log (last 50 lines):
    {chr(10).join(DEBUG.logs[-50:])}
    """
            QtWidgets.QApplication.clipboard().setText(report)
            QtWidgets.QMessageBox.information(dialog, "Success", "Bug report copied to clipboard!")
        
        def open_github():
            import webbrowser
            webbrowser.open("https://github.com/Bezna/OutlastTrials_AudioEditor/issues")
        
        copy_btn.clicked.connect(copy_report)
        send_btn.clicked.connect(open_github)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(send_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def show_about(self):
        """Show about dialog with animations"""
        about_dialog = QtWidgets.QDialog(self)
        about_dialog.setWindowTitle(self.tr("about") + " OutlastTrials AudioEditor")
        about_dialog.setMinimumSize(600, 500)
        
        layout = QtWidgets.QVBoxLayout(about_dialog)

        header_widget = QtWidgets.QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0078d4, stop:1 #106ebe);
                border-radius: 5px;
            }
        """)
        header_layout = QtWidgets.QVBoxLayout(header_widget)
        
        title_label = QtWidgets.QLabel("OutlastTrials AudioEditor")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
            }
            QLabel:hover {
                color: #ffff99;
            }
        """)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setCursor(QtCore.Qt.PointingHandCursor)
        
        title_label.mousePressEvent = lambda event: self.show_secret_easter_egg()
        
        version_label = QtWidgets.QLabel("Version " + current_version)
        version_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 16px;
                background: transparent;
            }
        """)
        version_label.setAlignment(QtCore.Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(version_label)
        header_widget.setFixedHeight(120)
        
        layout.addWidget(header_widget)

        about_tabs = QtWidgets.QTabWidget()

        about_content = QtWidgets.QTextBrowser()
        about_content.setOpenExternalLinks(True)
        about_content.setHtml(f"""
        <div style="padding: 20px;">
        <p style="font-size: 14px; line-height: 1.6;">
        {self.tr("about_description")}
        </p>

        <h3>{self.tr("key_features")}</h3>
        <ul style="line-height: 1.8;">
            <li>{self.tr("audio_management")}</li>
            <li>{self.tr("subtitle_editing")}</li>
            <li>{self.tr("mod_creation")}</li>
            <li>{self.tr("multi_language")}</li>
            <li>{self.tr("modern_ui")}</li>
        </ul>

        <h3>{self.tr("technology_stack")}</h3>
        <p>{self.tr("built_with")}</p>
        <ul>
            <li>{self.tr("unreal_locres_tool")}</li>
            <li>{self.tr("vgmstream_tool")}</li>
            <li>{self.tr("repak_tool")}</li>
            <li>{self.tr("ffmpeg_tool")}</li>
        </ul>
        </div>
        """)
        about_tabs.addTab(about_content, self.tr("about"))

        credits_content = QtWidgets.QTextBrowser()
        credits_content.setHtml(f"""
        <div style="padding: 20px;">
        <h3>{self.tr("development_team")}</h3>
        <p><b>Developer:</b> Bezna</p>        
        <p>Tester/Polish Translator: Alaneg</p>
        <p>Tester/Mexican Spanish Translator: Mercedes</p>
        
        <h3>Special Thanks</h3>
        <ul>
            <li>vgmstream team - For audio conversion tools</li>
            <li>UnrealLocres developers - For localization support</li>
            <li>hypermetric - For mod packaging</li>
            <li>FFmpeg - For audio processing</li>
            <li>Red Barrels - For creating Outlast Trials</li>
        </ul>
        
        <h3>Open Source Libraries</h3>
        <ul>
            <li>PyQt5 - GUI Framework</li>
            <li>Python Standard Library</li>
        </ul>
        
        <p style="margin-top: 30px; color: #666;">
        This software is provided "as is" without warranty of any kind.
        Use at your own risk.
        </p>
        </div>
        """)
        about_tabs.addTab(credits_content, self.tr("credits"))
        
        license_content = QtWidgets.QTextBrowser()
        license_content.setHtml(f"""
        <div style="padding: 20px;">
        <h3>{self.tr("license_agreement")}</h3>
        <p>Copyright (c) 2026 OutlastTrials AudioEditor</p>
        
        <p>Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:</p>
        
        <p>The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.</p>
        
        <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.</p>
        </div>
        """)
        about_tabs.addTab(license_content, self.tr("license"))
        
        layout.addWidget(about_tabs)
        
        footer_widget = QtWidgets.QWidget()
        footer_layout = QtWidgets.QHBoxLayout(footer_widget)
        
        github_btn = QtWidgets.QPushButton("GitHub")
        discord_btn = QtWidgets.QPushButton("Discord")
        donate_btn = QtWidgets.QPushButton(self.tr("donate"))
        
        github_btn.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "GitHub", "https://github.com/Bezna/OutlastTrials_AudioEditor"))
        discord_btn.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "Discord", "My Discord: Bezna"))
        donate_btn.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "Donate", "https://www.donationalerts.com/r/bezna_"))
        
        footer_layout.addWidget(github_btn)
        footer_layout.addWidget(discord_btn)
        footer_layout.addWidget(donate_btn)
        footer_layout.addStretch()
        
        close_btn = QtWidgets.QPushButton(self.tr("close"))
        close_btn.clicked.connect(about_dialog.close)
        footer_layout.addWidget(close_btn)
        
        layout.addWidget(footer_widget)
        
        about_dialog.exec_()

    def show_secret_easter_egg(self):
        secret_dialog = QtWidgets.QDialog(self)
        secret_dialog.setWindowTitle("Cat")
        secret_dialog.setFixedSize(450, 500)
        secret_dialog.setModal(True)
        secret_dialog.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        secret_dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff6b9d, stop:0.5 #c44569, stop:1 #f8b500);
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(secret_dialog)
        layout.setSpacing(15)
        
        title = QtWidgets.QLabel(self.tr("easter_egg_title"))
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 22px;
                font-weight: bold;
                text-align: center;
                background: transparent;
                padding: 10px;
            }
        """)
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        image_container = QtWidgets.QWidget()
        image_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 10px;
            }
        """)
        image_layout = QtWidgets.QVBoxLayout(image_container)
        
        cat_image_label = QtWidgets.QLabel()
        cat_image_label.setAlignment(QtCore.Qt.AlignCenter)
        cat_image_label.setMinimumSize(300, 300)
        cat_image_label.setText(self.tr("easter_egg_loading"))
        cat_image_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                text-align: center;
                padding: 20px;
            }
        """)
        
        message = QtWidgets.QLabel("Loading...")
        message.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                text-align: center;
                background: transparent;
                padding: 15px;
                line-height: 1.4;
            }
        """)
        message.setAlignment(QtCore.Qt.AlignCenter)
        message.setWordWrap(True)
        
        self.easter_egg_loader = EasterEggLoader(self)
        
        def on_config_loaded(config):
            print(f"Config loaded: {config}")
            message.setText(f"{config.get('message', self.tr('easter_egg_message'))}")
            self.easter_egg_loader.load_image(config.get('easter_egg_image', ''))
            
        def on_image_loaded(pixmap):
            print("Setting pixmap to label...")
            scaled_pixmap = pixmap.scaled(280, 280, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            cat_image_label.setPixmap(scaled_pixmap)
            cat_image_label.setText("")
            print("Pixmap set successfully!")
            
        def on_loading_failed(error):
            print(f"Loading failed: {error}")
            message.setText(f"{self.tr('easter_egg_message')}")
            cat_image_label.setStyleSheet("""
                QLabel {
                    color: #ffaaaa;
                    font-size: 14px;
                    text-align: center;
                    padding: 40px;
                }
            """)
        
        self.easter_egg_loader.config_loaded.connect(on_config_loaded)
        self.easter_egg_loader.image_loaded.connect(on_image_loaded)
        self.easter_egg_loader.loading_failed.connect(on_loading_failed)
        
        self.easter_egg_loader.load_config()
        
        image_layout.addWidget(cat_image_label)
        layout.addWidget(image_container)
        layout.addWidget(message)
        
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.9);
                color: #333;
                border: none;
                border-radius: 20px;
                padding: 12px 30px;
                font-weight: bold;
                font-size: 14px;
                margin: 10px;
            }
            QPushButton:hover {
                background: white;
            }
            QPushButton:pressed {
                background: #f0f0f0;
            }
        """)
        
        close_btn.clicked.connect(secret_dialog.close)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.animate_easter_egg(secret_dialog)
        
        secret_dialog.exec_()

    def animate_easter_egg(self, dialog):
        dialog.setWindowOpacity(0.0)
        dialog.show()
        
        self.fade_animation = QtCore.QPropertyAnimation(dialog, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

    def restore_window_state(self):
        if self.settings.data.get("window_geometry"):
            try:
                geometry = bytes.fromhex(self.settings.data["window_geometry"])
                self.restoreGeometry(geometry)
            except:
                self.resize(1400, 800)
        else:
            self.resize(1400, 800)
