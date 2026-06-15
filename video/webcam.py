"""Captura de video desde webcam."""

import cv2
from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal

from utils.constants import (
    VIDEO_BUFFER_SIZE,
    WEBCAM_CAPTURE_HEIGHT,
    WEBCAM_CAPTURE_WIDTH,
    WEBCAM_DROP_BUFFERS,
    WEBCAM_INDEX,
    WEBCAM_TARGET_FPS,
)


class WebcamCapture(QObject):
    """Captura webcam a 60 FPS con resolucion optimizada para fluidez."""

    frame_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    started = pyqtSignal()
    stopped = pyqtSignal()

    def __init__(self, camera_index: int = WEBCAM_INDEX, parent=None):
        super().__init__(parent)
        self._camera_index = camera_index
        self._capture = None
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._read_frame)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def target_fps(self) -> float:
        return float(WEBCAM_TARGET_FPS)

    def start(self) -> bool:
        """Abre la webcam e inicia captura a 60 FPS."""
        if self._active:
            return True

        capture = cv2.VideoCapture(self._camera_index, cv2.CAP_DSHOW)
        if not capture.isOpened():
            capture = cv2.VideoCapture(self._camera_index)
        if not capture.isOpened():
            self.error_occurred.emit(
                "No se pudo acceder a la webcam. Verifique que este conectada."
            )
            return False

        capture.set(cv2.CAP_PROP_BUFFERSIZE, VIDEO_BUFFER_SIZE)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_CAPTURE_WIDTH)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_CAPTURE_HEIGHT)
        capture.set(cv2.CAP_PROP_FPS, WEBCAM_TARGET_FPS)
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        self._capture = capture
        interval = max(1, int(1000 / WEBCAM_TARGET_FPS))
        self._timer.setInterval(interval)
        self._active = True
        self._timer.start()
        self.started.emit()
        return True

    def stop(self) -> None:
        """Detiene la captura y libera la camara."""
        if not self._active and self._capture is None:
            return

        was_active = self._active
        self._active = False
        self._timer.stop()

        capture = self._capture
        self._capture = None
        if capture is not None:
            capture.release()

        if was_active:
            self.stopped.emit()

    def _read_frame(self) -> None:
        if not self._active or self._capture is None:
            return

        for _ in range(WEBCAM_DROP_BUFFERS):
            if not self._capture.grab():
                break

        ret, frame = self._capture.retrieve()
        if not ret or frame is None:
            ret, frame = self._capture.read()
        if not ret or frame is None:
            self.error_occurred.emit("Error al leer frame de la webcam.")
            self.stop()
            return

        self.frame_ready.emit(frame)
