import os
import time
from PySide6.QtCore import QObject, Signal, QRunnable, Slot

class LogWatcherSignals(QObject):
    new_event = Signal(dict)
    status_changed = Signal(str)
    error = Signal(str)

class LogWatcher(QRunnable):
    def __init__(self, file_path, parser):
        super().__init__()
        self.file_path = file_path
        self.parser = parser
        self.signals = LogWatcherSignals()
        self.is_running = True

    @Slot()
    def run(self):
        self.signals.status_changed.emit("Starting monitoring...")
        
        if not os.path.exists(self.file_path):
            self.signals.error.emit(f"File not found: {self.file_path}")
            return

        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Go to end of file
                f.seek(0, os.SEEK_END)
                self.signals.status_changed.emit("Waiting for new lines...")
                
                while self.is_running:
                    line = f.readline()
                    if not line:
                        # Check if file was truncated or rotated
                        current_size = os.path.getsize(self.file_path)
                        if current_size < f.tell():
                            f.seek(0)
                            self.signals.status_changed.emit("Log file rotated/cleared.")
                        else:
                            time.sleep(0.5)
                        continue
                    
                    event = self.parser.parse_line(line)
                    if event:
                        self.signals.new_event.emit(event)
        except Exception as e:
            self.signals.error.emit(f"Read error: {str(e)}")

    def stop(self):
        self.is_running = False
