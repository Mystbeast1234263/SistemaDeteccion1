"""Entrenamiento, guardado y carga de RandomForestClassifier."""

import pickle
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from ml.dataset_manager import DatasetManager
from utils.constants import LABEL_NORMAL, LABEL_SOSPECHOSO, MODELS_DIR, RISK_ENCODING


class ModelTrainer:
    """Entrena y persiste modelos scikit-learn en models/*.pkl."""

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.model: RandomForestClassifier | None = None
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit([LABEL_NORMAL, LABEL_SOSPECHOSO])
        self._model_path: Path | None = None
        self._metrics: dict = {}

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    @property
    def model_path(self) -> Path | None:
        return self._model_path

    @property
    def metrics(self) -> dict:
        return self._metrics

    @staticmethod
    def _features_from_row(row: dict) -> list[float]:
        risk = row.get("nivel_riesgo", "BAJO").upper()
        return [
            float(row["intensidad_movimiento"]),
            float(row["magnitud_promedio"]),
            float(row["direccion_promedio"]),
            float(row["cantidad_movimiento"]),
            float(RISK_ENCODING.get(risk, 0)),
        ]

    def train(self, dataset: DatasetManager | None = None) -> tuple[bool, str]:
        try:
            dm = dataset or DatasetManager()
            rows = dm.load_labeled_rows()

            if len(rows) < 4:
                return False, "Se necesitan al menos 4 muestras etiquetadas en dataset.csv."

            label_counts = Counter(r["etiqueta"] for r in rows)
            if len(label_counts) < 2:
                return False, "El dataset debe incluir ejemplos 'normal' y 'sospechoso'."

            min_class = min(label_counts.values())
            if min_class < 2:
                return (
                    False,
                    f"Cada clase necesita al menos 2 muestras. "
                    f"Actual: normal={label_counts.get(LABEL_NORMAL, 0)}, "
                    f"sospechoso={label_counts.get(LABEL_SOSPECHOSO, 0)}.",
                )

            labels = [r["etiqueta"] for r in rows]
            X = np.array([self._features_from_row(r) for r in rows])
            y = self.label_encoder.transform(labels)

            can_stratify = len(rows) >= 10 and min_class >= 2
            if can_stratify:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, stratify=y
                )
            else:
                X_train, y_train = X, y
                X_test, y_test = X, y

            self.model = RandomForestClassifier(
                n_estimators=50,
                max_depth=8,
                random_state=42,
                n_jobs=-1,
            )
            self.model.fit(X_train, y_train)
            accuracy = float(self.model.score(X_test, y_test))
            self._metrics = {
                "accuracy": round(accuracy * 100, 2),
                "samples": len(rows),
                "features": ["intensidad", "magnitud", "direccion", "cantidad", "riesgo_enc"],
            }
            return True, (
                f"Modelo entrenado. Precision: {self._metrics['accuracy']}% "
                f"({len(rows)} muestras)"
            )
        except Exception as exc:
            return False, f"Error al entrenar: {exc}"

    def save(self, filename: str = "modelo_v1.pkl") -> tuple[bool, str]:
        if self.model is None:
            return False, "No hay modelo entrenado. Pulse 'Entrenar Modelo' primero."

        try:
            path = self.models_dir / filename
            payload = {
                "model": self.model,
                "label_encoder": self.label_encoder,
                "metrics": self._metrics,
            }
            with open(path, "wb") as f:
                pickle.dump(payload, f)
            self._model_path = path
            return True, f"Modelo guardado: {path.name}"
        except Exception as exc:
            return False, f"Error al guardar: {exc}"

    def load(self, path: str | Path) -> tuple[bool, str]:
        path = Path(path)
        if not path.exists():
            return False, f"No se encontró el modelo: {path}"

        try:
            with open(path, "rb") as f:
                payload = pickle.load(f)

            self.model = payload["model"]
            self.label_encoder = payload.get("label_encoder", self.label_encoder)
            self._metrics = payload.get("metrics", {})
            self._model_path = path
            return True, f"Modelo cargado: {path.name}"
        except Exception as exc:
            return False, f"Error al cargar: {exc}"

    def export_model(self, dest_path: str) -> tuple[bool, str]:
        try:
            if self._model_path is None or not self._model_path.exists():
                if self.model is None:
                    return False, "No hay modelo para exportar."
                ok, msg = self.save("modelo_export_temp.pkl")
                if not ok:
                    return False, msg

            dest = Path(dest_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self._model_path, dest)
            return True, f"Modelo exportado a: {dest.name}"
        except Exception as exc:
            return False, f"Error al exportar: {exc}"

    def import_model(self, src_path: str, filename: str | None = None) -> tuple[bool, str]:
        src = Path(src_path)
        if not src.exists():
            return False, "Archivo de modelo no encontrado."

        try:
            dest_name = filename or src.name
            dest = self.models_dir / dest_name
            shutil.copy2(src, dest)
            return self.load(dest)
        except Exception as exc:
            return False, f"Error al importar: {exc}"
