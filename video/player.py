"""Reproductor de archivos de video con OpenCV."""

import cv2
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from utils.constants import DEFAULT_FPS


class VideoPlayer(QObject):
    """Lee y reproduce un archivo de video frame a frame."""

    frame_ready = pyqtSignal(object)
    playback_finished = pyqtSignal()
    position_changed = pyqtSignal(float, float)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._capture = None
        self._path = ""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._read_next_frame)
        self._fps = DEFAULT_FPS
        self._playing = False
        self._total_frames = 0
        self._current_frame = 0
        self._duration = 0.0

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def source_path(self) -> str:
        return self._path

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def current_time(self) -> float:
        if self._fps <= 0:
            return 0.0
        return self._current_frame / self._fps

    @property
    def fps(self) -> float:
        return self._fps

    def load(self, path: str) -> bool:
        """Carga un archivo de video. Retorna True si fue exitoso."""
        self.stop()
        capture = cv2.VideoCapture(path)
        if not capture.isOpened():
            capture.release()
            self.error_occurred.emit(f"No se pudo abrir el video: {path}")
            return False

        fps = capture.get(cv2.CAP_PROP_FPS)
        self._fps = fps if fps and fps > 0 else DEFAULT_FPS
        self._total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self._duration = self._total_frames / self._fps if self._fps else 0.0
        self._current_frame = 0
        self._capture = capture
        self._path = path
        self.position_changed.emit(0.0, self._duration)
        return True

    def play(self) -> None:
        """Inicia la reproducción."""
        if self._capture is None or not self._capture.isOpened():
            self.error_occurred.emit("No hay video cargado.")
            return

        interval_ms = max(1, int(1000 / self._fps))
        self._timer.setInterval(interval_ms)
        self._playing = True
        self._timer.start()

    def pause(self) -> None:
        """Pausa la reproducción."""
        self._timer.stop()
        self._playing = False

    def stop(self) -> None:
        """Detiene y libera el recurso de video."""
        self._timer.stop()
        self._playing = False
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._path = ""
        self._total_frames = 0
        self._current_frame = 0
        self._duration = 0.0

    def seek_start(self) -> None:
        """Reinicia el video al inicio."""
        self.seek_seconds(0.0)

    def seek_seconds(self, seconds: float) -> None:
        """Salta a una posición en segundos."""
        if self._capture is None or not self._capture.isOpened():
            return

        seconds = max(0.0, min(seconds, self._duration))
        frame_idx = int(seconds * self._fps)
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        self._current_frame = frame_idx
        self.position_changed.emit(self.current_time, self._duration)

        ret, frame = self._capture.read()
        if ret:
            self._current_frame = frame_idx + 1
            self.frame_ready.emit(frame)
            self.position_changed.emit(self.current_time, self._duration)

    def _read_next_frame(self) -> None:
        if self._capture is None:
            return

        ret, frame = self._capture.read()
        if not ret:
            self._timer.stop()
            self._playing = False
            self.playback_finished.emit()
            return

        self._current_frame += 1
        self.position_changed.emit(self.current_time, self._duration)
        self.frame_ready.emit(frame)
