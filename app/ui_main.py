import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QListWidget, 
                             QFileDialog, QSpinBox, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt, QThreadPool, Slot
from PySide6.QtGui import QColor, QPalette

from .config_manager import ConfigManager
from .log_watcher import LogWatcher
from .parser_logic import LogParser
from .timer_logic import TimerLogic
from .sound_manager import SoundManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PoE 2 Re-entry Protection & Timer")
        self.setMinimumSize(600, 700)

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

        # 1. Path Selection
        path_group = QGroupBox("Game Path Settings")
        path_layout = QVBoxLayout()
        
        path_input_layout = QHBoxLayout()
        self.game_path_edit = QLineEdit()
        self.game_path_edit.setReadOnly(True)
        self.select_path_btn = QPushButton("Select Game Folder")
        path_input_layout.addWidget(self.game_path_edit)
        path_input_layout.addWidget(self.select_path_btn)
        
        self.client_txt_label = QLabel("Client.txt: Not found")
        self.status_label = QLabel("Status: Idle")
        
        path_layout.addLayout(path_input_layout)
        path_layout.addWidget(self.client_txt_label)
        path_layout.addWidget(self.status_label)
        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        # 2. Area Management
        area_group = QGroupBox("Tracked Areas")
        area_layout = QVBoxLayout()
        
        self.area_list = QListWidget()
        area_input_layout = QHBoxLayout()
        self.new_area_edit = QLineEdit()
        self.new_area_edit.setPlaceholderText("Enter area name...")
        self.add_area_btn = QPushButton("Add")
        self.remove_area_btn = QPushButton("Remove")
        area_input_layout.addWidget(self.new_area_edit)
        area_input_layout.addWidget(self.add_area_btn)
        area_input_layout.addWidget(self.remove_area_btn)
        
        area_layout.addWidget(self.area_list)
        area_layout.addLayout(area_input_layout)
        area_group.setLayout(area_layout)
        main_layout.addWidget(area_group)

        # 3. Timer Settings & Displays
        timers_container = QHBoxLayout()
        
        # Reentry Timer UI
        reentry_group = QGroupBox("Re-entry Timer")
        reentry_vbox = QVBoxLayout()
        self.reentry_display = QLabel("00:00")
        self.reentry_display.setAlignment(Qt.AlignCenter)
        self.reentry_display.setStyleSheet("font-size: 48px; font-weight: bold; color: green;")
        
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Duration (s):"))
        self.reentry_duration_spin = QSpinBox()
        self.reentry_duration_spin.setRange(1, 3600)
        self.reentry_duration_spin.setValue(60)
        settings_layout.addWidget(self.reentry_duration_spin)
        
        reentry_vbox.addWidget(self.reentry_display)
        reentry_vbox.addLayout(settings_layout)
        reentry_group.setLayout(reentry_vbox)
        
        # Area Timer UI
        area_timer_group = QGroupBox("Current Map Timer")
        area_vbox = QVBoxLayout()
        self.area_timer_display = QLabel("00:00")
        self.area_timer_display.setAlignment(Qt.AlignCenter)
        self.area_timer_display.setStyleSheet("font-size: 48px; font-weight: bold; color: green;")
        
        area_settings_layout = QHBoxLayout()
        area_settings_layout.addWidget(QLabel("Limit (s):"))
        self.area_duration_spin = QSpinBox()
        self.area_duration_spin.setRange(1, 7200)
        self.area_duration_spin.setValue(300)
        area_settings_layout.addWidget(self.area_duration_spin)
        
        self.last_map_label = QLabel("Last Map: None")
        self.last_id_label = QLabel("Last ID: None")
        
        area_vbox.addWidget(self.area_timer_display)
        area_vbox.addLayout(area_settings_layout)
        area_vbox.addWidget(self.last_map_label)
        area_vbox.addWidget(self.last_id_label)
        area_timer_group.setLayout(area_vbox)
        
        timers_container.addWidget(reentry_group)
        timers_container.addWidget(area_timer_group)
        main_layout.addLayout(timers_container)

        # 4. Sound & Control
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout()
        
        sound_layout = QHBoxLayout()
        self.sound_path_edit = QLineEdit()
        self.sound_path_edit.setPlaceholderText("Custom sound file (optional)...")
        self.select_sound_btn = QPushButton("...")
        self.test_sound_btn = QPushButton("Test Sound")
        sound_layout.addWidget(self.sound_path_edit)
        sound_layout.addWidget(self.select_sound_btn)
        sound_layout.addWidget(self.test_sound_btn)
        
        self.start_btn = QPushButton("Start Monitoring")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; height: 40px; font-weight: bold;")
        self.stop_btn = QPushButton("Stop Monitoring")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("height: 40px; font-weight: bold;")

        control_layout.addLayout(sound_layout)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

    def _connect_signals(self):
        self.select_path_btn.clicked.connect(self._on_select_path)
        self.add_area_btn.clicked.connect(self._on_add_area)
        self.remove_area_btn.clicked.connect(self._on_remove_area)
        self.select_sound_btn.clicked.connect(self._on_select_sound)
        self.test_sound_btn.clicked.connect(self._on_test_sound)
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)

        self.timer_logic.reentry_tick.connect(self._update_reentry_display)
        self.timer_logic.reentry_finished.connect(self._on_reentry_finished)
        self.timer_logic.area_tick.connect(self._update_area_timer_display)

    def _load_settings(self):
        self.game_path_edit.setText(self.config.get("game_path"))
        self._update_client_txt_status(self.config.get("game_path"))
        
        for area in self.config.get("tracked_areas", []):
            self.area_list.addItem(area)
            
        self.reentry_duration_spin.setValue(self.config.get("reentry_timer_duration"))
        self.area_duration_spin.setValue(self.config.get("area_timer_limit", 300))
        self.sound_path_edit.setText(self.config.get("sound_file"))

    def _save_settings(self):
        self.config.set("game_path", self.game_path_edit.text())
        tracked_areas = [self.area_list.item(i).text() for i in range(self.area_list.count())]
        self.config.set("tracked_areas", tracked_areas)
        self.config.set("reentry_timer_duration", self.reentry_duration_spin.value())
        self.config.set("area_timer_limit", self.area_duration_spin.value())
        self.config.set("sound_file", self.sound_path_edit.text())

    def _on_select_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Path of Exile 2 Folder")
        if path:
            self.game_path_edit.setText(path)
            self._update_client_txt_status(path)
            self._save_settings()

    def _update_client_txt_status(self, game_path):
        if not game_path:
            self.client_txt_label.setText("Client.txt: Path not selected")
            return
            
        client_path = os.path.join(game_path, "logs", "Client.txt")
        if os.path.exists(client_path):
            self.client_txt_label.setText(f"Client.txt: Found ({client_path})")
            self.client_txt_label.setStyleSheet("color: green;")
        else:
            self.client_txt_label.setText(f"Client.txt: Not found in {os.path.join(game_path, 'logs')}")
            self.client_txt_label.setStyleSheet("color: red;")

    def _on_add_area(self):
        name = self.new_area_edit.text().strip()
        if name:
            # Check for duplicates
            items = [self.area_list.item(i).text() for i in range(self.area_list.count())]
            if name not in items:
                self.area_list.addItem(name)
                self.new_area_edit.clear()
                self._save_settings()

    def _on_remove_area(self):
        current_item = self.area_list.currentItem()
        if current_item:
            self.area_list.takeItem(self.area_list.row(current_item))
            self._save_settings()

    def _on_select_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Sound File", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            self.sound_path_edit.setText(file_path)
            self._save_settings()

    def _on_test_sound(self):
        self.sound_manager.play_sound(self.sound_path_edit.text())

    def _on_start(self):
        game_path = self.game_path_edit.text()
        client_path = os.path.join(game_path, "logs", "Client.txt")
        
        if not os.path.exists(client_path):
            QMessageBox.critical(self, "Error", "Client.txt not found. Please select the correct game folder.")
            return

        self._save_settings()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        self.log_watcher = LogWatcher(client_path, LogParser())
        self.log_watcher.signals.new_event.connect(self._handle_log_event)
        self.log_watcher.signals.status_changed.connect(lambda s: self.status_label.setText(f"Status: {s}"))
        self.log_watcher.signals.error.connect(self._on_watcher_error)
        
        self.thread_pool.start(self.log_watcher)

    def _on_stop(self):
        if self.log_watcher:
            self.log_watcher.stop()
        self.timer_logic.stop_all()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopped")

    def _on_watcher_error(self, err_msg):
        QMessageBox.warning(self, "Watcher Error", err_msg)
        self._on_stop()

    @Slot(dict)
    def _handle_log_event(self, event):
        tracked_areas = [self.area_list.item(i).text() for i in range(self.area_list.count())]
        duration = self.reentry_duration_spin.value()
        
        if event["type"] == "area":
            self.last_map_label.setText(f"Last Map: {event['value']}")
        elif event["type"] == "instance":
            self.last_id_label.setText(f"Last ID: {event['value']}")
            
        self.timer_logic.handle_event(event, tracked_areas, duration)

    def _update_reentry_display(self, seconds):
        mins, secs = divmod(seconds, 60)
        self.reentry_display.setText(f"{mins:02}:{secs:02}")
        
        # Color transition: Green -> Yellow -> Red
        total = self.reentry_duration_spin.value()
        if total <= 0: return
        
        ratio = seconds / total
        if ratio > 0.5:
            # Green to Yellow
            # ratio 1.0 -> (0, 255, 0)
            # ratio 0.5 -> (255, 255, 0)
            r = int(255 * (1 - (ratio - 0.5) * 2))
            g = 255
            b = 0
        else:
            # Yellow to Red
            # ratio 0.5 -> (255, 255, 0)
            # ratio 0.0 -> (255, 0, 0)
            r = 255
            g = int(255 * (ratio * 2))
            b = 0
        
        self.reentry_display.setStyleSheet(f"font-size: 48px; font-weight: bold; color: rgb({r}, {g}, {b});")

    def _on_reentry_finished(self):
        self.status_label.setText("Status: RE-ENTRY TIMER FINISHED!")
        self.sound_manager.play_sound(self.sound_path_edit.text())
        # Optional: Add some visual blink effect if needed

    def _update_area_timer_display(self, seconds):
        mins, secs = divmod(seconds, 60)
        self.area_timer_display.setText(f"{mins:02}:{secs:02}")
        
        limit = self.area_duration_spin.value()
        if limit <= 0: return
        
        ratio = seconds / limit
        if ratio > 1.0: ratio = 1.0
        
        if ratio < 0.5:
            # Green to Yellow
            # ratio 0.0 -> (0, 255, 0)
            # ratio 0.5 -> (255, 255, 0)
            r = int(255 * (ratio * 2))
            g = 255
            b = 0
        else:
            # Yellow to Red
            # ratio 0.5 -> (255, 255, 0)
            # ratio 1.0 -> (255, 0, 0)
            r = 255
            g = int(255 * (1 - (ratio - 0.5) * 2))
            b = 0
            
        self.area_timer_display.setStyleSheet(f"font-size: 48px; font-weight: bold; color: rgb({r}, {g}, {b});")

    def closeEvent(self, event):
        self._on_stop()
        self._save_settings()
        event.accept()
