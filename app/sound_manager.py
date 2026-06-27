from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QObject

class SoundManager(QObject):
    def __init__(self):
        super().__init__()
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(1.0)

    def play_sound(self, file_path=None):
        if file_path and isinstance(file_path, str) and file_path.strip():
            url = QUrl.fromLocalFile(file_path)
            self._player.setSource(url)
            self._player.play()
        else:
            # Fallback to system sound could be added here if needed
            # For now, if no path, we do nothing or could play a default resource
            pass

    def set_volume(self, volume: float):
        self._audio_output.setVolume(max(0.0, min(1.0, volume)))

    def get_volume(self) -> float:
        return self._audio_output.volume()

    def stop(self):
        self._player.stop()
