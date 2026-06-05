"""Barra de tiempo inteligente con marcas de segmentos sospechosos."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

from ml.segment_tracker import SegmentType, TimelineSegment
from utils.constants import COLORS


class TimelineSlider(QSlider):
    """Slider con marcas de segmentos pintadas."""

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self._segments: list[TimelineSegment] = []
        self._duration = 0.0

    def set_duration(self, duration: float) -> None:
        self._duration = max(duration, 0.001)
        self.setRange(0, int(self._duration * 1000))

    def set_position(self, seconds: float) -> None:
        self.blockSignals(True)
        self.setValue(int(seconds * 1000))
        self.blockSignals(False)

    def set_segments(self, segments: list[TimelineSegment]) -> None:
        self._segments = segments
        self.update()

    marker_clicked = pyqtSignal(float)

    def mousePressEvent(self, event) -> None:
        if self._duration > 0 and self._segments and event.button() == Qt.LeftButton:
            margin = 12
            track_left = margin
            track_width = self.width() - 2 * margin
            click_x = event.pos().x()
            nearest = None
            min_dist = 12

            for seg in self._segments:
                ratio = seg.time_sec / self._duration
                x = int(track_left + ratio * track_width)
                if abs(click_x - x) <= min_dist:
                    min_dist = abs(click_x - x)
                    nearest = seg.time_sec

            if nearest is not None:
                self.marker_clicked.emit(nearest)
                return

        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self._segments or self._duration <= 0:
            return

        painter = QPainter(self)
        groove = self.rect()
        margin = 12
        track_left = margin
        track_width = groove.width() - 2 * margin
        track_y = groove.height() // 2 + 8

        for seg in self._segments:
            ratio = seg.time_sec / self._duration
            x = int(track_left + ratio * track_width)

            if seg.segment_type == SegmentType.SUSPICIOUS:
                color = QColor("#ff0033")
                h = 10
            elif seg.segment_type == SegmentType.HIGH:
                color = QColor("#ff3366")
                h = 8
            else:
                color = QColor("#ffaa00")
                h = 6

            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRect(x - 2, track_y - h // 2, 4, h)

        painter.end()


class TimelineBar(QWidget):
    """Barra de progreso tipo YouTube con navegación por eventos."""

    seek_requested = pyqtSignal(float)
    marker_clicked = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("timelineBar")
        self._duration = 0.0
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        time_row = QHBoxLayout()
        self.lbl_current = QLabel("00:00")
        self.lbl_current.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        self.lbl_total = QLabel("00:00")
        self.lbl_total.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        self.lbl_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        time_row.addWidget(self.lbl_current)
        time_row.addStretch()
        time_row.addWidget(self.lbl_total)
        layout.addLayout(time_row)

        self.slider = TimelineSlider()
        self.slider.setObjectName("timelineSlider")
        self.slider.sliderMoved.connect(self._on_slider_moved)
        self.slider.sliderReleased.connect(self._on_slider_released)
        self.slider.marker_clicked.connect(self.marker_clicked.emit)
        layout.addWidget(self.slider)

        legend = QLabel("Amarillo: riesgo medio | Rojo: riesgo alto | Rojo intenso: sospechoso")
        legend.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px;")
        layout.addWidget(legend)

    def set_duration(self, duration: float) -> None:
        self._duration = duration
        self.slider.set_duration(duration)
        self.lbl_total.setText(self._format_time(duration))
        self.setEnabled(duration > 0)

    def set_position(self, seconds: float) -> None:
        self.slider.set_position(seconds)
        self.lbl_current.setText(self._format_time(seconds))

    def set_segments(self, segments: list[TimelineSegment]) -> None:
        self.slider.set_segments(segments)

    def reset(self) -> None:
        self._duration = 0.0
        self.slider.set_duration(0)
        self.slider.set_position(0)
        self.slider.set_segments([])
        self.lbl_current.setText("00:00")
        self.lbl_total.setText("00:00")
        self.setEnabled(False)

    def _on_slider_moved(self, value: int) -> None:
        seconds = value / 1000.0
        self.lbl_current.setText(self._format_time(seconds))

    def _on_slider_released(self) -> None:
        seconds = self.slider.value() / 1000.0
        self.seek_requested.emit(seconds)

    @staticmethod
    def _format_time(seconds: float) -> str:
        seconds = max(0, int(seconds))
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
