"""Gestión del dataset para entrenamiento ML."""

import csv
from datetime import datetime
from pathlib import Path

from utils.constants import DATASET_COLUMNS, DATASET_PATH, LABEL_NORMAL, LABEL_SOSPECHOSO
from video.optical_flow import MotionFeatures


class DatasetManager:
    """Genera y gestiona dataset/dataset.csv con características MotionFeatures."""

    def __init__(self, dataset_path: Path = DATASET_PATH):
        self.dataset_path = Path(dataset_path)
        self.dataset_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_header()

    def _ensure_header(self) -> None:
        if not self.dataset_path.exists():
            with open(self.dataset_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=DATASET_COLUMNS)
                writer.writeheader()

    def _heuristic_label(self, features: MotionFeatures) -> str:
        if features.nivel_riesgo == "ALTO" or features.intensidad_movimiento >= 56:
            return LABEL_SOSPECHOSO
        return LABEL_NORMAL

    def _row_from_features(self, features: MotionFeatures, etiqueta: str) -> dict:
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "intensidad_movimiento": features.intensidad_movimiento,
            "magnitud_promedio": features.magnitud_promedio,
            "direccion_promedio": features.direccion_promedio,
            "cantidad_movimiento": features.cantidad_movimiento,
            "nivel_riesgo": features.nivel_riesgo,
            "etiqueta": etiqueta,
        }

    def append_auto(self, features: MotionFeatures) -> None:
        """Registro automático con etiqueta heurística."""
        self._append_row(self._row_from_features(features, self._heuristic_label(features)))

    def append_manual(self, features: MotionFeatures, etiqueta: str) -> None:
        """Registro manual con etiqueta del usuario."""
        label = LABEL_SOSPECHOSO if etiqueta.lower() == LABEL_SOSPECHOSO else LABEL_NORMAL
        self._append_row(self._row_from_features(features, label))

    def _append_row(self, row: dict) -> None:
        with open(self.dataset_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=DATASET_COLUMNS)
            writer.writerow(row)

    def load_labeled_rows(self) -> list[dict]:
        """Carga filas con etiqueta válida para entrenamiento."""
        if not self.dataset_path.exists():
            return []

        rows = []
        with open(self.dataset_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                etiqueta = (row.get("etiqueta") or "").strip().lower()
                if etiqueta in (LABEL_NORMAL, LABEL_SOSPECHOSO):
                    rows.append(row)
        return rows

    def count_samples(self) -> dict:
        rows = self.load_labeled_rows()
        normal = sum(1 for r in rows if r["etiqueta"] == LABEL_NORMAL)
        sospechoso = sum(1 for r in rows if r["etiqueta"] == LABEL_SOSPECHOSO)
        return {"total": len(rows), "normal": normal, "sospechoso": sospechoso}
