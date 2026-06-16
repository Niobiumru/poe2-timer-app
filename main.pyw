import sys
import os

# Suppress Qt multimedia/ffmpeg logging noise
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.*=false;*.debug=false"

from PySide6.QtWidgets import QApplication
from app.ui_main import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow(sys.argv)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
