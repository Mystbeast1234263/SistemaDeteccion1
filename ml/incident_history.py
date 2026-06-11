"""Historial persistente de incidentes detectados."""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from utils.constants import INCIDENTS_PATH, SORT_CONFIDENCE_DESC, SORT_DATE_ASC, SORT_DATE_DESC, SORT_RISK_DESC
from utils.suspicious_labels import (
    SUSPICIOUS_SORT_ORDER,
    format_suspicious_display,
    suspicious_label_from_confidence,
)


@dataclass
class IncidentRecord:
    """Registro de un evento detectado durante el monitoreo."""

    id: str
    datetime: str
    time_display: str
    event_type: str
    confidence: float
    risk_level: str  # Etiqueta de sospecha: NORMAL, SOSPECHOSO, SOSPECHOSO ALTO
    file_path: str = ""
    file_type: str = ""
    video_time_sec: float = 0.0

    @classmethod
    def create(
        cls,
        event_type: str,
        confidence: float = 0.0,
        risk_level: str = "BAJO",  # ignorado; se calcula desde confianza
        file_path: str = "",
        file_type: str = "",
        video_time_sec: float = 0.0,
    ) -> "IncidentRecord":
        now = datetime.now()
        suspicious = suspicious_label_from_confidence(confidence)
        return cls(
            id=str(uuid.uuid4())[:8],
            datetime=now.strftime("%Y-%m-%d %H:%M:%S"),
            time_display=now.strftime("%H:%M"),
            event_type=event_type,
            confidence=round(confidence, 1),
            risk_level=suspicious,
            file_path=file_path,
            file_type=file_type,
            video_time_sec=round(video_time_sec, 1),
        )

    @classmethod
    def from_dict(cls, data: dict) -> "IncidentRecord":
        return cls(
            id=data.get("id", ""),
            datetime=data.get("datetime", ""),
            time_display=data.get("time_display", ""),
            event_type=data.get("event_type", ""),
            confidence=float(data.get("confidence", 0)),
            risk_level=data.get("risk_level", "BAJO"),
            file_path=data.get("file_path", ""),
            file_type=data.get("file_type", ""),
            video_time_sec=float(data.get("video_time_sec", 0)),
        )

    @property
    def suspicious_label(self) -> str:
        return format_suspicious_display(self.confidence, self.risk_level)


class IncidentHistory:
    """Gestiona incidentes en evidence/incidents.json."""

    def __init__(self, path: Path = INCIDENTS_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._records: list[IncidentRecord] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._records = []
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            self._records = [IncidentRecord.from_dict(r) for r in data.get("incidents", [])]
        except (json.JSONDecodeError, OSError):
            self._records = []

    def save(self) -> None:
        payload = {"incidents": [asdict(r) for r in self._records]}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def add(self, record: IncidentRecord) -> IncidentRecord:
        self._records.insert(0, record)
        self.save()
        return record

    def add_event(
        self,
        event_type: str,
        confidence: float = 0.0,
        file_path: str = "",
        file_type: str = "",
        video_time_sec: float = 0.0,
    ) -> IncidentRecord:
        record = IncidentRecord.create(
            event_type=event_type,
            confidence=confidence,
            file_path=file_path,
            file_type=file_type,
            video_time_sec=video_time_sec,
        )
        return self.add(record)

    @property
    def records(self) -> list[IncidentRecord]:
        return list(self._records)

    def get_sorted(self, sort_key: str) -> list[IncidentRecord]:
        items = list(self._records)
        if sort_key == SORT_DATE_ASC:
            return sorted(items, key=lambda r: r.datetime)
        if sort_key == SORT_RISK_DESC:
            return sorted(
                items,
                key=lambda r: (SUSPICIOUS_SORT_ORDER.get(r.suspicious_label, 0), r.confidence),
                reverse=True,
            )
        if sort_key == SORT_CONFIDENCE_DESC:
            return sorted(items, key=lambda r: r.confidence, reverse=True)
        return items
