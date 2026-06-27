import json
import os

DEFAULT_CONFIG = {
    "game_path": "",
    "tracked_areas": [
        "Map*",
        "Expedition*"
    ],
    "reentry_timer_duration": 320,  # Updated to user preference
    "area_timer_limit": 300,       # seconds (for gradient)
    "maps_completed": 0,           # Counter
    "auto_start": True,            # Preferred by user
    "mini_mode": False,            
    "mini_scale": 1.0,             
    "sound_file": "",
    "sound_volume": 100,
    "ui_settings": {}
}

class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.data = self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except Exception:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()
