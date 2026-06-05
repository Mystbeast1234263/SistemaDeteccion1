"""Predicción en tiempo real con el modelo entrenado."""

import numpy as np

from ml.model_trainer import ModelTrainer
from utils.constants import LABEL_NORMAL, LABEL_SOSPECHOSO, RISK_ENCODING
from video.optical_flow import MotionFeatures


class PredictionResult:
    def __init__(self, label: str, confidence: float, raw_label: str):
        self.label = label
        self.confidence = confidence
        self.raw_label = raw_label

    @property
    def is_suspicious(self) -> bool:
        return self.raw_label == LABEL_SOSPECHOSO


class BehaviorPredictor:
    """Predice comportamiento NORMAL o SOSPECHOSO desde MotionFeatures."""

    def __init__(self, trainer: ModelTrainer):
        self._trainer = trainer

    @property
    def is_ready(self) -> bool:
        return self._trainer.is_loaded

    def predict(self, features: MotionFeatures) -> PredictionResult | None:
        if not self.is_ready:
            return None

        risk_enc = RISK_ENCODING.get(features.nivel_riesgo.upper(), 0)
        X = np.array([[
            features.intensidad_movimiento,
            features.magnitud_promedio,
            features.direccion_promedio,
            features.cantidad_movimiento,
            risk_enc,
        ]])

        model = self._trainer.model
        proba = model.predict_proba(X)[0]
        pred_idx = int(np.argmax(proba))
        raw = self._trainer.label_encoder.inverse_transform([pred_idx])[0]
        confidence = float(proba[pred_idx] * 100)

        display = "SOSPECHOSO" if raw == LABEL_SOSPECHOSO else "NORMAL"
        return PredictionResult(label=display, confidence=round(confidence, 1), raw_label=raw)
