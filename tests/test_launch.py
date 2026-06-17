import sys
import os
from PySide6.QtWidgets import QApplication

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.ui_main import MainWindow
    app = QApplication(sys.argv)
    window = MainWindow()
    print("MainWindow instantiated successfully!")
    window.close()
    sys.exit(0)
except Exception as e:
    print(f"FAILED TO INSTANTIATE: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
