"""Utilidades para convertir frames de OpenCV a Qt."""

import cv2
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap


def frame_to_pixmap(frame: np.ndarray, target_width: int, target_height: int) -> QPixmap:
    """Convierte un frame BGR de OpenCV a QPixmap escalado."""
    if frame is None or frame.size == 0:
        return QPixmap()

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    q_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

    pixmap = QPixmap.fromImage(q_image)
    return pixmap.scaled(
        target_width,
        target_height,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )

