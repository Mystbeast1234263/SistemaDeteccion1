"""Panel central de visualización de video."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from video.frame_utils import frame_to_pixmap


class VideoPanel(QFrame):
    """Área principal donde se muestra video o webcam."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("videoFrame")
        self._cached_w = 0
        self._cached_h = 0
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QWidget()
        header.setObjectName("videoHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.overlay_label = QLabel("SIN SEÑAL — ESPERANDO FUENTE DE VIDEO")
        self.overlay_label.setObjectName("videoOverlayTitle")
        self.overlay_label.setAlignment(Qt.AlignLeft)
        header_layout.addWidget(self.overlay_label)

        self.display = QLabel()
        self.display.setObjectName("videoDisplay")
        self.display.setAlignment(Qt.AlignCenter)
        self.display.setMinimumSize(640, 400)
        self.display.setText(
            "AREA DE MONITOREO\n\n"
            "Importe un video o active la webcam\n"
            "para iniciar la vigilancia inteligente"
        )
        self.display.setScaledContents(False)

        layout.addWidget(header)
        layout.addWidget(self.display, stretch=1)

    def show_frame(self, frame, source_label: str = "") -> None:
        """Muestra un frame de OpenCV en el panel."""
        if source_label:
            self.overlay_label.setText(source_label.upper())

        w = self.display.width()
        h = self.display.height()
        if w < 64 or h < 64:
            w, h = 640, 400

        if w != self._cached_w or h != self._cached_h:
            self._cached_w = w
            self._cached_h = h

        pixmap = frame_to_pixmap(frame, w, h, fast=True)
        if not pixmap.isNull():
            self.display.setPixmap(pixmap)
            self.display.setText("")

    def clear_display(self, message: str = None) -> None:
        """Limpia el área de video."""
        self._cached_w = 0
        self._cached_h = 0
        self.display.setPixmap(QPixmap())
        self.display.setText(
            message
            or "AREA DE MONITOREO\n\n"
            "Importe un video o active la webcam\n"
            "para iniciar la vigilancia inteligente"
        )
        self.overlay_label.setText("SIN SEÑAL — ESPERANDO FUENTE DE VIDEO")

    def set_overlay(self, text: str) -> None:
        self.overlay_label.setText(text)
