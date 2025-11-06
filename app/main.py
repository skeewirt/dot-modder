import sys, os
from PySide6.QtWidgets import QApplication
from app.gui.app_window import AppWindow

def ensure_dirs():
    os.makedirs(os.path.join(os.getcwd(), "profiles"), exist_ok=True)

if __name__ == "__main__":
    ensure_dirs()
    app = QApplication(sys.argv)
    win = AppWindow()
    win.show()
    sys.exit(app.exec())
