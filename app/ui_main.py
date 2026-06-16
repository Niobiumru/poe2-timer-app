import os
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QListWidget, 
                             QFileDialog, QSpinBox, QMessageBox, QGroupBox,
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGridLayout)
from PySide6.QtCore import Qt, QThreadPool, Slot, QSize
from PySide6.QtGui import QColor, QPalette, QFont, QIcon

from .config_manager import ConfigManager
from .log_watcher import LogWatcher
from .parser_logic import LogParser
from .timer_logic import TimerLogic
from .sound_manager import SoundManager

DARK_THEME = """
QMainWindow {
    background-color: #0b0f12;
}
QWidget {
    background-color: #0b0f12;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
}
QGroupBox {
    border: 1px solid #1a2228;
    border-radius: 8px;
    margin-top: 1.5em;
    font-weight: bold;
    color: #00bfa5;
    background-color: #12181d;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QLineEdit, QSpinBox, QListWidget {
    background-color: #1a2228;
    border: 1px solid #2c3e50;
    border-radius: 4px;
    padding: 5px;
    color: #ffffff;
}
QPushButton {
    background-color: #1a2228;
    border: 1px solid #00bfa5;
    border-radius: 4px;
    padding: 8px 15px;
    color: #00bfa5;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2c3e50;
}
QPushButton#startBtn {
    background-color: #00bfa5;
    color: #0b0f12;
}
QPushButton#stopBtn {
    background-color: #cf6679;
    color: #0b0f12;
    border-color: #cf6679;
}
QTableWidget {
    background-color: #12181d;
    gridline-color: #1a2228;
    border: none;
}
QHeaderView::section {
    background-color: #1a2228;
    color: #00bfa5;
    padding: 5px;
    border: 1px solid #12181d;
}
"""

class Card(QFrame):
    def __init__(self, title, color="#00bfa5"):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #12181d;
                border: 1px solid {color}33;
                border-radius: 12px;
            }}
            QLabel#cardTitle {{
                color: {color};
                font-weight: bold;
                text-transform: uppercase;
                border: none;
            }}
        """)
        self.layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        header.addWidget(self.title_label)
        header.addStretch()
        self.layout.addLayout(header)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PoE 2 Map Timer Monitor")
        self.setMinimumSize(1100, 850)
        self.setStyleSheet(DARK_THEME)

        self.config = ConfigManager()
        self.timer_logic = TimerLogic()
        self.sound_manager = SoundManager()
        self.thread_pool = QThreadPool()
        self.log_watcher = None

        self._setup_ui()
        self._connect_signals()
        self._load_settings()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- Top: Path Settings ---
        top_settings = QHBoxLayout()
        
        path_fields = QVBoxLayout()
        
        # Game Folder
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Game Folder"))
        self.game_path_edit = QLineEdit()
        self.game_path_edit.setReadOnly(True)
        self.select_path_btn = QPushButton("Browse")
        folder_layout.addWidget(self.game_path_edit)
        folder_layout.addWidget(self.select_path_btn)
        path_fields.addLayout(folder_layout)
        
        # Client Log
        log_layout = QHBoxLayout()
        log_layout.addWidget(QLabel("Client Log"))
        self.client_log_edit = QLineEdit()
        self.client_log_edit.setReadOnly(True)
        self.monitoring_status = QLabel("Monitoring: ● Inactive")
        self.monitoring_status.setStyleSheet("color: #cf6679; font-weight: bold;")
        log_layout.addWidget(self.client_log_edit)
        log_layout.addWidget(self.monitoring_status)
        path_fields.addLayout(log_layout)
        
        top_settings.addLayout(path_fields)
        main_layout.addLayout(top_settings)

        # --- Middle: Main Dashboard ---
        dashboard = QHBoxLayout()
        dashboard.setSpacing(20)

        # Left: Area List
        left_col = QVBoxLayout()
        area_group = Card("Tracked Areas")
        self.area_list = QListWidget()
        area_group.layout.addWidget(self.area_list)
        
        btn_layout = QHBoxLayout()
        self.add_area_btn = QPushButton("+ Add Area")
        self.remove_area_btn = QPushButton("Remove Area")
        self.remove_area_btn.setStyleSheet("color: #cf6679; border-color: #cf6679;")
        btn_layout.addWidget(self.add_area_btn)
        btn_layout.addWidget(self.remove_area_btn)
        area_group.layout.addLayout(btn_layout)
        
        left_col.addWidget(area_group)
        dashboard.addLayout(left_col, 1)

        # Center/Right: Timers & Stats
        right_col = QVBoxLayout()
        
        timers_row = QHBoxLayout()
        
        # Re-entry Timer Card
        self.reentry_card = Card("Re-entry Timer", "#00bfa5")
        self.reentry_display = QLabel("00:00")
        self.reentry_display.setAlignment(Qt.AlignCenter)
        self.reentry_display.setStyleSheet("font-size: 82px; font-weight: bold; color: #00bfa5; border: none;")
        self.reentry_card.layout.addWidget(self.reentry_display)
        self.reentry_card.layout.addWidget(QLabel("MM:SS"), 0, Qt.AlignCenter)
        
        info_layout = QGridLayout()
        info_layout.addWidget(QLabel("Last Area:"), 0, 0)
        self.last_area_val = QLabel("-")
        self.last_area_val.setStyleSheet("color: #00bfa5; font-weight: bold;")
        info_layout.addWidget(self.last_area_val, 0, 1)
        
        info_layout.addWidget(QLabel("Last Instance ID:"), 1, 0)
        self.last_id_val = QLabel("-")
        self.last_id_val.setStyleSheet("color: #00bfa5; font-weight: bold;")
        info_layout.addWidget(self.last_id_val, 1, 1)
        self.reentry_card.layout.addLayout(info_layout)
        
        # Map Timer Card
        self.map_timer_card = Card("Current Map Timer", "#ff9800")
        self.map_timer_display = QLabel("00:00")
        self.map_timer_display.setAlignment(Qt.AlignCenter)
        self.map_timer_display.setStyleSheet("font-size: 82px; font-weight: bold; color: #ff9800; border: none;")
        self.map_timer_card.layout.addWidget(self.map_timer_display)
        self.map_timer_card.layout.addWidget(QLabel("MM:SS"), 0, Qt.AlignCenter)
        
        timers_row.addWidget(self.reentry_card, 1)
        timers_row.addWidget(self.map_timer_card, 1)
        right_col.addLayout(timers_row)

        # Sub-stats Row
        sub_stats = QHBoxLayout()
        
        # Re-entry Settings
        settings_card = Card("Settings", "#e0e0e0")
        settings_form = QGridLayout()
        settings_form.addWidget(QLabel("Re-entry Duration"), 0, 0)
        self.reentry_spin = QSpinBox()
        self.reentry_spin.setRange(1, 3600)
        settings_form.addWidget(self.reentry_spin, 0, 1)
        settings_form.addWidget(QLabel("seconds"), 0, 2)
        
        settings_form.addWidget(QLabel("Alert Sound"), 1, 0)
        self.sound_edit = QLineEdit()
        self.sound_browse = QPushButton("Browse")
        settings_form.addWidget(self.sound_edit, 1, 1)
        settings_form.addWidget(self.sound_browse, 1, 2)
        settings_card.layout.addLayout(settings_form)
        
        # Completion Counter
        counter_card = Card("Maps Completed", "#00bfa5")
        self.counter_display = QLabel("0")
        self.counter_display.setAlignment(Qt.AlignCenter)
        self.counter_display.setStyleSheet("font-size: 36px; font-weight: bold; color: #00bfa5; border: none;")
        counter_card.layout.addWidget(self.counter_display)
        self.reset_counter_btn = QPushButton("Reset Counter")
        counter_card.layout.addWidget(self.reset_counter_btn)
        
        # Start/Stop Buttons
        control_card = QVBoxLayout()
        self.start_monitoring_btn = QPushButton("Start Monitoring")
        self.start_monitoring_btn.setObjectName("startBtn")
        self.start_monitoring_btn.setMinimumHeight(45)
        self.stop_monitoring_btn = QPushButton("Stop Monitoring")
        self.stop_monitoring_btn.setObjectName("stopBtn")
        self.stop_monitoring_btn.setMinimumHeight(45)
        self.stop_monitoring_btn.setEnabled(False)
        control_card.addWidget(self.start_monitoring_btn)
        control_card.addWidget(self.stop_monitoring_btn)

        sub_stats.addWidget(settings_card, 2)
        sub_stats.addWidget(counter_card, 1)
        sub_stats.addLayout(control_card, 1)
        right_col.addLayout(sub_stats)
        
        dashboard.addLayout(right_col, 2)
        main_layout.addLayout(dashboard)

        # --- Bottom: Event Log ---
        log_group = Card("Event Log")
        self.log_table = QTableWidget(0, 4)
        self.log_table.setHorizontalHeaderLabels(["Time", "Level", "Source", "Message"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.log_table.horizontalHeader().setStretchLastSection(True)
        self.log_table.setColumnWidth(0, 100)
        self.log_table.setColumnWidth(1, 60)
        self.log_table.setColumnWidth(2, 80)
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.log_table.verticalHeader().setVisible(False)
        log_group.layout.addWidget(self.log_table)
        main_layout.addWidget(log_group, 1)

        # --- Status Bar ---
        status_bar = QHBoxLayout()
        self.status_text = QLabel("Monitoring inactive")
        self.last_update_text = QLabel("Last update: -")
        self.lines_parsed_text = QLabel("Lines parsed: 0")
        status_bar.addWidget(self.status_text)
        status_bar.addStretch()
        status_bar.addWidget(self.last_update_text)
        status_bar.addWidget(QLabel("|"))
        status_bar.addWidget(self.lines_parsed_text)
        main_layout.addLayout(status_bar)

    def _connect_signals(self):
        self.select_path_btn.clicked.connect(self._on_select_path)
        self.sound_browse.clicked.connect(self._on_select_sound)
        self.add_area_btn.clicked.connect(self._on_add_area)
        self.remove_area_btn.clicked.connect(self._on_remove_area)
        self.start_monitoring_btn.clicked.connect(self._on_start)
        self.stop_monitoring_btn.clicked.connect(self._on_stop)
        self.reset_counter_btn.clicked.connect(self._on_reset_counter)

        self.timer_logic.reentry_tick.connect(self._update_reentry_display)
        self.timer_logic.reentry_finished.connect(self._on_reentry_finished)
        self.timer_logic.area_tick.connect(self._update_area_timer_display)
        self.timer_logic.map_completed.connect(self._on_map_completed)
        self.timer_logic.log_message.connect(self._add_log_entry)

    def _load_settings(self):
        self.game_path_edit.setText(self.config.get("game_path"))
        self._update_log_path_display(self.config.get("game_path"))
        for area in self.config.get("tracked_areas", []):
            self.area_list.addItem(area)
        self.reentry_spin.setValue(self.config.get("reentry_timer_duration"))
        self.sound_edit.setText(self.config.get("sound_file"))
        self.counter_display.setText(str(self.config.get("maps_completed", 0)))

    def _save_settings(self):
        self.config.set("game_path", self.game_path_edit.text())
        areas = [self.area_list.item(i).text() for i in range(self.area_list.count())]
        self.config.set("tracked_areas", areas)
        self.config.set("reentry_timer_duration", self.reentry_spin.value())
        self.config.set("sound_file", self.sound_edit.text())

    def _on_select_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Path of Exile 2 Folder")
        if path:
            self.game_path_edit.setText(path)
            self._update_log_path_display(path)
            self._save_settings()

    def _update_log_path_display(self, path):
        if path:
            log_path = os.path.join(path, "logs", "Client.txt")
            self.client_log_edit.setText(log_path)

    def _on_select_sound(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Sound", "", "Audio Files (*.wav *.mp3)")
        if file:
            self.sound_edit.setText(file)
            self._save_settings()

    def _on_add_area(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Add Area", "Enter area name:")
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
        self.counter_display.setText("0")

    def _on_map_completed(self):
        val = int(self.counter_display.text()) + 1
        self.counter_display.setText(str(val))
        self.config.set("maps_completed", val)

    def _add_log_entry(self, level, source, message):
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        self.log_table.setItem(row, 0, QTableWidgetItem(time_str))
        level_item = QTableWidgetItem(level)
        if level == "INFO": level_item.setForeground(QColor("#00bfa5"))
        elif level == "WARN": level_item.setForeground(QColor("#ff9800"))
        elif level == "ERROR": level_item.setForeground(QColor("#cf6679"))
        self.log_table.setItem(row, 1, level_item)
        self.log_table.setItem(row, 2, QTableWidgetItem(source))
        self.log_table.setItem(row, 3, QTableWidgetItem(message))
        self.log_table.scrollToBottom()
        self.last_update_text.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

    def _on_start(self):
        log_path = self.client_log_edit.text()
        if not os.path.exists(log_path):
            QMessageBox.critical(self, "Error", "Log file not found!")
            return
            
        self._save_settings()
        self.start_monitoring_btn.setEnabled(False)
        self.stop_monitoring_btn.setEnabled(True)
        self.monitoring_status.setText("Monitoring: ● Active")
        self.monitoring_status.setStyleSheet("color: #00bfa5; font-weight: bold;")
        self.status_text.setText("Monitoring active")
        
        self.log_watcher = LogWatcher(log_path, LogParser())
        self.log_watcher.signals.new_event.connect(self._handle_log_event)
        self.log_watcher.signals.error.connect(lambda e: self._add_log_entry("ERROR", "Watcher", e))
        self.thread_pool.start(self.log_watcher)
        self._add_log_entry("INFO", "App", "Started monitoring logs.")

    def _on_stop(self):
        if self.log_watcher:
            self.log_watcher.stop()
        self.timer_logic.stop_all()
        self.start_monitoring_btn.setEnabled(True)
        self.stop_monitoring_btn.setEnabled(False)
        self.monitoring_status.setText("Monitoring: ● Inactive")
        self.monitoring_status.setStyleSheet("color: #cf6679; font-weight: bold;")
        self.status_text.setText("Monitoring stopped")
        self._add_log_entry("INFO", "App", "Stopped monitoring logs.")

    @Slot(dict)
    def _handle_log_event(self, event):
        tracked = [self.area_list.item(i).text() for i in range(self.area_list.count())]
        duration = self.reentry_spin.value()
        
        if event["type"] == "area":
            self.last_area_val.setText(event["value"])
        elif event["type"] == "instance":
            self.last_id_val.setText(event["value"])
            
        self.timer_logic.handle_event(event, tracked, duration)

    def _update_reentry_display(self, seconds):
        mins, secs = divmod(seconds, 60)
        self.reentry_display.setText(f"{mins:02}:{secs:02}")
        # Color transition logic remains the same but with dark theme colors
        total = self.reentry_spin.value()
        if total <= 0: return
        ratio = seconds / total
        if ratio > 0.5: r, g, b = int(255 * (1 - (ratio - 0.5) * 2)), 191, 165 # Muted teal variants
        else: r, g, b = 191, int(191 * (ratio * 2)), 165
        self.reentry_display.setStyleSheet(f"font-size: 82px; font-weight: bold; color: rgb({r}, {g}, {b}); border: none;")

    def _on_reentry_finished(self):
        self._add_log_entry("WARN", "Timer", "RE-ENTRY TIMER FINISHED!")
        self.sound_manager.play_sound(self.sound_edit.text())

    def _update_area_timer_display(self, seconds):
        mins, secs = divmod(seconds, 60)
        self.map_timer_display.setText(f"{mins:02}:{secs:02}")

    def closeEvent(self, event):
        self._on_stop()
        self._save_settings()
        event.accept()
