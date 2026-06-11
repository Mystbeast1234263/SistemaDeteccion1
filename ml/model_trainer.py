"""Entrenamiento, guardado y carga de RandomForestClassifier."""

import copy
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
        self._training_rows: list[dict] = []

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    @property
    def model_path(self) -> Path | None:
        return self._model_path

    @property
    def metrics(self) -> dict:
        return self._metrics

    @property
    def training_sample_count(self) -> int:
        return len(self._training_rows)

    @staticmethod
    def _normalize_row(row: dict) -> dict:
        risk = (row.get("nivel_riesgo") or "BAJO").upper()
        etiqueta = (row.get("etiqueta") or "").strip().lower()
        return {
            "timestamp": row.get("timestamp", ""),
            "intensidad_movimiento": float(row["intensidad_movimiento"]),
            "magnitud_promedio": float(row["magnitud_promedio"]),
            "direccion_promedio": float(row["direccion_promedio"]),
            "cantidad_movimiento": float(row["cantidad_movimiento"]),
            "nivel_riesgo": risk,
            "etiqueta": etiqueta,
        }

    @staticmethod
    def _row_signature(row: dict) -> tuple:
        normalized = ModelTrainer._normalize_row(row)
        return (
            round(normalized["intensidad_movimiento"], 2),
            round(normalized["magnitud_promedio"], 4),
            round(normalized["direccion_promedio"], 2),
            round(normalized["cantidad_movimiento"], 2),
            normalized["nivel_riesgo"],
            normalized["etiqueta"],
        )

    @classmethod
    def _merge_training_rows(cls, base: list[dict], extra: list[dict]) -> tuple[list[dict], int]:
        seen = {cls._row_signature(r) for r in base}
        merged = [cls._normalize_row(r) for r in base]
        added = 0
        for row in extra:
            sig = cls._row_signature(row)
            if sig in seen:
                continue
            merged.append(cls._normalize_row(row))
            seen.add(sig)
            added += 1
        return merged, added

    def count_pending_samples(self, dataset: DatasetManager | None = None) -> int:
        """Muestras en dataset.csv que aun no estan en el conocimiento del modelo cargado."""
        dm = dataset or DatasetManager()
        csv_rows = dm.load_labeled_rows()
        if not self._training_rows:
            return len(csv_rows)
        _, added = self._merge_training_rows(self._training_rows, csv_rows)
        return added

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

    def _fit_model(self, rows: list[dict]) -> tuple[bool, str, int, int]:
        if len(rows) < 4:
            return False, "Se necesitan al menos 4 muestras etiquetadas.", 0, 0

        label_counts = Counter(r["etiqueta"] for r in rows)
        if len(label_counts) < 2:
            return False, "El dataset debe incluir ejemplos 'normal' y 'sospechoso'.", 0, 0

        min_class = min(label_counts.values())
        if min_class < 2:
            return (
                False,
                f"Cada clase necesita al menos 2 muestras. "
                f"Actual: normal={label_counts.get(LABEL_NORMAL, 0)}, "
                f"sospechoso={label_counts.get(LABEL_SOSPECHOSO, 0)}.",
                0,
                0,
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
        self._training_rows = copy.deepcopy(rows)
        self._metrics = {
            "accuracy": round(accuracy * 100, 2),
            "samples": len(rows),
            "features": ["intensidad", "magnitud", "direccion", "cantidad", "riesgo_enc"],
        }
        return True, "", len(rows), round(accuracy * 100, 2)

    def train(
        self,
        dataset: DatasetManager | None = None,
        *,
        continue_from_loaded: bool = False,
    ) -> tuple[bool, str]:
        try:
            dm = dataset or DatasetManager()
            csv_rows = dm.load_labeled_rows()
            prev_count = len(self._training_rows)
            new_count = 0

            if continue_from_loaded and self.is_loaded:
                if self._training_rows:
                    rows, new_count = self._merge_training_rows(self._training_rows, csv_rows)
                    if new_count == 0:
                        return (
                            False,
                            "No hay muestras nuevas en dataset.csv. "
                            "Etiquete frames (Normal/Sospechoso) o deje correr el monitoreo "
                            "para registrar datos automaticos, luego pulse Ampliar.",
                        )
                else:
                    rows = [self._normalize_row(r) for r in csv_rows]
                    new_count = len(rows)
                    if not rows:
                        return False, "No hay muestras en dataset.csv para ampliar el modelo."
            else:
                rows = [self._normalize_row(r) for r in csv_rows]
                new_count = len(rows)
                if not rows:
                    return False, "Se necesitan al menos 4 muestras etiquetadas en dataset.csv."

            ok, err, total, accuracy = self._fit_model(rows)
            if not ok:
                return False, err

            self._metrics["trained_from"] = (
                "modelo + dataset.csv" if continue_from_loaded and self.is_loaded else "dataset.csv"
            )
            if continue_from_loaded and self.is_loaded and prev_count:
                self._metrics["previous_samples"] = prev_count
                self._metrics["new_samples"] = new_count
                msg = (
                    f"Conocimiento ampliado: +{new_count} muestras nuevas "
                    f"(total {total}). Precision: {accuracy}%."
                )
            elif continue_from_loaded and self.is_loaded:
                msg = (
                    f"Modelo actualizado con {total} muestras de dataset.csv. "
                    f"Precision: {accuracy}%. Guarde el modelo para conservar el conocimiento."
                )
            else:
                msg = (
                    f"Modelo entrenado con {total} muestras desde dataset.csv. "
                    f"Precision: {accuracy}%. Use Guardar para persistirlo."
                )
            return True, msg
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
                "training_rows": self._training_rows,
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

        if path.stat().st_size > 50_000_000:
            return False, "El archivo es demasiado grande. Puede estar corrupto."

        try:
            with open(path, "rb") as f:
                payload = pickle.load(f)

            if not isinstance(payload, dict) or "model" not in payload:
                return False, "Archivo invalido: no es un modelo SIDACS (.pkl)."

            model = payload["model"]
            if not hasattr(model, "predict_proba"):
                return False, "El archivo no contiene un clasificador valido."

            self.model = model
            le = payload.get("label_encoder")
            if le is not None and hasattr(le, "classes_"):
                self.label_encoder = le
            else:
                self.label_encoder = LabelEncoder()
                self.label_encoder.fit([LABEL_NORMAL, LABEL_SOSPECHOSO])

            self._metrics = payload.get("metrics", {})
            self._training_rows = [
                self._normalize_row(r) for r in payload.get("training_rows", [])
            ]
            self._model_path = path.resolve()
            samples = len(self._training_rows)
            detail = f" ({samples} muestras de conocimiento)" if samples else ""
            return True, f"Modelo cargado: {path.name}{detail}"
        except MemoryError:
            return False, (
                "El archivo del modelo esta corrupto. Entrene de nuevo y guarde un modelo nuevo."
            )
        except Exception as exc:
            return False, f"Error al cargar: {exc}"

    def load_latest(self) -> tuple[bool, str]:
        """Carga el .pkl mas reciente en models/."""
        candidates = sorted(
            self.models_dir.glob("*.pkl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for path in candidates:
            ok, msg = self.load(path)
            if ok:
                return True, msg
        return False, "No hay modelos validos en la carpeta models/."

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
