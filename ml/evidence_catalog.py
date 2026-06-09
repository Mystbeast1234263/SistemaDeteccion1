"""Catálogo de evidencias en disco (capturas, clips e incidentes)."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ml.incident_history import IncidentHistory, IncidentRecord
from utils.constants import (
    EVIDENCE_CLIPS_DIR,
    EVIDENCE_DIR,
    EVIDENCE_SCREENSHOTS_DIR,
    SORT_CONFIDENCE_DESC,
    SORT_DATE_ASC,
    SORT_DATE_DESC,
    SORT_RISK_DESC,
)


@dataclass
class EvidenceItem:
    """Elemento de evidencia listado en el centro de evidencias."""

    path: Path
    kind: str
    date: str
    time: str
    confidence: float
    risk_level: str
    event_type: str
    filename: str

    @property
    def sort_datetime(self) -> str:
        return f"{self.date} {self.time}"


class EvidenceCatalog:
    """Escanea carpetas de evidencia y combina metadatos de incidentes."""

    SCREENSHOT_EXTS = {".png", ".jpg", ".jpeg"}
    CLIP_EXTS = {".mp4", ".avi", ".mov"}

    def __init__(self, incident_history: IncidentHistory | None = None):
        self.incidents = incident_history or IncidentHistory()
        EVIDENCE_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        EVIDENCE_CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    def _parse_filename_datetime(self, path: Path) -> tuple[str, str]:
        stem = path.stem
        for fmt in ("%Y-%m-%d_%H-%M-%S", "%Y%m%d_%H%M%S"):
            try:
                dt = datetime.strptime(stem, fmt)
                return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")
            except ValueError:
                continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return mtime.strftime("%Y-%m-%d"), mtime.strftime("%H:%M:%S")

    def _find_incident_for_file(self, path: Path) -> IncidentRecord | None:
        path_str = str(path).replace("\\", "/")
        name = path.name
        for record in self.incidents.records:
            if not record.file_path:
                continue
            fp = record.file_path.replace("\\", "/")
            if fp.endswith(name) or path_str.endswith(fp.split("/")[-1]):
                return record
        return None

    def _build_item(self, path: Path, kind: str) -> EvidenceItem:
        date, time = self._parse_filename_datetime(path)
        incident = self._find_incident_for_file(path)
        if incident:
            return EvidenceItem(
                path=path,
                kind=kind,
                date=incident.datetime.split(" ")[0] if " " in incident.datetime else date,
                time=incident.datetime.split(" ")[1] if " " in incident.datetime else time,
                confidence=incident.confidence,
                risk_level=incident.risk_level,
                event_type=incident.event_type,
                filename=path.name,
            )
        return EvidenceItem(
            path=path,
            kind=kind,
            date=date,
            time=time,
            confidence=0.0,
            risk_level="—",
            event_type="Incidente registrado",
            filename=path.name,
        )

    def _scan_screenshots(self) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        dirs = [EVIDENCE_SCREENSHOTS_DIR, EVIDENCE_DIR]
        seen: set[str] = set()
        for folder in dirs:
            if not folder.exists():
                continue
            for path in sorted(folder.iterdir(), reverse=True):
                if path.suffix.lower() not in self.SCREENSHOT_EXTS:
                    continue
                if path.parent == EVIDENCE_DIR and path.parent.name == "clips":
                    continue
                key = str(path.resolve())
                if key in seen:
                    continue
                seen.add(key)
                items.append(self._build_item(path, "screenshot"))
        return sorted(items, key=lambda i: i.sort_datetime, reverse=True)

    def _scan_clips(self) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        if not EVIDENCE_CLIPS_DIR.exists():
            return items
        for path in sorted(EVIDENCE_CLIPS_DIR.iterdir(), reverse=True):
            if path.suffix.lower() not in self.CLIP_EXTS:
                continue
            items.append(self._build_item(path, "clip"))
        return sorted(items, key=lambda i: i.sort_datetime, reverse=True)

    def get_screenshots(self) -> list[EvidenceItem]:
        self.incidents.load()
        return self._scan_screenshots()

    def get_clips(self) -> list[EvidenceItem]:
        self.incidents.load()
        return self._scan_clips()

    def get_incidents(self, sort_key: str = SORT_DATE_DESC) -> list[IncidentRecord]:
        self.incidents.load()
        return self.incidents.get_sorted(sort_key)

    @staticmethod
    def sort_items(items: list[EvidenceItem], sort_key: str) -> list[EvidenceItem]:
        if sort_key == SORT_DATE_ASC:
            return sorted(items, key=lambda i: i.sort_datetime)
        if sort_key == SORT_RISK_DESC:
            from utils.constants import RISK_SORT_ORDER
            return sorted(
                items,
                key=lambda i: (RISK_SORT_ORDER.get(i.risk_level, 0), i.confidence),
                reverse=True,
            )
        if sort_key == SORT_CONFIDENCE_DESC:
            return sorted(items, key=lambda i: i.confidence, reverse=True)
        return sorted(items, key=lambda i: i.sort_datetime, reverse=True)
