from PySide6.QtCore import QObject, QTimer, Signal

class TimerLogic(QObject):
    reentry_tick = Signal(int)  # remaining seconds
    reentry_finished = Signal()
    area_tick = Signal(int)     # elapsed seconds
    map_completed = Signal()    # New map instance detected
    log_message = Signal(str, str, str) # Level, Source, Message
    
    def __init__(self):
        super().__init__()
        
        # Reentry Countdown Timer
        self._reentry_timer = QTimer()
        self._reentry_timer.timeout.connect(self._on_reentry_timeout)
        self._reentry_remaining = 0
        
        # Area Count-up Timer
        self._area_timer = QTimer()
        self._area_timer.timeout.connect(self._on_area_timeout)
        self._area_elapsed = 0
        
        self.last_instance_id = None
        self.pending_instance_id = None

    def start_reentry(self, duration):
        self._reentry_remaining = duration
        self._reentry_timer.start(1000)
        self.reentry_tick.emit(self._reentry_remaining)

    def _on_reentry_timeout(self):
        if self._reentry_remaining > 0:
            self._reentry_remaining -= 1
            self.reentry_tick.emit(self._reentry_remaining)
            if self._reentry_remaining == 0:
                self._reentry_timer.stop()
                self.reentry_finished.emit()

    def reset_area_timer(self):
        self._area_elapsed = 0
        self._area_timer.start(1000)
        self.area_tick.emit(self._area_elapsed)

    def resume_area_timer(self):
        if not self._area_timer.isActive():
            self._area_timer.start(1000)

    def pause_area_timer(self):
        self._area_timer.stop()

    def _on_area_timeout(self):
        self._area_elapsed += 1
        self.area_tick.emit(self._area_elapsed)

    def handle_event(self, event, tracked_areas, reentry_duration):
        if event["type"] == "instance":
            self.pending_instance_id = event["value"]
            self.log_message.emit("INFO", "Parser", f"Client-Safe Instance ID = {event['value']}")
            
        elif event["type"] == "area":
            area_name = event["value"]
            self.log_message.emit("INFO", "Parser", f"Generating level area \"{area_name}\"")
            
            if area_name in tracked_areas:
                self.log_message.emit("INFO", "Timer", f"Re-entry timer started for {area_name} ({reentry_duration} seconds)")
                self.start_reentry(reentry_duration)
                
                if self.pending_instance_id and self.pending_instance_id != self.last_instance_id:
                    self.last_instance_id = self.pending_instance_id
                    self.log_message.emit("INFO", "Timer", "New map instance detected. Resetting global timer.")
                    self.reset_area_timer()
                    self.map_completed.emit()
                elif self.pending_instance_id == self.last_instance_id:
                    self.log_message.emit("INFO", "Timer", "Returning to same instance. Resuming global timer.")
                    self.resume_area_timer()
                elif not self.last_instance_id and self.pending_instance_id:
                    self.last_instance_id = self.pending_instance_id
                    self.log_message.emit("INFO", "Timer", "Initial map instance. Starting global timer.")
                    self.reset_area_timer()
                    self.map_completed.emit()
            else:
                self.log_message.emit("INFO", "Timer", f"Entered non-tracked area \"{area_name}\". Pausing timers.")
                self._reentry_timer.stop()
                self._reentry_remaining = 0
                self.reentry_tick.emit(0)
                self.pause_area_timer()
            
            self.pending_instance_id = None

    def stop_all(self):
        self._reentry_timer.stop()
        self._area_timer.stop()
        self.last_instance_id = None
        self.pending_instance_id = None
