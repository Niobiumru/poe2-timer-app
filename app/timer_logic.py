from PySide6.QtCore import QObject, QTimer, Signal

class TimerLogic(QObject):
    reentry_tick = Signal(int)  # remaining seconds
    reentry_finished = Signal()
    area_tick = Signal(int)     # elapsed seconds
    
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
            
        elif event["type"] == "area":
            area_name = event["value"]
            if area_name in tracked_areas:
                # Always start/reset reentry timer when entering a tracked area
                self.start_reentry(reentry_duration)
                
                # Check if it's a NEW instance to reset area timer
                if self.pending_instance_id and self.pending_instance_id != self.last_instance_id:
                    self.last_instance_id = self.pending_instance_id
                    self.reset_area_timer()
                elif self.pending_instance_id == self.last_instance_id:
                    # Returning to the SAME instance, resume without reset
                    self.resume_area_timer()
                elif not self.last_instance_id and self.pending_instance_id:
                    # Initial case
                    self.last_instance_id = self.pending_instance_id
                    self.reset_area_timer()
            else:
                # Entering non-tracked area (Hideout, Town, etc.)
                self._reentry_timer.stop()
                self._reentry_remaining = 0
                self.reentry_tick.emit(0)
                
                # Pause global area timer
                self.pause_area_timer()
            
            # Clear pending after processing area
            self.pending_instance_id = None

    def stop_all(self):
        self._reentry_timer.stop()
        self._area_timer.stop()
        self.last_instance_id = None
        self.pending_instance_id = None
