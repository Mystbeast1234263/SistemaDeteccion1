"""Reproductor de archivos de video con OpenCV."""

import cv2
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from utils.constants import DEFAULT_FPS


class VideoPlayer(QObject):
    """Lee y reproduce un archivo de video frame a frame."""

    frame_ready = pyqtSignal(object)
    playback_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._capture = None
        self._path = ""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._read_next_frame)
        self._fps = DEFAULT_FPS
        self._playing = False

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def source_path(self) -> str:
        return self._path

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
        self._capture = capture
        self._path = path
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

    def seek_start(self) -> None:
        """Reinicia el video al inicio."""
        if self._capture is not None:
            self._capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def _read_next_frame(self) -> None:
        if self._capture is None:
            return

        ret, frame = self._capture.read()
        if not ret:
            self._timer.stop()
            self._playing = False
            self.playback_finished.emit()
            return

        self.frame_ready.emit(frame)

