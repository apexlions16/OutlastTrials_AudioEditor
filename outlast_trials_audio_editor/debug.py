from .common import *

class DebugLogger:
    def __init__(self):
        self.logs_in_memory = []
        self.callbacks = []
        self.log_file_path = None

    def setup_logging(self, base_path):
        try:
            data_path = os.path.join(base_path, "data")
            os.makedirs(data_path, exist_ok=True)
            
            self.log_file_path = os.path.join(data_path, "session_log.txt")
            previous_log_path = os.path.join(data_path, "previous_session_log.txt")
            
            if os.path.exists(self.log_file_path):
                if os.path.exists(previous_log_path):
                    os.remove(previous_log_path)
                os.rename(self.log_file_path, previous_log_path)

            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.write(f"=== Session started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

        except Exception as e:
            print(f"FATAL: Could not set up file logging: {e}")
            self.log_file_path = None

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        self.logs_in_memory.append(log_entry)
        print(log_entry)
        
        if self.log_file_path:
            try:
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(log_entry + '\n')
            except Exception as e:
                print(f"ERROR: Could not write to log file: {e}")
        
        for callback in self.callbacks:
            callback(log_entry)
            
    def add_callback(self, callback):
        self.callbacks.append(callback)
        
    def get_logs(self):
        return "\n".join(self.logs_in_memory)

DEBUG = DebugLogger()

class DebugWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tr = parent.tr if parent and hasattr(parent, 'tr') else lambda key: key 
        self.setWindowTitle(self.tr("debug_console_title"))
        self.setMinimumSize(800, 400)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        controls = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls)
        
        self.auto_scroll = QtWidgets.QCheckBox(self.tr("auto_scroll_check"))
        self.auto_scroll.setChecked(True)
        
        clear_btn = QtWidgets.QPushButton(self.tr("clear"))
        clear_btn.clicked.connect(self.clear_logs)
        
        save_btn = QtWidgets.QPushButton(self.tr("save_log_btn"))
        save_btn.clicked.connect(self.save_log)
        
        controls_layout.addWidget(self.auto_scroll)
        controls_layout.addStretch()
        controls_layout.addWidget(clear_btn)
        controls_layout.addWidget(save_btn)
        
        layout.addWidget(controls)
        
        self.log_display = QtWidgets.QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QtGui.QFont("Consolas", 9))
        layout.addWidget(self.log_display)
        
        self.log_display.setPlainText(DEBUG.get_logs())
        
        DEBUG.add_callback(self.append_log)
        
    def append_log(self, log_entry):
        self.log_display.append(log_entry)
        if self.auto_scroll.isChecked():
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def clear_logs(self):
        self.log_display.clear()
        DEBUG.logs.clear()
        
    def save_log(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("save_debug_log_title"), 
            f"wem_subtitle_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            self.tr("log_files_filter")
        )
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(DEBUG.get_logs())

def global_exception_handler(exc_type, exc_value, exc_traceback):
    error_details = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    full_error_msg = f"An unexpected error occurred:\n\n{error_details}"
    
    DEBUG.log("="*20 + " CRITICAL ERROR " + "="*20, "ERROR")
    DEBUG.log(full_error_msg, "ERROR")
    
    log_filename = f"crash_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else str(APP_ROOT)
    log_path = os.path.join(base_path, "data", log_filename)
    
    try:
        with open(log_path, 'w', encoding='utf-8') as crash_file:
            crash_file.write("=== CRASH REPORT ===\n")
            crash_file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            crash_file.write(f"Version: {current_version}\n\n")
            crash_file.write(f"OS: {sys.platform}\n")
            crash_file.write("--- Error Details ---\n")
            crash_file.write(full_error_msg + "\n\n")
            crash_file.write("--- Full Session Log ---\n")
            crash_file.write(DEBUG.get_logs())
        
        final_message_for_user = f"{full_error_msg}\n\nA detailed crash log has been saved to:\n{log_path}"
    except Exception as save_error:
        final_message_for_user = f"{full_error_msg}\n\nFailed to save detailed crash log: {str(save_error)}"
    
    app = QtWidgets.QApplication.instance()
    if app:
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("Application Error")
        msg.setText("The application has encountered a critical error and will close.")
        msg.setInformativeText("Please report this bug with the details from the log files found in the 'data' folder.")
        msg.setDetailedText(final_message_for_user)
        
        copy_btn = msg.addButton("Copy Error to Clipboard", QtWidgets.QMessageBox.ActionRole)
        msg.addButton("Close", QtWidgets.QMessageBox.RejectRole)
        
        msg.exec_()
        
        if msg.clickedButton() == copy_btn:
            QtWidgets.QApplication.clipboard().setText(final_message_for_user)
    
    print("CRITICAL ERROR:", final_message_for_user)
    sys.exit(1)

def thread_exception_handler(args):
    global_exception_handler(args.exc_type, args.exc_value, args.exc_traceback)

def install_exception_hooks():
    """Install process and Python-thread exception handlers."""
    sys.excepthook = global_exception_handler
    if hasattr(threading, "excepthook"):
        threading.excepthook = thread_exception_handler
