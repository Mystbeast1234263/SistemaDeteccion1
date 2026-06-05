"""Seguimiento de segmentos sospechosos para la barra de tiempo."""

from dataclasses import dataclass
from enum import Enum


class SegmentType(Enum):
    MEDIUM = "medium"
    HIGH = "high"
    SUSPICIOUS = "suspicious"


@dataclass
class TimelineSegment:
    time_sec: float
    segment_type: SegmentType
    confidence: float = 0.0
    label: str = ""


class SegmentTracker:
    """Registra marcas de eventos sospechosos en la línea de tiempo."""

    def __init__(self):
        self._segments: list[TimelineSegment] = []
        self._last_mark: dict[float, float] = {}

    def reset(self) -> None:
        self._segments.clear()
        self._last_mark.clear()

    @property
    def segments(self) -> list[TimelineSegment]:
        return list(self._segments)

    def add_segment(
        self,
        time_sec: float,
        risk_level: str,
        prediction_label: str = "",
        confidence: float = 0.0,
        min_gap: float = 2.0,
    ) -> TimelineSegment | None:
        rounded = round(time_sec, 1)
        last = self._last_mark.get(rounded, -999.0)
        if time_sec - last < min_gap:
            return None

        if prediction_label == "SOSPECHOSO" and confidence >= 85:
            seg_type = SegmentType.SUSPICIOUS
        elif risk_level == "ALTO":
            seg_type = SegmentType.HIGH
        elif risk_level == "MEDIO":
            seg_type = SegmentType.MEDIUM
        else:
            return None

        segment = TimelineSegment(
            time_sec=time_sec,
            segment_type=seg_type,
            confidence=confidence,
            label=prediction_label,
        )
        self._segments.append(segment)
        self._last_mark[rounded] = time_sec
        return segment
