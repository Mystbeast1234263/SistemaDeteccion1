"""Estadísticas de la sesión de análisis."""

from dataclasses import dataclass, field


@dataclass
class SessionStatistics:
    total_alerts: int = 0
    total_suspicious: int = 0
    time_analyzed_sec: float = 0.0
    risk_sum: int = 0
    risk_samples: int = 0
    captures_count: int = 0
    clips_count: int = 0

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

    def add_clip(self) -> None:
        self.clips_count += 1

    @property
    def avg_risk(self) -> float:
        if self.risk_samples == 0:
            return 0.0
        return round(self.risk_sum / self.risk_samples, 1)

    def reset(self) -> None:
        self.total_alerts = 0
        self.total_suspicious = 0
        self.time_analyzed_sec = 0.0
        self.risk_sum = 0
        self.risk_samples = 0
        self.captures_count = 0
        self.clips_count = 0

    def as_dict(self) -> dict:
        return {
            "total_alerts": self.total_alerts,
            "total_suspicious": self.total_suspicious,
            "time_analyzed": self._format_time(self.time_analyzed_sec),
            "avg_risk": f"{self.avg_risk}%",
            "captures": self.captures_count,
            "clips": self.clips_count,
        }

    @staticmethod
    def _format_time(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
