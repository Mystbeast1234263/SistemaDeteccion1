"""Reproductor de archivos de video con OpenCV."""

import time

import cv2
from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal

from utils.constants import (
    DEFAULT_FPS,
    PLAYBACK_DISPLAY_FPS,
    TARGET_FPS,
    VIDEO_BUFFER_SIZE,
)


class VideoPlayer(QObject):
    """Reproduce video a 60 FPS en pantalla respetando la velocidad del archivo."""

    frame_ready = pyqtSignal(object)
    playback_finished = pyqtSignal()
    position_changed = pyqtSignal(float, float)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._capture = None
        self._path = ""
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._read_next_frame)
        self._fps = DEFAULT_FPS
        self._playing = False
        self._total_frames = 0
        self._current_frame = 0
        self._duration = 0.0
        self._last_tick = 0.0
        self._time_debt = 0.0
        self._display_frame = None
        self._position_emit_counter = 0

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

    @property
    def display_fps(self) -> float:
        return float(PLAYBACK_DISPLAY_FPS)

    def load(self, path: str) -> bool:
        """Carga un archivo de video. Retorna True si fue exitoso."""
        self.stop()
        capture = cv2.VideoCapture(path, cv2.CAP_FFMPEG)
        if not capture.isOpened():
            capture = cv2.VideoCapture(path)
        if not capture.isOpened():
            capture.release()
            self.error_occurred.emit(f"No se pudo abrir el video: {path}")
            return False

        fps = capture.get(cv2.CAP_PROP_FPS)
        self._fps = min(fps if fps and fps > 0 else DEFAULT_FPS, TARGET_FPS)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, VIDEO_BUFFER_SIZE)
        self._total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self._duration = self._total_frames / self._fps if self._fps else 0.0
        self._current_frame = 0
        self._display_frame = None
        self._time_debt = 0.0
        self._capture = capture
        self._path = path
        self.position_changed.emit(0.0, self._duration)
        return True

    def play(self) -> None:
        """Inicia reproduccion fluida a 60 FPS en pantalla."""
        if self._capture is None or not self._capture.isOpened():
            self.error_occurred.emit("No hay video cargado.")
            return

        self._last_tick = time.perf_counter()
        self._time_debt = 0.0
        interval_ms = max(1, int(1000 / PLAYBACK_DISPLAY_FPS))
        self._timer.setInterval(interval_ms)
        self._playing = True
        self._timer.start()

    def pause(self) -> None:
        """Pausa la reproduccion."""
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
        self._display_frame = None
        self._time_debt = 0.0
        self._position_emit_counter = 0

    def seek_start(self) -> None:
        """Reinicia el video al inicio."""
        self.seek_seconds(0.0)

    def seek_seconds(self, seconds: float) -> None:
        """Salta a una posicion en segundos."""
        if self._capture is None or not self._capture.isOpened():
            return

        seconds = max(0.0, min(seconds, self._duration))
        frame_idx = int(seconds * self._fps)
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        self._current_frame = frame_idx
        self._time_debt = 0.0
        self.position_changed.emit(self.current_time, self._duration)

        ret, frame = self._capture.read()
        if ret:
            self._display_frame = frame
            self._current_frame = frame_idx + 1
            self.frame_ready.emit(frame)
            self.position_changed.emit(self.current_time, self._duration)

    def _read_next_frame(self) -> None:
        if self._capture is None:
            return

        now = time.perf_counter()
        dt = now - self._last_tick
        self._last_tick = now

        source_interval = 1.0 / self._fps if self._fps > 0 else 1.0 / DEFAULT_FPS
        self._time_debt += dt

        while self._time_debt >= source_interval:
            ret, frame = self._capture.read()
            if not ret or frame is None:
                self._timer.stop()
                self._playing = False
                self.playback_finished.emit()
                return
            self._display_frame = frame
            self._current_frame += 1
            self._time_debt -= source_interval

        if self._display_frame is None:
            return

        self._position_emit_counter += 1
        if self._position_emit_counter % 6 == 0:
            self.position_changed.emit(self.current_time, self._duration)

        self.frame_ready.emit(self._display_frame)
