import sys
from PySide6.QtWidgets import QApplication
from gui_parts.main_window import MainWindow

if __name__ == "__main__":
    def handle_exception(exc_type, exc_value, exc_traceback):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    sys.excepthook = handle_exception
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1600, 900)
    window.show()
    sys.exit(app.exec())