from ._imports import *

class AppearanceMixin:
    def on_global_search(self, text):
        self.search_timer.start()

    def perform_delayed_search(self):
        current_lang = self.get_current_language()
        if current_lang and current_lang in self.tab_widgets:
            self.populate_tree(current_lang)

    def on_tab_changed(self, index):

        if index >= len(self.tab_widgets):
            return
            
        lang = self.get_current_language()
        if lang and lang in self.tab_widgets: 
            self.update_filter_combo(lang)
            if lang not in self.populated_tabs:
                self.populate_tree(lang)
                self.populated_tabs.add(lang)

    def expand_all_trees(self):
        current_lang = self.get_current_language()
        if current_lang and current_lang in self.tab_widgets:
            self.tab_widgets[current_lang]["tree"].expandAll()

    def collapse_all_trees(self):
        current_lang = self.get_current_language()
        if current_lang and current_lang in self.tab_widgets:
            self.tab_widgets[current_lang]["tree"].collapseAll()

    def apply_settings(self):

        theme = self.settings.data["theme"]
        if theme == "dark":
            self.setStyleSheet(self.get_dark_theme())
        else:
            self.setStyleSheet(self.get_light_theme())

    def get_dark_theme(self):
        return """
        QMainWindow, QDialog, QWidget {
            background-color: #2b2b2b;
            color: #d4d4d4;
            border: none;
        }

        QMenuBar {
            background-color: #3c3f41;
            border-bottom: 1px solid #4a4d4f;
        }
        QMenuBar::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        QMenu {
            background-color: #2b2b2b;
            border: 1px solid #4a4d4f;
        }
        QMenu::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }

        QToolBar {
            background-color: #3c3f41;
            spacing: 3px;
            padding: 3px;
        }
        QToolButton {
            background-color: transparent;
            padding: 4px;
            border-radius: 3px;
        }
        QToolButton:hover {
            background-color: #4a4d4f;
        }
        QToolButton:pressed, QToolButton:checked {
            background-color: #007acc;
        }

        QTabWidget::pane {
            border-top: 1px solid #4a4d4f;
        }
        QTabBar {
            qproperty-drawBase: 0;
            border: 0;
        }
        QTabBar::tab {
            background-color: #3c3f41;
            color: #d4d4d4;
            padding: 6px 12px;
            margin-right: 1px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:hover {
            background-color: #4a4d4f;
        }
        QTabBar::tab:selected {
            background-color: #2b2b2b; 
            border-bottom: 2px solid #007acc;
        }

        QTreeWidget, QTableWidget {
            background-color: #2b2b2b;
            alternate-background-color: #3c3f41; 
            border: 1px solid #4a4d4f;
            selection-background-color: #007acc; 
            selection-color: #ffffff; 
            gridline-color: #4a4d4f; 
        }
        QTreeWidget::item:hover, QTableWidget::item:hover {
            background-color: #45494a;
        }
        QHeaderView::section {
            background-color: #3c3f41;
            color: #d4d4d4;
            border: none;
            border-right: 1px solid #4a4d4f;
            border-bottom: 1px solid #4a4d4f;
            padding: 4px;
        }

        QPushButton {
            background-color: #4a4d4f;
            color: #d4d4d4;
            border: 1px solid #5a5d5f;
            padding: 5px 12px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #5a5d5f;
            border-color: #6a6d6f;
        }
        QPushButton:pressed {
            background-color: #3c3f41;
        }
        QPushButton[primary="true"], QPushButton:default {
            background-color: #007acc;
            color: white;
            border: 1px solid #007acc;
        }
        QPushButton[primary="true"]:hover {
            background-color: #1185cf;
        }
        QLabel {
            background-color: transparent;
        }
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            background-color: #3c3f41;
            border: 1px solid #4a4d4f;
            padding: 4px;
            border-radius: 4px;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
            border: 1px solid #007acc;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: url(./path/to/your/dark-arrow.png); 
        }

        QGroupBox {
            border: 1px solid #4a4d4f;
            margin-top: 8px;
            padding: 8px;
            border-radius: 4px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding-left: 5px;
            padding-right: 5px;
        }

        QProgressBar {
            background-color: #3c3f41;
            border: 1px solid #4a4d4f;
            border-radius: 4px;
            text-align: center;
            color: #d4d4d4;
        }
        QProgressBar::chunk {
            background-color: #007acc;
            border-radius: 4px;
        }
        QStatusBar {
            background-color: #007acc;
            color: white;
        }
        QSplitter::handle {
            background: #3c3f41;
        }
        QScrollBar:vertical {
            border: none;
            background: #2b2b2b;
            width: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: #4a4d4f;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar:horizontal {
            border: none;
            background: #2b2b2b;
            height: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:horizontal {
            background: #4a4d4f;
            min-width: 20px;
            border-radius: 5px;
        }
        """

    def get_light_theme(self):
        return """
        QMainWindow, QWidget {
            background-color: #f3f3f3;
            color: #1e1e1e;
        }
        
        QMenuBar {
            background-color: #e7e7e7;
            border-bottom: 1px solid #cccccc;
        }
        
        QMenuBar::item:selected {
            background-color: #bee6fd;
        }
        
        QMenu {
            background-color: #f3f3f3;
            border: 1px solid #cccccc;
        }
        
        QMenu::item:selected {
            background-color: #bee6fd;
        }
        
        QToolBar {
            background-color: #e7e7e7;
            border: none;
            spacing: 5px;
            padding: 5px;
        }
        
        QToolButton {
            background-color: transparent;
            border: none;
            padding: 5px;
            border-radius: 3px;
        }
        
        QToolButton:hover {
            background-color: #dadada;
        }
        
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #e7e7e7;
            color: #1e1e1e;
            padding: 8px 16px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 2px solid #0078d4;
        }
        
        QTreeWidget {
            background-color: #ffffff;
            alternate-background-color: #f9f9f9;
            border: 1px solid #cccccc;
            selection-background-color: #bee6fd;
        }
        
        QTreeWidget::item:hover {
            background-color: #e5f3ff;
        }
        
        QHeaderView::section {
            background-color: #e7e7e7;
            border: none;
            border-right: 1px solid #cccccc;
            padding: 5px;
        }
        
        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 6px 14px;
            border-radius: 3px;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QPushButton[primary="true"] {
            background-color: #107c10;
        }
        
        QPushButton[primary="true"]:hover {
            background-color: #0e7b0e;
        }
        
        QLineEdit, QTextEdit, QComboBox {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            padding: 5px;
            border-radius: 3px;
        }
        
        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid #0078d4;
        }
        
        QGroupBox {
            border: 1px solid #cccccc;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #ffffff;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QProgressBar {
            background-color: #e7e7e7;
            border: 1px solid #cccccc;
            border-radius: 3px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }
        
        QStatusBar {
            background-color: #0078d4;
            color: white;
        }
        """
