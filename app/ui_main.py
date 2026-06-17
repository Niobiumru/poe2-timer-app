import os
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QListWidget, 
                             QFileDialog, QSpinBox, QMessageBox, QGroupBox,
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGridLayout, QCheckBox, QComboBox, QSizePolicy)
from PySide6.QtCore import Qt, QThreadPool, Slot, QSize, QTimer
from PySide6.QtGui import QColor, QPalette, QFont, QIcon

from .config_manager import ConfigManager
from .log_watcher import LogWatcher
from .parser_logic import LogParser
from .timer_logic import TimerLogic
from .sound_manager import SoundManager

DARK_THEME = """
QMainWindow { background-color: #0b0f12; }
QWidget { background-color: #0b0f12; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
QLabel { background: transparent; }
QGroupBox { border: 1px solid #1a2228; border-radius: 8px; margin-top: 1.5em; font-weight: bold; color: #00bfa5; background-color: #12181d; }
QLineEdit, QSpinBox, QListWidget, QComboBox { background-color: #1a2228; border: 1px solid #2c3e50; border-radius: 4px; padding: 5px; color: #ffffff; }
QPushButton { background-color: #1a2228; border: 1px solid #00bfa5; border-radius: 4px; padding: 8px 15px; color: #00bfa5; font-weight: bold; }
QPushButton:hover { background-color: #2c3e50; }
QPushButton#startBtn { background-color: #00bfa5; color: #0b0f12; }
QPushButton#stopBtn { background-color: #cf6679; color: #0b0f12; border-color: #cf6679; }
QPushButton#miniBtn { 
    background-color: #12181d; 
    border: 1px solid #00bfa544; 
    color: #00bfa5; 
    padding: 2px 8px; 
    font-size: 11px; 
    font-weight: bold; 
    border-radius: 4px;
    min-height: 22px;
}
QPushButton#miniBtn:hover { border: 1px solid #00bfa5; background-color: #1a2228; }
QTableWidget { background-color: #12181d; gridline-color: #1a2228; border: none; }
QHeaderView::section { background-color: #1a2228; color: #00bfa5; padding: 5px; border: 1px solid #12181d; }
"""

class Card(QFrame):
    def __init__(self, title, color="#00bfa5"):
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
        
        self.update_style(5)

    def update_style(self, margins):
        self.setStyleSheet(f"""
            QFrame#mainCard {{ 
                background-color: #12181d; 
                border: 1px solid {self.color}33; 
                border-radius: 8px; 
            }}
            QLabel#cardTitle {{ 
                color: {self.color}; 
                font-weight: bold; 
                font-size: 8px; 
                text-transform: uppercase; 
                border: none; 
                background: transparent; 
            }}
        """)
        self.card_layout.setContentsMargins(margins, margins, margins, margins)

class MainWindow(QMainWindow):
    def __init__(self, args=None):
        super().__init__()
        self.setWindowTitle("PoE 2 Map Timer Monitor")
        self.setMinimumSize(1100, 550)
        self.setStyleSheet(DARK_THEME)
        self.is_debug = bool(args and "-debug" in args)
        self.is_mini = False
        self.current_reentry_color = "#00bfa5"
        self.base_reentry_color = "#00bfa5"
        self.is_blink_hidden = False
        self.blink_timer = QTimer(self)
        self.config = ConfigManager()
        self.timer_logic = TimerLogic()
        self.sound_manager = SoundManager()
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

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setSpacing(5)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        
        # --- Top ---
        self.top_container = QWidget()
        top_l = QVBoxLayout(self.top_container)
        top_l.setContentsMargins(0, 0, 0, 0)
        f_l = QHBoxLayout()
        f_l.addWidget(QLabel("Game Folder"))
        self.game_path_edit = QLineEdit()
        self.game_path_edit.setReadOnly(True)
        self.select_path_btn = QPushButton("Browse")
        f_l.addWidget(self.game_path_edit)
        f_l.addWidget(self.select_path_btn)
        top_l.addLayout(f_l)
        
        l_l = QHBoxLayout()
        l_l.addWidget(QLabel("Client Log"))
        self.client_log_edit = QLineEdit()
        self.client_log_edit.setReadOnly(True)
        self.monitoring_status = QLabel("● Inactive")
        self.monitoring_status.setStyleSheet("color: #cf6679; font-weight: bold;")
        l_l.addWidget(self.client_log_edit)
        l_l.addWidget(self.monitoring_status)
        top_l.addLayout(l_l)
        self.main_layout.addWidget(self.top_container)

        # --- Dashboard ---
        self.dashboard_widget = QWidget()
        self.dashboard_layout = QHBoxLayout(self.dashboard_widget)
        self.dashboard_layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_layout.setSpacing(8)

        # Left Column
        self.left_col_widget = QWidget()
        left_l = QVBoxLayout(self.left_col_widget)
        left_l.setContentsMargins(0, 0, 0, 0)
        area_group = Card("Tracked Areas")
        self.area_list = QListWidget()
        area_group.card_layout.addWidget(self.area_list)
        b_l = QHBoxLayout()
        self.add_area_btn = QPushButton("+ Add")
        self.remove_area_btn = QPushButton("- Remove")
        self.remove_area_btn.setStyleSheet("color: #cf6679; border-color: #cf6679;")
        b_l.addWidget(self.add_area_btn)
        b_l.addWidget(self.remove_area_btn)
        area_group.card_layout.addLayout(b_l)
        left_l.addWidget(area_group)
        self.dashboard_layout.addWidget(self.left_col_widget, 1)

        # Right Column
        self.right_col_widget = QWidget()
        right_l = QVBoxLayout(self.right_col_widget)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(8)
        
        timers_row = QHBoxLayout()
        timers_row.setSpacing(5)
        
        # TIMERS WITH FIXED SIZE POLICY (NATIVE WRAPPING)
        self.reentry_card = Card("Re-entry Timer")
        self.reentry_card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.reentry_display = QLabel("00:00")
        self.reentry_display.setAlignment(Qt.AlignCenter)
        self.reentry_display.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.reentry_display.setStyleSheet("font-size: 56px; font-weight: bold; color: #00bfa5; background: transparent; padding: 0; margin: 0; line-height: 1;")
        self.reentry_card.card_layout.addWidget(self.reentry_display, 0, Qt.AlignCenter)
        
        self.map_timer_card = Card("Map Timer")
        self.map_timer_card.color = "#ff9800"
        self.map_timer_card.update_style(5)
        self.map_timer_card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.map_timer_display = QLabel("00:00")
        self.map_timer_display.setAlignment(Qt.AlignCenter)
        self.map_timer_display.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.map_timer_display.setStyleSheet("font-size: 56px; font-weight: bold; color: #ff9800; background: transparent; padding: 0; margin: 0; line-height: 1;")
        self.map_timer_card.card_layout.addWidget(self.map_timer_display, 0, Qt.AlignCenter)
        
        self.maps_card = Card("Maps")
        self.maps_card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.maps_inline_label.setAlignment(Qt.AlignCenter)
        self.maps_inline_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.maps_inline_label.setStyleSheet("font-size: 38px; font-weight: bold; color: #00bfa5; background: transparent; padding: 0; margin: 0; line-height: 1;")
        self.maps_card.card_layout.addWidget(self.maps_inline_label, 0, Qt.AlignCenter)
        
        # Add to row with alignment to prevent any expansion
        timers_row.addWidget(self.reentry_card, 0, Qt.AlignLeft | Qt.AlignTop)
        timers_row.addWidget(self.map_timer_card, 0, Qt.AlignLeft | Qt.AlignTop)
        timers_row.addWidget(self.maps_card, 0, Qt.AlignLeft | Qt.AlignTop)
        timers_row.addStretch()
        right_l.addLayout(timers_row)

        # Session Stats Bar
        self.info_bar = Card("Session Stats")
        self.info_bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.info_bar.setFixedHeight(50)
        info_l = QHBoxLayout()
        info_l.setContentsMargins(10, 0, 10, 0)
        info_l.setSpacing(15)
        
        self.last_area_val = QLabel("No Area")
        self.last_area_val.setStyleSheet("color: #00bfa5; font-weight: bold; font-size: 11px; background: transparent; border: none;")
        info_l.addWidget(self.last_area_val)
        info_l.addStretch()
        
        self.mini_controls_widget = QWidget()
        self.mini_controls_widget.setStyleSheet("background: transparent; border: none;")
        mc_l = QHBoxLayout(self.mini_controls_widget)
        mc_l.setContentsMargins(0, 0, 0, 0)
        mc_l.setSpacing(0) 
        
        self.btn_s = QPushButton("S"); self.btn_s.setObjectName("miniBtn")
        self.btn_m = QPushButton("M"); self.btn_m.setObjectName("miniBtn")
        self.btn_l = QPushButton("L"); self.btn_l.setObjectName("miniBtn")
        self.expand_btn = QPushButton("F"); self.expand_btn.setObjectName("miniBtn")
        
        mc_l.addWidget(self.btn_s)
        mc_l.addWidget(self.btn_m)
        mc_l.addWidget(self.btn_l)
        mc_l.addWidget(self.expand_btn)
        self.mini_controls_widget.hide()
        info_l.addWidget(self.mini_controls_widget)
        
        self.info_bar.card_layout.addLayout(info_l)
        right_l.addWidget(self.info_bar)

        # Settings
        self.sub_stats_widget = QWidget()
        sub_l = QHBoxLayout(self.sub_stats_widget)
        sub_l.setContentsMargins(0, 0, 0, 0)
        s_card = Card("Settings")
        s_f = QGridLayout()
        s_f.addWidget(QLabel("Re-entry (s)"), 0, 0)
        self.reentry_spin = QSpinBox()
        self.reentry_spin.setRange(1, 3600)
        s_f.addWidget(self.reentry_spin, 0, 1)
        self.sound_edit = QLineEdit()
        self.sound_browse = QPushButton("...")
        s_f.addWidget(QLabel("Sound Path"), 1, 0)
        s_f.addWidget(self.sound_edit, 1, 1)
        s_f.addWidget(self.sound_browse, 1, 2)
        self.auto_start_check = QCheckBox("Auto-start")
        self.mini_mode_check = QCheckBox("Mini Mode")
        s_f.addWidget(self.auto_start_check, 2, 0)
        s_f.addWidget(self.mini_mode_check, 2, 1)
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["Large", "Medium", "Small"])
        s_f.addWidget(QLabel("Mini Size"), 3, 0)
        s_f.addWidget(self.scale_combo, 3, 1)
        s_card.card_layout.addLayout(s_f)
        
        ctrl = QVBoxLayout()
        self.start_btn = QPushButton("START MONITORING"); self.start_btn.setObjectName("startBtn")
        self.stop_btn = QPushButton("STOP MONITORING"); self.stop_btn.setObjectName("stopBtn"); self.stop_btn.setEnabled(False)
        self.reset_btn = QPushButton("Reset Total Count")
        self.exit_btn = QPushButton("EXIT APPLICATION"); self.exit_btn.setStyleSheet("color: #cf6679; border-color: #cf6679;")
        
        ctrl.addWidget(self.start_btn)
        ctrl.addWidget(self.stop_btn)
        ctrl.addWidget(self.reset_btn)
        ctrl.addWidget(self.exit_btn)
        sub_l.addWidget(s_card, 2)
        sub_l.addLayout(ctrl, 1)
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
        self.last_update_text = QLabel("-")
        sb_l.addWidget(self.status_text)
        sb_l.addStretch()
        sb_l.addWidget(self.last_update_text)
        self.main_layout.addWidget(self.status_bar_widget)

    def _connect_signals(self):
        self.select_path_btn.clicked.connect(self._on_select_path)
        self.sound_browse.clicked.connect(self._on_select_sound)
        self.add_area_btn.clicked.connect(self._on_add_area)
        self.remove_area_btn.clicked.connect(self._on_remove_area)
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)
        self.reset_btn.clicked.connect(self._on_reset_counter)
        self.exit_btn.clicked.connect(self.close)
        
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
        if self.is_debug:
            self.log_group.setVisible(not mini)
            
        scale_map = {"Large": 1.0, "Medium": 0.8, "Small": 0.65}
        scale = scale_map.get(self.scale_combo.currentText(), 1.0) if mini else 1.0
        
        # In mini mode, we force the frame's internal margins to exactly 2 pixels.
        # This completely removes math-based guesswork.
        m_val = 2 if mini else 5
        self.reentry_card.update_style(m_val)
        self.map_timer_card.update_style(m_val)
        self.maps_card.update_style(m_val)
        
        self.reentry_card.header_widget.setVisible(not mini)
        self.map_timer_card.header_widget.setVisible(not mini)
        self.maps_card.header_widget.setVisible(not mini)
        
        # Clear any manual width/height limitations. Qt will wrap the text naturally.
        self.reentry_card.setMinimumSize(0, 0)
        self.reentry_card.setMaximumSize(16777215, 16777215)
        self.map_timer_card.setMinimumSize(0, 0)
        self.map_timer_card.setMaximumSize(16777215, 16777215)
        self.maps_card.setMinimumSize(0, 0)
        self.maps_card.setMaximumSize(16777215, 16777215)
        
        self._refresh_displays_style(scale)
        
        if mini:
            if scale < 0.7:
                self.info_bar.setFixedHeight(30)
                self.info_bar.header_widget.hide()
            else:
                self.info_bar.setFixedHeight(40)
                self.info_bar.header_widget.hide()
                
            # Allow the main window to shrink to exactly fit its tightly packed contents
            self.setMinimumSize(0, 0)
            QTimer.singleShot(10, self.adjustSize)
        else:
            self.info_bar.setFixedHeight(50)
            self.info_bar.header_widget.show()
            self.setMinimumSize(1100, 550)
            self.resize(1100, 550)

    def _refresh_displays_style(self, scale):
        # We use negative margins to cut off the empty vertical space around the font.
        # This allows the frame to wrap tightly around the shape of the numbers.
        px = int(72 * scale)
        mt = int(-0.25 * px)
        mb = int(-0.20 * px)
        
        px_small = int(48 * scale)
        mt_small = int(-0.25 * px_small)
        mb_small = int(-0.20 * px_small)

        self.reentry_display.setStyleSheet(f"font-size: {px}px; font-weight: bold; color: {self.current_reentry_color}; background: transparent; padding: 0px; margin-top: {mt}px; margin-bottom: {mb}px; line-height: 1;")
        self.map_timer_display.setStyleSheet(f"font-size: {px}px; font-weight: bold; color: #ff9800; background: transparent; padding: 0px; margin-top: {mt}px; margin-bottom: {mb}px; line-height: 1;")
        self.maps_inline_label.setStyleSheet(f"font-size: {px_small}px; font-weight: bold; color: #00bfa5; background: transparent; padding: 0px; margin-top: {mt_small}px; margin-bottom: {mb_small}px; line-height: 1;")

    def _load_settings(self):
        self.game_path_edit.setText(self.config.get("game_path"))
        self._update_log_path_display(self.config.get("game_path"))
        for area in self.config.get("tracked_areas", []):
            self.area_list.addItem(area)
        self.reentry_spin.setValue(self.config.get("reentry_timer_duration"))
        self.sound_edit.setText(self.config.get("sound_file"))
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

    def _on_remove_area(self):
        item = self.area_list.currentItem()
        if item:
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
            li.setForeground(QColor("#00bfa5"))
        elif level == "WARN":
            li.setForeground(QColor("#ff9800"))
        elif level == "ERROR":
            li.setForeground(QColor("#cf6679"))
        self.log_table.setItem(row, 1, li)
        self.log_table.setItem(row, 2, QTableWidgetItem(source))
        self.log_table.setItem(row, 3, QTableWidgetItem(message))
        self.log_table.scrollToBottom()
        self.last_update_text.setText(f"Updated: {t}")

    def _on_start(self):
        log_path = self.client_log_edit.text()
        if not os.path.exists(log_path):
            return
        self._save_settings()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.monitoring_status.setText("● Active")
        self.monitoring_status.setStyleSheet("color: #00bfa5; font-weight: bold;")
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
        self.monitoring_status.setStyleSheet("color: #cf6679; font-weight: bold;")
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
        
        # Color gradient: White -> Green -> Yellow -> Red
        white = (255, 255, 255)
        green = (0, 191, 165)
        yellow = (255, 235, 59)
        red = (207, 102, 121)

        def interpolate(c1, c2, factor):
            return (
                int(c1[0] + (c2[0] - c1[0]) * factor),
                int(c1[1] + (c2[1] - c1[1]) * factor),
                int(c1[2] + (c2[2] - c1[2]) * factor)
            )

        if ratio >= 0.66:
            f = (ratio - 0.66) / 0.34
            r, g, b = interpolate(green, white, f)
        elif ratio >= 0.33:
            f = (ratio - 0.33) / 0.33
            r, g, b = interpolate(yellow, green, f)
        else:
            f = ratio / 0.33
            r, g, b = interpolate(red, yellow, f)
            
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
