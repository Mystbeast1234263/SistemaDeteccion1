"""Utilidades para convertir frames de OpenCV a Qt."""

import cv2
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

from utils.constants import DISPLAY_MAX_HEIGHT, DISPLAY_MAX_WIDTH


def frame_to_pixmap(
    frame: np.ndarray,
    target_width: int,
    target_height: int,
    fast: bool = True,
    max_width: int = DISPLAY_MAX_WIDTH,
    max_height: int = DISPLAY_MAX_HEIGHT,
) -> QPixmap:
    """Convierte un frame BGR de OpenCV a QPixmap escalado (optimizado para fluidez)."""
    if frame is None or frame.size == 0:
        return QPixmap()

    cap_w = min(target_width, max_width)
    cap_h = min(target_height, max_height)

    h, w = frame.shape[:2]
    scale = min(cap_w / w, cap_h / h, 1.0)

    if scale < 1.0:
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        interp = cv2.INTER_AREA if scale < 0.5 else cv2.INTER_LINEAR
        frame = cv2.resize(frame, (new_w, new_h), interpolation=interp)
        h, w = frame.shape[:2]

    rgb = np.ascontiguousarray(frame[:, :, ::-1])
    bytes_per_line = 3 * w
    q_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(q_image)

    if w != cap_w or h != cap_h:
        transform = Qt.FastTransformation if fast else Qt.SmoothTransformation
        pixmap = pixmap.scaled(
            cap_w,
            cap_h,
            Qt.KeepAspectRatio,
            transform,
        )
    return pixmap
