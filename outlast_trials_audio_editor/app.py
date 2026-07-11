from .common import *
from .debug import DEBUG, install_exception_hooks
from .i18n import TRANSLATIONS
from .services.settings import AppSettings
from .ui.main_window import WemSubtitleApp


def main():
    install_exception_hooks()
    from PyQt5.QtCore import QSharedMemory
    from PyQt5.QtWidgets import QMessageBox

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    shared_memory_key = "DAA73E5A-A93B-4264-8263-6901E788C946-OutlastTrialsAudioEditor"
    shared_memory = QSharedMemory(shared_memory_key)
    
    temp_settings = AppSettings()
    lang = temp_settings.data.get("ui_language", "en")
    temp_tr = lambda key: TRANSLATIONS.get(lang, {}).get(key, key)
    
    if not shared_memory.create(1):
        QMessageBox.warning(
            None, 
            temp_tr("app_already_running_title"), 
            temp_tr("app_already_running_msg")
        )
        sys.exit(0)

    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = str(APP_ROOT)
    
    splash_path = os.path.join(base_path, "data", "splash.png")
    splash = None

    if os.path.exists(splash_path):
        original_pixmap = QtGui.QPixmap(splash_path)
        splash = QtWidgets.QSplashScreen(original_pixmap, QtCore.Qt.WindowStaysOnTopHint)
        splash.setMask(original_pixmap.mask())

        def show_splash_message(message_key):
            pixmap_with_text = original_pixmap.copy()
            painter = QtGui.QPainter(pixmap_with_text)
            
            font = QtGui.QFont()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QtGui.QColor(220, 220, 220))

            rect = pixmap_with_text.rect()
            text_rect = QtCore.QRect(rect.x(), rect.y() + rect.height() - 40, rect.width(), 30)

            painter.drawText(text_rect, QtCore.Qt.AlignCenter, temp_tr(message_key))
            painter.end()
            
            splash.setPixmap(pixmap_with_text)
            app.processEvents()

        show_splash_message("splash_loading_app")
        splash.show()
        app.processEvents()
    
    try:
        if splash: show_splash_message("splash_init_ui")
        window = WemSubtitleApp()

        if splash: show_splash_message("splash_loading_profiles")
        if not window.initialize_profiles_and_ui():
            sys.exit(0)
        
        if splash:
            splash.finish(window)
        
        window.show()
        
        QtCore.QTimer.singleShot(100, window.load_orphans_from_cache_or_scan)
        
        sys.exit(app.exec_())
    except Exception as e:
        error_msg = f"An unexpected error occurred:\n\n{str(e)}\n\n"
        error_msg += "Traceback:\n" + traceback.format_exc()
        
        log_filename = f"crash_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        log_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else str(APP_ROOT), log_filename)
        
        try:
            with open(log_path, 'w', encoding='utf-8') as log_file:
                log_file.write("=== CRASH LOG ===\n")
                log_file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"Version: {current_version}\n")
                log_file.write(f"OS: {sys.platform}\n")
                log_file.write(f"Python: {sys.version}\n")
                log_file.write(f"PyQt5: {QtCore.PYQT_VERSION_STR}\n\n")
                
                log_file.write("Debug Logs:\n")
                log_file.write(DEBUG.get_logs() + "\n\n")
                
                log_file.write("Error Details:\n")
                log_file.write(error_msg)

            error_msg += f"\n\nCrash log saved to: {log_path}"
        except Exception as save_error:
            error_msg += f"\n\nFailed to save crash log: {str(save_error)}"
        
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("Application Error")
        msg.setText("The application has encountered an error and will close.")
        msg.setInformativeText("Please report this bug with the details below.")
        msg.setDetailedText(error_msg)
        
        copy_btn = msg.addButton("Copy Error to Clipboard", QtWidgets.QMessageBox.ActionRole)
        msg.addButton("Close", QtWidgets.QMessageBox.RejectRole)
        
        msg.exec_()
        
        if msg.clickedButton() == copy_btn:
            QtWidgets.QApplication.clipboard().setText(error_msg)
            print("Error copied to clipboard")
        
        if 'DEBUG' in globals():
            DEBUG.log(f"Critical error: {str(e)}\n{traceback.format_exc()}", "ERROR")
        
        sys.exit(1) 



if __name__ == "__main__":
    main()
