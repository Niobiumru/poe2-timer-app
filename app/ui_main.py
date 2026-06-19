import os
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QListWidget, 
                             QFileDialog, QSpinBox, QMessageBox, QGroupBox,
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGridLayout, QCheckBox, QComboBox, QSizePolicy)
from PySide6.QtCore import Qt, QThreadPool, Slot, QSize, QTimer
from PySide6.QtGui import QColor, QPalette, QFont, QIcon, QFontMetrics

from .config_manager import ConfigManager
from .log_watcher import LogWatcher
from .parser_logic import LogParser
from .timer_logic import TimerLogic
from .sound_manager import SoundManager
from .version import VERSION
from .updater import UpdateManager

DARK_THEME = """
QMainWindow { background-color: #09090b; }
QWidget { background-color: #09090b; color: #fafafa; font-family: 'Arial Black', 'Impact', 'Arial', sans-serif; font-weight: bold; }
QLabel { background: transparent; }
QGroupBox { border: 1px solid #27272a; border-radius: 4px; margin-top: 1.5em; font-weight: bold; color: #8b5cf6; background-color: #18181b; }
QLineEdit, QSpinBox, QListWidget, QComboBox { 
    background-color: #18181b; 
    border: 1px solid #27272a; 
    border-radius: 4px; 
    padding: 6px; 
    color: #ffffff; 
}
QLineEdit:focus, QSpinBox:focus, QListWidget:focus, QComboBox:focus {
    border: 1px solid #8b5cf6;
}
QPushButton { 
    background-color: #18181b; 
    border: 1px solid #8b5cf6; 
    border-radius: 4px; 
    padding: 8px 15px; 
    color: #8b5cf6; 
    font-weight: bold; 
}
QPushButton:hover { 
    background-color: #8b5cf6; 
    color: #ffffff; 
}
QPushButton#startBtn { 
    background-color: #12181d; 
    border: 1.5px solid #8b5cf6; 
    border-radius: 6px; 
    color: #8b5cf6; 
    font-size: 18px; 
    font-weight: bold; 
    padding: 0px; 
    padding-left: 2px;
}
QPushButton#startBtn:hover { 
    background-color: #8b5cf6; 
    color: #ffffff; 
}
QPushButton#stopBtn { 
    background-color: #12181d; 
    border: 1.5px solid #ef4444; 
    border-radius: 6px; 
    color: #ef4444; 
    font-size: 16px; 
    font-weight: bold; 
    padding: 0px; 
}
QPushButton#stopBtn:hover { 
    background-color: #ef4444; 
    color: #ffffff; 
}
QPushButton#stopBtn:disabled { 
    background-color: #12181d; 
    border: 1.5px solid #ef444444; 
    color: #ef444444; 
}
QPushButton#resetBtn { 
    background-color: #12181d; 
    border: 1.5px solid #8b5cf6; 
    border-radius: 6px; 
    color: #8b5cf6; 
    font-size: 20px; 
    font-weight: bold; 
    padding: 0px; 
}
QPushButton#resetBtn:hover { 
    background-color: #8b5cf6; 
    color: #ffffff; 
}
QPushButton#exitBtn { 
    background-color: #12181d; 
    border: 1.5px solid #ef4444; 
    border-radius: 6px; 
    color: #ef4444; 
    font-size: 18px; 
    font-weight: bold; 
    padding: 0px; 
}
QPushButton#exitBtn:hover { 
    background-color: #ef4444; 
    color: #ffffff; 
}
QPushButton#updateBtn { 
    background-color: #fbbf24; 
    color: #09090b; 
    border: none; 
    font-size: 10px; 
    padding: 2px 10px; 
    border-radius: 4px;
}
QPushButton#miniBtn { 
    background-color: #18181b; 
    border: 1px solid #8b5cf644; 
    color: #8b5cf6; 
    padding: 2px 8px; 
    font-size: 11px; 
    font-weight: bold; 
    border-radius: 4px;
    min-height: 22px;
}
QPushButton#miniBtn:hover { 
    border: 1px solid #8b5cf6; 
    background-color: #18181b; 
}
QScrollBar:vertical {
    border: none;
    background: #09090b;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #27272a;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #8b5cf6;
}
QTableWidget { background-color: #18181b; gridline-color: #27272a; border: none; }
QHeaderView::section { background-color: #18181b; color: #fafafa; padding: 5px; border: 1px solid #27272a; }
"""

class Card(QFrame):
    def __init__(self, title, color="#8b5cf6"):
        super().__init__()
        self.setObjectName("mainCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.color = color
        
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setSpacing(0)
        
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet("background: transparent; border: none;")
        header_l = QHBoxLayout(self.header_widget)
        header_l.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        header_l.addWidget(self.title_label)
        header_l.addStretch()
        self.card_layout.addWidget(self.header_widget)
        
        self.update_style(6)

    def update_style(self, margins):
        self.setStyleSheet(f"""
            QFrame#mainCard {{ 
                background-color: #18181b; 
                border: 2px solid #27272a; 
                border-radius: 6px; 
            }}
            QLabel#cardTitle {{ 
                color: #fbbf24; 
                font-weight: 900; 
                font-size: 11px; 
                text-transform: uppercase; 
                border: none; 
                background: transparent; 
                letter-spacing: 2px;
            }}
        """)
        self.card_layout.setContentsMargins(margins, margins, margins, margins)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self, args=None):
        super().__init__()
        self.setWindowTitle("PoE 2 Map Timer Monitor")
        self.setMinimumSize(855, 500)
        self.setStyleSheet(DARK_THEME)
        self.is_debug = bool(args and "-debug" in args)
        self.is_mini = False
        self.current_reentry_color = "#8b5cf6"
        self.base_reentry_color = "#8b5cf6"
        self.is_blink_hidden = False
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._on_blink_timeout)
        self.config = ConfigManager()
        self.timer_logic = TimerLogic()
        self.sound_manager = SoundManager()
        self.update_manager = UpdateManager()
        self.thread_pool = QThreadPool()
        self.log_watcher = None
        
        # DEFENSIVE PRE-INIT
        self.maps_inline_label = QLabel("000")
        self.total_maps_val = QLabel("0")
        
        self._setup_ui()
        self._connect_signals()
        self._load_settings()
        
        if self.auto_start_check.isChecked():
            QTimer.singleShot(1000, self._on_start)
            
        # Check for updates in background
        QTimer.singleShot(2000, self._check_updates_async)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        
        # --- Top Area (Unified Grid) ---
        self.top_container = QWidget()
        top_l = QGridLayout(self.top_container)
        top_l.setContentsMargins(0, 0, 0, 0)
        top_l.setSpacing(8)
        
        game_label = QLabel("Game Folder")
        self.game_path_edit = QLineEdit()
        self.game_path_edit.setReadOnly(True)
        self.select_path_btn = QPushButton("Browse")
        
        top_l.addWidget(game_label, 0, 0)
        top_l.addWidget(self.game_path_edit, 0, 1)
        top_l.addWidget(self.select_path_btn, 0, 2)
        
        log_label = QLabel("Client Log")
        self.client_log_edit = QLineEdit()
        self.client_log_edit.setReadOnly(True)
        self.monitoring_status = QLabel("● Inactive")
        self.monitoring_status.setStyleSheet("color: #ef4444; font-weight: bold;")
        
        top_l.addWidget(log_label, 1, 0)
        top_l.addWidget(self.client_log_edit, 1, 1)
        top_l.addWidget(self.monitoring_status, 1, 2)
        
        top_l.setColumnStretch(0, 0)
        top_l.setColumnStretch(1, 1)
        top_l.setColumnStretch(2, 0)
        
        self.main_layout.addWidget(self.top_container)

        # --- Dashboard ---
        self.dashboard_widget = QWidget()
        self.dashboard_layout = QHBoxLayout(self.dashboard_widget)
        self.dashboard_layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_layout.setSpacing(10)

        # Left Column (Tracked Areas)
        self.left_col_widget = QWidget()
        self.left_col_widget.setFixedWidth(220)
        left_l = QVBoxLayout(self.left_col_widget)
        left_l.setContentsMargins(0, 0, 0, 0)
        area_group = Card("Tracked Areas", color="#8b5cf6")
        self.area_list = QListWidget()
        area_group.card_layout.addWidget(self.area_list)
        b_l = QHBoxLayout()
        b_l.setSpacing(6)
        self.add_area_btn = QPushButton("+")
        self.add_area_btn.setStyleSheet("font-size: 20px; font-weight: bold; padding: 2px;")
        self.add_area_btn.setToolTip("Add Area")
        self.remove_area_btn = QPushButton("-")
        self.remove_area_btn.setToolTip("Remove Selected Area")
        self.remove_area_btn.setStyleSheet("color: #ef4444; border-color: #ef4444; font-size: 20px; font-weight: bold; padding: 2px;")
        b_l.addWidget(self.add_area_btn)
        b_l.addWidget(self.remove_area_btn)
        area_group.card_layout.addLayout(b_l)
        left_l.addWidget(area_group)
        self.dashboard_layout.addWidget(self.left_col_widget, 0)

        # Right Column (Timers & Settings)
        self.right_col_widget = QWidget()
        right_l = QVBoxLayout(self.right_col_widget)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(10)
        
        # Timers layout (horizontal, stretch to fill)
        timers_row = QHBoxLayout()
        timers_row.setSpacing(8)
        
        self.reentry_card = Card("Re-entry Timer", color="#8b5cf6")
        self.reentry_display = QLabel("00:00")
        self.reentry_display.setAlignment(Qt.AlignCenter)
        self.reentry_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reentry_display.setStyleSheet("font-size: 56px; font-weight: bold; color: #8b5cf6; background: transparent; padding: 0; margin: 0; line-height: 1;")
        self.reentry_card.card_layout.addWidget(self.reentry_display, 0, Qt.AlignCenter)
        
        self.map_timer_card = Card("Map Timer", color="#fbbf24")
        self.map_timer_display = QLabel("00:00")
        self.map_timer_display.setAlignment(Qt.AlignCenter)
        self.map_timer_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.map_timer_display.setStyleSheet("font-size: 56px; font-weight: bold; color: #fbbf24; background: transparent; padding: 0; margin: 0; line-height: 1;")
        self.map_timer_card.card_layout.addWidget(self.map_timer_display, 0, Qt.AlignCenter)
        
        self.maps_card = Card("Maps", color="#fbbf24")
        self.maps_inline_label.setAlignment(Qt.AlignCenter)
        self.maps_inline_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.maps_inline_label.setStyleSheet("font-size: 38px; font-weight: bold; color: #fbbf24; background: transparent; padding: 0; margin: 0; line-height: 1;")
        self.maps_card.card_layout.addWidget(self.maps_inline_label, 0, Qt.AlignCenter)
        
        timers_row.addWidget(self.reentry_card)
        timers_row.addWidget(self.map_timer_card)
        timers_row.addWidget(self.maps_card)
        timers_row.addStretch()
        right_l.addLayout(timers_row)

        # Session Stats Bar
        self.info_bar = Card("Session Stats", color="#8b5cf6")
        self.info_bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.info_bar.setFixedHeight(50)
        self.info_l = QHBoxLayout()
        self.info_l.setContentsMargins(10, 0, 10, 0)
        self.info_l.setSpacing(15)
        
        self.last_area_val = QLabel("No Area")
        self.last_area_val.setStyleSheet("color: #8b5cf6; font-weight: bold; font-size: 11px; background: transparent; border: none;")
        self.info_l.addWidget(self.last_area_val)
        
        self.add_current_area_btn = QPushButton("+")
        self.add_current_area_btn.setObjectName("miniBtn")
        self.add_current_area_btn.setToolTip("Add current area to tracked list")
        self.add_current_area_btn.setCursor(Qt.PointingHandCursor)
        self.add_current_area_btn.setVisible(False)
        self.info_l.addWidget(self.add_current_area_btn)
        
        self.info_l.addStretch()
        
        self.mini_controls_widget = QWidget()
        self.mini_controls_widget.setStyleSheet("background: transparent; border: none;")
        self.mc_l = QHBoxLayout(self.mini_controls_widget)
        self.mc_l.setContentsMargins(0, 0, 0, 0)
        self.mc_l.setSpacing(0) 
        self.mc_l.setAlignment(Qt.AlignCenter)
        
        self.btn_s = QPushButton("S"); self.btn_s.setObjectName("miniBtn")
        self.btn_m = QPushButton("M"); self.btn_m.setObjectName("miniBtn")
        self.btn_l = QPushButton("L"); self.btn_l.setObjectName("miniBtn")
        self.expand_btn = QPushButton("F"); self.expand_btn.setObjectName("miniBtn")
        
        self.mc_l.addWidget(self.btn_s)
        self.mc_l.addWidget(self.btn_m)
        self.mc_l.addWidget(self.btn_l)
        self.mc_l.addWidget(self.expand_btn)
        self.mini_controls_widget.hide()
        self.info_l.addWidget(self.mini_controls_widget)
        
        self.info_bar.card_layout.addLayout(self.info_l)
        right_l.addWidget(self.info_bar)

        # Unified Settings & Controls Card
        self.sub_stats_widget = Card("Settings & Controls", color="#8b5cf6")
        
        # Grid layout for settings and control buttons to achieve perfect symmetry
        s_f = QGridLayout()
        s_f.setContentsMargins(10, 10, 10, 10)
        s_f.setSpacing(8)
        s_f.setHorizontalSpacing(15)
        
        s_f.setColumnStretch(0, 0)
        s_f.setColumnStretch(1, 1)
        s_f.setColumnStretch(2, 0)
        s_f.setColumnStretch(3, 0)
        
        # Row 0: Re-entry
        s_f.addWidget(QLabel("Re-entry (s)"), 0, 0)
        self.reentry_spin = QSpinBox()
        self.reentry_spin.setRange(1, 3600)
        s_f.addWidget(self.reentry_spin, 0, 1, 1, 2)
        
        self.start_btn = QPushButton("▶")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setFixedSize(32, 32)
        self.start_btn.setToolTip("Start Monitoring")
        s_f.addWidget(self.start_btn, 0, 3)
        
        # Row 1: Sound Path
        self.sound_edit = QLineEdit()
        self.sound_browse = QPushButton("...")
        self.sound_browse.setFixedSize(32, 32)
        self.sound_browse.setStyleSheet("padding: 0px; font-size: 14px; font-weight: bold;")
        s_f.addWidget(QLabel("Sound Path"), 1, 0)
        s_f.addWidget(self.sound_edit, 1, 1)
        s_f.addWidget(self.sound_browse, 1, 2)
        
        self.stop_btn = QPushButton("■")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFixedSize(32, 32)
        self.stop_btn.setToolTip("Stop Monitoring")
        s_f.addWidget(self.stop_btn, 1, 3)
        
        # Row 2: Checkboxes
        self.auto_start_check = QCheckBox("Auto-start")
        self.mini_mode_check = QCheckBox("Mini Mode")
        s_f.addWidget(self.auto_start_check, 2, 0)
        s_f.addWidget(self.mini_mode_check, 2, 1, 1, 2)
        
        self.reset_btn = QPushButton("↻")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setFixedSize(32, 32)
        self.reset_btn.setToolTip("Reset Total Count")
        s_f.addWidget(self.reset_btn, 2, 3)
        
        # Row 3: Mini Size
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["Large", "Medium", "Small"])
        s_f.addWidget(QLabel("Mini Size"), 3, 0)
        s_f.addWidget(self.scale_combo, 3, 1, 1, 2)
        
        self.exit_btn = QPushButton("✖")
        self.exit_btn.setObjectName("exitBtn")
        self.exit_btn.setFixedSize(32, 32)
        self.exit_btn.setToolTip("Exit Application")
        s_f.addWidget(self.exit_btn, 3, 3)
        
        self.sub_stats_widget.card_layout.addLayout(s_f)
        right_l.addWidget(self.sub_stats_widget)
        
        self.dashboard_layout.addWidget(self.right_col_widget, 2)
        self.main_layout.addWidget(self.dashboard_widget)

        self.log_group = Card("Event Log")
        self.log_table = QTableWidget(0, 4)
        self.log_table.setHorizontalHeaderLabels(["Time", "Level", "Source", "Message"])
        self.log_table.horizontalHeader().setStretchLastSection(True)
        self.log_table.verticalHeader().setVisible(False)
        self.log_group.card_layout.addWidget(self.log_table)
        self.main_layout.addWidget(self.log_group, 1)
        if not self.is_debug:
            self.log_group.hide()

        self.status_bar_widget = QWidget()
        sb_l = QHBoxLayout(self.status_bar_widget)
        sb_l.setContentsMargins(0, 0, 0, 0)
        self.status_text = QLabel("System Ready")
        self.update_btn = QPushButton(f"v{VERSION} - Up to date")
        self.update_btn.setObjectName("updateBtn")
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.setVisible(True) # Visible by default, shows current version
        self.last_update_text = QLabel("-")
        sb_l.addWidget(self.status_text)
        sb_l.addStretch()
        sb_l.addWidget(self.update_btn)
        sb_l.addWidget(self.last_update_text)
        self.main_layout.addWidget(self.status_bar_widget)

    def _connect_signals(self):
        self.select_path_btn.clicked.connect(self._on_select_path)
        self.sound_browse.clicked.connect(self._on_select_sound)
        self.add_area_btn.clicked.connect(self._on_add_area)
        self.remove_area_btn.clicked.connect(self._on_remove_area)
        self.area_list.itemDoubleClicked.connect(self._on_edit_area)
        self.add_current_area_btn.clicked.connect(self._on_add_current_area)
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)
        self.reset_btn.clicked.connect(self._on_reset_counter)
        self.exit_btn.clicked.connect(self.close)
        self.update_btn.clicked.connect(self._on_update_clicked)
        
        self.btn_s.clicked.connect(lambda: self._apply_quick_scale("Small"))
        self.btn_m.clicked.connect(lambda: self._apply_quick_scale("Medium"))
        self.btn_l.clicked.connect(lambda: self._apply_quick_scale("Large"))
        self.expand_btn.clicked.connect(self._on_expand_ui)
        
        self.mini_mode_check.toggled.connect(self._on_mini_mode_toggled)
        self.scale_combo.currentIndexChanged.connect(lambda: self._set_mini_state(self.is_mini))
        
        self.timer_logic.reentry_tick.connect(self._update_reentry_display)
        self.timer_logic.reentry_finished.connect(self._on_reentry_finished)
        self.timer_logic.area_tick.connect(self._update_area_timer_display)
        self.timer_logic.map_completed.connect(self._on_map_completed)
        self.timer_logic.log_message.connect(self._add_log_entry)

    def _check_updates_async(self):
        from PySide6.QtCore import QRunnable, QObject, Signal
        class WorkerSignals(QObject):
            finished = Signal(bool)
        class UpdateWorker(QRunnable):
            def __init__(self, manager):
                super().__init__()
                self.manager = manager
                self.signals = WorkerSignals()
            def run(self):
                res = self.manager.check_for_updates()
                self.signals.finished.emit(res)
        
        worker = UpdateWorker(self.update_manager)
        worker.signals.finished.connect(self._on_update_check_finished)
        self.thread_pool.start(worker)

    def _on_update_check_finished(self, available):
        if available:
            self.update_btn.setText(f"NEW UPDATE: v{self.update_manager.latest_version}")
            self.update_btn.setStyleSheet("background-color: #ff9800; color: #0b0f12; font-weight: bold;")
        else:
            self.update_btn.setText(f"v{VERSION} - Latest")
            self.update_btn.setEnabled(False)

    def _on_update_clicked(self):
        msg = QMessageBox.question(
            self, 
            "Update Available", 
            f"Would you like to download and install version {self.update_manager.latest_version} automatically?",
            QMessageBox.Yes | QMessageBox.No
        )
        if msg == QMessageBox.No:
            return

        self.update_btn.setText("Downloading...")
        self.update_btn.setEnabled(False)

        # Run download in a thread to keep UI responsive
        from PySide6.QtCore import QRunnable, QObject, Signal
        class DownloadSignals(QObject):
            progress = Signal(int)
            finished = Signal(bool, str)
        
        class DownloadWorker(QRunnable):
            def __init__(self, manager):
                super().__init__()
                self.manager = manager
                self.signals = DownloadSignals()
            def run(self):
                import tempfile
                temp_exe = os.path.join(tempfile.gettempdir(), "PoE2Timer_new.exe")
                # Using a lambda to bridge the callback to a signal
                success = self.manager.download_file(temp_exe, progress_callback=self.signals.progress.emit)
                self.signals.finished.emit(success, temp_exe)

        worker = DownloadWorker(self.update_manager)
        worker.signals.progress.connect(self._on_download_progress)
        worker.signals.finished.connect(self._on_download_finished)
        self.thread_pool.start(worker)

    def _on_download_progress(self, percent):
        self.update_btn.setText(f"Downloading: {percent}%")
        if percent >= 100:
            self.update_btn.setText("READY: Restart & Install")
            self.update_btn.setEnabled(True)
            self.update_btn.setStyleSheet("background-color: #fbbf24; color: #09090b; font-weight: bold;")
            # Disconnect previous slot to change behavior
            try:
                self.update_btn.clicked.disconnect()
            except:
                pass
            self.update_btn.clicked.connect(self._run_self_replacement)

    def _on_download_finished(self, success, temp_exe):
        if not success:
            QMessageBox.critical(self, "Error", "Failed to download the update.")
            self.update_btn.setText("Retry Update")
            self.update_btn.setEnabled(True)
            return
        
        self.downloaded_temp_exe = temp_exe
        # UI already updated in _on_download_progress

    def _run_self_replacement(self):
        if not hasattr(self, 'downloaded_temp_exe'):
            return

        msg = QMessageBox.question(
            self, 
            "Finish Update", 
            "Download complete. The application will now restart to apply the update. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if msg == QMessageBox.No:
            return

        temp_exe = self.downloaded_temp_exe
        # sys.executable is the most reliable way in PyInstaller to find the EXE path
        import sys
        current_exe = sys.executable
        
        if not current_exe.lower().endswith(".exe"):
            QMessageBox.information(self, "Info", f"Update downloaded to {temp_exe}. Automatic replacement only works for the compiled EXE version.")
            return

        # Create a batch script to swap files
        # We explicitly clear _MEIPASS in the batch environment to prevent the new EXE 
        # from attempting to load files/DLLs from the old temporary directory.
        batch_content = f"""@echo off
taskkill /f /pid {os.getpid()} >nul 2>&1
timeout /t 1 /nobreak >nul
move /y "{temp_exe}" "{current_exe}"
set _MEIPASS=
start "" "{current_exe}"
del "%~f0"
"""
        batch_path = os.path.join(os.path.dirname(current_exe), "updater.bat")
        try:
            with open(batch_path, "w") as f:
                f.write(batch_content)
            
            # Clear _MEIPASS environment variable for the child process environment as well
            env = os.environ.copy()
            env.pop("_MEIPASS", None)
            
            import subprocess
            subprocess.Popen(["cmd.exe", "/c", batch_path], env=env, shell=True)
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create update script: {e}")

    def _load_settings(self):
        self.game_path_edit.setText(self.config.get("game_path"))
        self._update_log_path_display(self.config.get("game_path"))
        for area in self.config.get("tracked_areas", []):
            self.area_list.addItem(area)
        self.reentry_spin.setValue(self.config.get("reentry_timer_duration"))
        
        # --- Asset Auto-Setup ---
        assets_dir = os.path.join(os.getcwd(), "assets", "sounds")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir, exist_ok=True)
            
        target_sound = os.path.join(assets_dir, "notify.mp3")
        
        # If external sound doesn't exist, try to copy it from internal bundle
        if not os.path.exists(target_sound):
            try:
                import shutil
                # In PyInstaller bundle, the internal path matches the relative structure
                internal_sound = resource_path("assets/sounds/notify.mp3")
                if os.path.exists(internal_sound):
                    shutil.copy2(internal_sound, target_sound)
                    self._add_log_entry("INFO", "App", "Default sound extracted to assets folder.")
                else:
                    # Fallback for dev environment or if path resolution differs
                    dev_sound = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds", "notify.mp3")
                    if os.path.exists(dev_sound):
                        shutil.copy2(dev_sound, target_sound)
            except Exception as e:
                self._add_log_entry("ERROR", "App", f"Failed to extract default sound: {e}")
        
        # Load sound from config or fallback to auto-setup target
        sound = self.config.get("sound_file")
        if not sound or not os.path.exists(sound):
            sound = target_sound
            
        self.sound_edit.setText(sound)
        
        self._on_map_completed(count=self.config.get("maps_completed", 0))
        self.auto_start_check.setChecked(self.config.get("auto_start", False))
        self.mini_mode_check.setChecked(self.config.get("mini_mode", False))
        
        saved_scale = self.config.get("mini_scale_text", "Large")
        idx = self.scale_combo.findText(saved_scale)
        if idx >= 0:
            self.scale_combo.setCurrentIndex(idx)

    def _save_settings(self):
        self.config.set("game_path", self.game_path_edit.text())
        areas = []
        for i in range(self.area_list.count()):
            areas.append(self.area_list.item(i).text())
        self.config.set("tracked_areas", areas)
        self.config.set("reentry_timer_duration", self.reentry_spin.value())
        self.config.set("sound_file", self.sound_edit.text())
        self.config.set("auto_start", self.auto_start_check.isChecked())
        self.config.set("mini_mode", self.mini_mode_check.isChecked())
        self.config.set("mini_scale_text", self.scale_combo.currentText())

    def _on_select_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select PoE 2 Folder")
        if path:
            self.game_path_edit.setText(path)
            self._update_log_path_display(path)
            self._save_settings()

    def _update_log_path_display(self, path):
        if path:
            self.client_log_edit.setText(os.path.join(path, "logs", "Client.txt"))

    def _on_select_sound(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Sound", "", "Audio Files (*.wav *.mp3)")
        if file:
            self.sound_edit.setText(file)
            self._save_settings()

    def _on_add_area(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Add Area", "Name:")
        if ok and name.strip():
            self.area_list.addItem(name.strip())
            self._save_settings()
            
    def _on_add_current_area(self):
        current_area = self.last_area_val.text()
        if not current_area or current_area == "No Area":
            return
            
        existing = []
        for i in range(self.area_list.count()):
            existing.append(self.area_list.item(i).text().lower())
            
        if current_area.lower() not in existing:
            self.area_list.addItem(current_area)
            self._save_settings()
            self._add_log_entry("INFO", "App", f"Added current area \"{current_area}\" to tracked list.")
            self.status_text.setText(f"Added {current_area}")

    def _on_remove_area(self):
        item = self.area_list.currentItem()
        if item:
            self.area_list.takeItem(self.area_list.row(item))
            self._save_settings()
            
    def _on_edit_area(self, item):
        from PySide6.QtWidgets import QInputDialog
        old_text = item.text()
        new_text, ok = QInputDialog.getText(self, "Edit Area", "Name:", QLineEdit.Normal, old_text)
        if ok:
            new_text_stripped = new_text.strip()
            if new_text_stripped:
                item.setText(new_text_stripped)
                self._save_settings()
            else:
                self.area_list.takeItem(self.area_list.row(item))
                self._save_settings()

    def _on_reset_counter(self):
        self.config.set("maps_completed", 0)
        self._on_map_completed(count=0)

    def _on_map_completed(self, count=None):
        if self.maps_inline_label is None:
            return
        if count is None:
            try:
                count = int(self.maps_inline_label.text()) + 1
            except:
                count = 1
        self.maps_inline_label.setText(f"{count:03d}")
        self.config.set("maps_completed", count)

    def _add_log_entry(self, level, source, message):
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        t = datetime.now().strftime("%H:%M:%S")
        self.log_table.setItem(row, 0, QTableWidgetItem(t))
        li = QTableWidgetItem(level)
        if level == "INFO":
            li.setForeground(QColor("#8b5cf6"))
        elif level == "WARN":
            li.setForeground(QColor("#fbbf24"))
        elif level == "ERROR":
            li.setForeground(QColor("#ef4444"))
        self.log_table.setItem(row, 1, li)
        self.log_table.setItem(row, 2, QTableWidgetItem(source))
        self.log_table.setItem(row, 3, QTableWidgetItem(message))
        self.log_table.scrollToBottom()
        self.last_update_text.setText(f"Updated: {t}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_mini:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.is_mini and hasattr(self, 'drag_pos'):
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def _apply_quick_scale(self, scale_text):
        idx = self.scale_combo.findText(scale_text)
        if idx >= 0:
            self.scale_combo.setCurrentIndex(idx)
        self._set_mini_state(True)

    def _on_expand_ui(self):
        self.mini_mode_check.setChecked(False)

    def _on_mini_mode_toggled(self, checked):
        self.is_mini = checked
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
            flags &= ~Qt.FramelessWindowHint
        self.setWindowFlags(flags)
        self._set_mini_state(checked)
        self.show()

    def _set_mini_state(self, mini):
        self.top_container.setVisible(not mini)
        self.left_col_widget.setVisible(not mini)
        self.sub_stats_widget.setVisible(not mini)
        self.status_bar_widget.setVisible(not mini)
        self.mini_controls_widget.setVisible(mini)
        self.add_current_area_btn.setVisible(mini)
        if self.is_debug:
            self.log_group.setVisible(not mini)
            
        scale_map = {"Large": 1.0, "Medium": 0.8, "Small": 0.65}
        scale = scale_map.get(self.scale_combo.currentText(), 1.0) if mini else 1.0
        
        # In mini mode, we force the frame's internal margins to exactly 2 pixels.
        m_val = 2 if mini else 8
        self.reentry_card.update_style(m_val)
        self.map_timer_card.update_style(m_val)
        self.maps_card.update_style(m_val)
        
        self.reentry_card.header_widget.setVisible(not mini)
        self.map_timer_card.header_widget.setVisible(not mini)
        self.maps_card.header_widget.setVisible(not mini)
        
        if mini:
            self.reentry_card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.map_timer_card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.maps_card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            
            px = int(72 * scale)
            px_small = int(48 * scale)
            
            # Use QFontMetrics to measure the exact width of text and set the cards size to match
            font = QFont()
            font.setPixelSize(px)
            font.setBold(True)
            fm = QFontMetrics(font)
            text_w = fm.horizontalAdvance("00:00")
            card_w = text_w + 16 # Padding + border padding
            card_h = px + 12     # Height based on font size + padding
            
            font_small = QFont()
            font_small.setPixelSize(px_small)
            font_small.setBold(True)
            fm_small = QFontMetrics(font_small)
            text_w_small = fm_small.horizontalAdvance("000")
            card_w_small = text_w_small + 16
            
            self.reentry_card.setFixedSize(card_w, card_h)
            self.map_timer_card.setFixedSize(card_w, card_h)
            self.maps_card.setFixedSize(card_w_small, card_h)
        else:
            self.reentry_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            self.map_timer_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            self.maps_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            self.reentry_card.setMinimumSize(0, 0)
            self.reentry_card.setMaximumSize(16777215, 16777215)
            self.map_timer_card.setMinimumSize(0, 0)
            self.map_timer_card.setMaximumSize(16777215, 16777215)
            self.maps_card.setMinimumSize(0, 0)
            self.maps_card.setMaximumSize(16777215, 16777215)
            self.reentry_card.setFixedHeight(120)
            self.map_timer_card.setFixedHeight(120)
            self.maps_card.setFixedHeight(120)
            
        self._refresh_displays_style(scale)
        
        if mini:
            if scale < 0.7:
                self.info_bar.setFixedHeight(30)
                self.info_bar.header_widget.hide()
                self.add_current_area_btn.setFixedHeight(18)
                self.mc_l.setSpacing(2)
                for i in range(self.mc_l.count()):
                    w = self.mc_l.itemAt(i).widget()
                    if w: w.setFixedHeight(18)
            else:
                self.info_bar.setFixedHeight(40)
                self.info_bar.header_widget.hide()
                self.add_current_area_btn.setFixedHeight(22)
                self.mc_l.setSpacing(0)
                for i in range(self.mc_l.count()):
                    w = self.mc_l.itemAt(i).widget()
                    if w: w.setFixedHeight(22)
                
            self.setMinimumSize(0, 0)
            QTimer.singleShot(10, self.adjustSize)
        else:
            self.info_bar.setFixedHeight(50)
            self.info_bar.header_widget.show()
            self.add_current_area_btn.setVisible(False)
            self.setMinimumSize(855, 500)
            self.resize(855, 500)

    def _refresh_displays_style(self, scale):
        px = int(72 * scale)
        mt = int(-0.25 * px)
        mb = int(-0.20 * px)
        
        px_small = int(48 * scale)
        mt_small = int(-0.25 * px_small)
        mb_small = int(-0.20 * px_small)

        self.reentry_display.setStyleSheet(f"font-size: {px}px; font-weight: bold; color: {self.current_reentry_color}; background: transparent; padding: 0px; margin-top: {mt}px; margin-bottom: {mb}px; line-height: 1;")
        self.map_timer_display.setStyleSheet(f"font-size: {px}px; font-weight: bold; color: #fbbf24; background: transparent; padding: 0px; margin-top: {mt}px; margin-bottom: {mb}px; line-height: 1;")
        self.maps_inline_label.setStyleSheet(f"font-size: {px_small}px; font-weight: bold; color: #fbbf24; background: transparent; padding: 0px; margin-top: {mt_small}px; margin-bottom: {mb_small}px; line-height: 1;")

    def _on_start(self):
        log_path = self.client_log_edit.text()
        if not os.path.exists(log_path):
            return
        self._save_settings()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.monitoring_status.setText("● Active")
        self.monitoring_status.setStyleSheet("color: #fbbf24; font-weight: bold;")
        self.log_watcher = LogWatcher(log_path, LogParser())
        self.log_watcher.signals.new_event.connect(self._handle_log_event)
        self.thread_pool.start(self.log_watcher)
        self._add_log_entry("INFO", "App", "Started.")

    def _on_stop(self):
        if self.log_watcher:
            self.log_watcher.stop()
        self.timer_logic.stop_all()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.monitoring_status.setText("● Inactive")
        self.monitoring_status.setStyleSheet("color: #ef4444; font-weight: bold;")
        self._add_log_entry("INFO", "App", "Stopped.")

    @Slot(dict)
    def _handle_log_event(self, event):
        tracked = []
        for i in range(self.area_list.count()):
            tracked.append(self.area_list.item(i).text())
        if event["type"] == "area":
            self.last_area_val.setText(event["value"])
        elif event["type"] == "instance":
            pass # ID hidden as per request
        self.timer_logic.handle_event(event, tracked, self.reentry_spin.value())

    def _update_reentry_display(self, seconds):
        m, s = divmod(seconds, 60)
        self.reentry_display.setText(f"{m:02}:{s:02}")
        total = self.reentry_spin.value()
        ratio = seconds / total if total > 0 else 0
        
        # Streamer gradient: Purple -> Gold -> Red
        purple = (139, 92, 246)
        gold = (251, 191, 36)
        red = (239, 68, 68)

        def interpolate(c1, c2, factor):
            return (
                int(c1[0] + (c2[0] - c1[0]) * factor),
                int(c1[1] + (c2[1] - c1[1]) * factor),
                int(c1[2] + (c2[2] - c1[2]) * factor)
            )

        if ratio >= 0.5:
            f = (ratio - 0.5) / 0.5
            r, g, b = interpolate(gold, purple, f)
        else:
            f = ratio / 0.5
            r, g, b = interpolate(red, gold, f)
            
        self.base_reentry_color = f"rgb({r}, {g}, {b})"
        
        # Blink logic for last 30 seconds
        if seconds <= 30 and seconds > 0:
            if not self.blink_timer.isActive():
                self.is_blink_hidden = False
                self.blink_timer.start(500)
        else:
            if self.blink_timer.isActive():
                self.blink_timer.stop()
                self.is_blink_hidden = False
                
        self._apply_reentry_color()

    def _on_blink_timeout(self):
        self.is_blink_hidden = not self.is_blink_hidden
        self._apply_reentry_color()

    def _apply_reentry_color(self):
        if self.is_blink_hidden:
            # Semi-transparent text to create a beautiful blink
            base = self.base_reentry_color
            self.current_reentry_color = base.replace("rgb", "rgba").replace(")", ", 0.2)")
        else:
            self.current_reentry_color = self.base_reentry_color
            
        scale_map = {"Large": 1.0, "Medium": 0.8, "Small": 0.65}
        scale = scale_map.get(self.scale_combo.currentText(), 1.0) if self.is_mini else 1.0
        self._refresh_displays_style(scale)

    def _on_reentry_finished(self):
        self._add_log_entry("WARN", "Timer", "RE-ENTRY FINISHED!")
        self.sound_manager.play_sound(self.sound_edit.text())

    def _update_area_timer_display(self, seconds):
        m, s = divmod(seconds, 60)
        self.map_timer_display.setText(f"{m:02}:{s:02}")

    def closeEvent(self, event):
        self._on_stop()
        self._save_settings()
        event.accept()
