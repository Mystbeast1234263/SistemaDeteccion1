"""Captura de video desde webcam."""

import cv2
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from utils.constants import DEFAULT_FPS, WEBCAM_INDEX


class WebcamCapture(QObject):
    """Captura frames en tiempo real desde la cámara."""

    frame_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    started = pyqtSignal()
    stopped = pyqtSignal()

    def __init__(self, camera_index: int = WEBCAM_INDEX, parent=None):
        super().__init__(parent)
        self._camera_index = camera_index
        self._capture = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._read_frame)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def start(self) -> bool:
        """Abre la webcam e inicia la captura."""
        if self._active:
            return True

        capture = cv2.VideoCapture(self._camera_index, cv2.CAP_DSHOW)
        if not capture.isOpened():
            capture = cv2.VideoCapture(self._camera_index)
        if not capture.isOpened():
            self.error_occurred.emit(
                "No se pudo acceder a la webcam. Verifique que esté conectada."
            )
            return False

        self._capture = capture
        self._timer.setInterval(int(1000 / DEFAULT_FPS))
        self._active = True
        self._timer.start()
        self.started.emit()
        return True

    def stop(self) -> None:
        """Detiene la captura y libera la cámara."""
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

        ret, frame = self._capture.read()
        if not ret:
            self.error_occurred.emit("Error al leer frame de la webcam.")
            self.stop()
            return

        self.frame_ready.emit(frame)

