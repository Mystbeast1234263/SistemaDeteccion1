"""Utilidades para convertir frames de OpenCV a Qt."""

import cv2
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap


def frame_to_pixmap(
    frame: np.ndarray,
    target_width: int,
    target_height: int,
    fast: bool = True,
) -> QPixmap:
    """Convierte un frame BGR de OpenCV a QPixmap escalado."""
    if frame is None or frame.size == 0:
        return QPixmap()

    h, w = frame.shape[:2]
    scale = min(target_width / w, target_height / h, 1.0)

    if scale < 1.0:
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        interp = cv2.INTER_AREA if scale < 0.5 else cv2.INTER_LINEAR
        frame = cv2.resize(frame, (new_w, new_h), interpolation=interp)
        h, w = frame.shape[:2]

    rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    bytes_per_line = 3 * w
    q_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

    transform = Qt.FastTransformation if fast else Qt.SmoothTransformation
    return QPixmap.fromImage(q_image).scaled(
        target_width,
        target_height,
        Qt.KeepAspectRatio,
        transform,
    )
