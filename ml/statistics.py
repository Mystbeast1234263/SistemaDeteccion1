"""Estadísticas de la sesión de análisis y métricas avanzadas Sprint 5."""

from dataclasses import dataclass
from datetime import datetime

from utils.constants import TARGET_FPS


@dataclass
class SessionStatistics:
    total_alerts: int = 0
    total_suspicious: int = 0
    time_analyzed_sec: float = 0.0
    risk_sum: int = 0
    risk_samples: int = 0
    captures_count: int = 0
    clips_count: int = 0

    frames_processed: int = 0
    fps_sum: float = 0.0
    fps_samples: int = 0
    sessions_count: int = 0

    intensity_sum: int = 0
    intensity_min: int = 100
    intensity_max: int = 0
    intensity_samples: int = 0

    magnitude_sum: float = 0.0
    magnitude_samples: int = 0
    direction_sum: float = 0.0
    direction_samples: int = 0

    risk_low_count: int = 0
    risk_medium_count: int = 0
    risk_high_count: int = 0

    confidence_sum: float = 0.0
    confidence_max: float = 0.0
    confidence_samples: int = 0
    suspicious_predictions: int = 0

    last_evidence_at: str = ""
    session_started_at: str = ""

    def add_alert(self) -> None:
        self.total_alerts += 1

    def add_suspicious(self) -> None:
        self.total_suspicious += 1

    def add_time(self, seconds: float) -> None:
        self.time_analyzed_sec += seconds

    def add_risk_sample(self, intensity: int) -> None:
        self.risk_sum += intensity
        self.risk_samples += 1

    def add_capture(self) -> None:
        self.captures_count += 1
        self.last_evidence_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def add_clip(self) -> None:
        self.clips_count += 1
        self.last_evidence_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def add_frame(self, fps: float = 60.0) -> None:
        self.frames_processed += 1
        self.fps_sum += fps
        self.fps_samples += 1

    def add_motion_sample(
        self,
        intensity: int,
        magnitude: float,
        direction: float,
        risk_level: str,
    ) -> None:
        self.intensity_sum += intensity
        self.intensity_min = min(self.intensity_min, intensity)
        self.intensity_max = max(self.intensity_max, intensity)
        self.intensity_samples += 1
        self.magnitude_sum += magnitude
        self.magnitude_samples += 1
        self.direction_sum += direction
        self.direction_samples += 1

        risk = (risk_level or "BAJO").upper()
        if risk == "ALTO":
            self.risk_high_count += 1
        elif risk == "MEDIO":
            self.risk_medium_count += 1
        else:
            self.risk_low_count += 1

    def add_prediction(self, label: str, confidence: float) -> None:
        if label.upper() == "SOSPECHOSO":
            self.suspicious_predictions += 1
            self.confidence_sum += confidence
            self.confidence_max = max(self.confidence_max, confidence)
            self.confidence_samples += 1

    def begin_session(self) -> None:
        self.sessions_count += 1
        self.session_started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def avg_risk(self) -> float:
        if self.risk_samples == 0:
            return 0.0
        return round(self.risk_sum / self.risk_samples, 1)

    @property
    def avg_intensity(self) -> float:
        if self.intensity_samples == 0:
            return 0.0
        return round(self.intensity_sum / self.intensity_samples, 1)

    @property
    def avg_magnitude(self) -> float:
        if self.magnitude_samples == 0:
            return 0.0
        return round(self.magnitude_sum / self.magnitude_samples, 3)

    @property
    def avg_direction(self) -> float:
        if self.direction_samples == 0:
            return 0.0
        return round(self.direction_sum / self.direction_samples, 1)

    @property
    def avg_fps(self) -> float:
        if self.fps_samples == 0:
            return 0.0
        return round(self.fps_sum / self.fps_samples, 1)

    @property
    def avg_confidence(self) -> float:
        if self.confidence_samples == 0:
            return 0.0
        return round(self.confidence_sum / self.confidence_samples, 1)

    @property
    def suspicious_rate(self) -> float:
        if self.frames_processed == 0:
            return 0.0
        return round(self.suspicious_predictions / self.frames_processed * 100, 2)

    def reset(self) -> None:
        self.total_alerts = 0
        self.total_suspicious = 0
        self.time_analyzed_sec = 0.0
        self.risk_sum = 0
        self.risk_samples = 0
        self.captures_count = 0
        self.clips_count = 0
        self.frames_processed = 0
        self.fps_sum = 0.0
        self.fps_samples = 0
        self.intensity_sum = 0
        self.intensity_min = 100
        self.intensity_max = 0
        self.intensity_samples = 0
        self.magnitude_sum = 0.0
        self.magnitude_samples = 0
        self.direction_sum = 0.0
        self.direction_samples = 0
        self.risk_low_count = 0
        self.risk_medium_count = 0
        self.risk_high_count = 0
        self.confidence_sum = 0.0
        self.confidence_max = 0.0
        self.confidence_samples = 0
        self.suspicious_predictions = 0
        self.last_evidence_at = ""
        self.session_started_at = ""

    @property
    def risk_event_total(self) -> int:
        return self.risk_low_count + self.risk_medium_count + self.risk_high_count

    @property
    def fps_efficiency_pct(self) -> float:
        target = float(TARGET_FPS)
        if self.avg_fps <= 0:
            return 0.0
        return round(min(self.avg_fps / target * 100, 100.0), 1)

    @property
    def alert_rate_pct(self) -> float:
        if self.frames_processed == 0:
            return 0.0
        return round(self.total_alerts / self.frames_processed * 100, 2)

    @property
    def suspicious_detect_rate_pct(self) -> float:
        if self.frames_processed == 0:
            return 0.0
        return round(self.total_suspicious / self.frames_processed * 100, 2)

    @property
    def evidence_rate_pct(self) -> float:
        total_ev = self.captures_count + self.clips_count
        base = max(self.total_suspicious, 1)
        return round(total_ev / base * 100, 1)

    def _risk_pct(self, count: int) -> float:
        total = self.risk_event_total
        if total == 0:
            return 0.0
        return round(count / total * 100, 1)

    def as_dict(self) -> dict:
        return {
            "total_alerts": f"{self.alert_rate_pct}%",
            "total_alerts_raw": self.total_alerts,
            "total_suspicious": f"{self.suspicious_detect_rate_pct}%",
            "time_analyzed": self._format_time(self.time_analyzed_sec),
            "avg_risk": f"{self.avg_risk}%",
            "captures": f"{self.evidence_rate_pct}%",
            "clips": f"{self.clips_count}",
        }

    def as_advanced_dict(self) -> dict:
        intensity_min = self.intensity_min if self.intensity_samples else 0
        total_risk = self.risk_event_total
        total_ev = self.captures_count + self.clips_count
        return {
            "activity": {
                "time_analyzed": self._format_time(self.time_analyzed_sec),
                "time_analyzed_sec": round(self.time_analyzed_sec, 1),
                "frames_processed": self.frames_processed,
                "avg_fps": self.avg_fps,
                "fps_efficiency_pct": self.fps_efficiency_pct,
                "sessions_count": self.sessions_count,
                "session_started_at": self.session_started_at,
            },
            "movement": {
                "avg_intensity": self.avg_intensity,
                "max_intensity": self.intensity_max,
                "min_intensity": intensity_min,
                "avg_magnitude": self.avg_magnitude,
                "avg_direction": self.avg_direction,
                "avg_intensity_pct": f"{self.avg_intensity}%",
                "max_intensity_pct": f"{self.intensity_max}%",
                "min_intensity_pct": f"{intensity_min}%",
            },
            "risk": {
                "low_events": self.risk_low_count,
                "medium_events": self.risk_medium_count,
                "high_events": self.risk_high_count,
                "low_pct": self._risk_pct(self.risk_low_count),
                "medium_pct": self._risk_pct(self.risk_medium_count),
                "high_pct": self._risk_pct(self.risk_high_count),
                "avg_risk": self.avg_risk,
                "avg_risk_pct": f"{self.avg_risk}%",
            },
            "suspicious": {
                "total_detected": self.total_suspicious,
                "predictions": self.suspicious_predictions,
                "avg_confidence": self.avg_confidence,
                "max_confidence": self.confidence_max,
                "suspicious_rate": self.suspicious_rate,
                "detect_rate_pct": self.suspicious_detect_rate_pct,
                "avg_confidence_pct": f"{self.avg_confidence}%",
                "max_confidence_pct": f"{self.confidence_max}%",
            },
            "evidence": {
                "captures": self.captures_count,
                "clips": self.clips_count,
                "total": total_ev,
                "evidence_rate_pct": self.evidence_rate_pct,
                "last_evidence_at": self.last_evidence_at or "—",
            },
            "alerts": {
                "total": self.total_alerts,
                "alert_rate_pct": self.alert_rate_pct,
            },
        }

    @staticmethod
    def _format_time(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
