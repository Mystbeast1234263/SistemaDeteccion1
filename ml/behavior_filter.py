"""Filtro anti-falsos-positivos para movimiento y predicciones ML."""

from utils.constants import (
    ALERT_ELEVATED_MIN,
    ALERT_INTENSE_MIN,
    ALERT_MOTION_MIN,
    BRIEF_MOTION_MAX_INTENSITY,
    MIN_ML_SUSPICIOUS_CONF,
    MOTION_ALERT_SUSTAINED_CYCLES,
    MOTION_DETECT_MIN_INTENSITY,
    RISK_HIGH_MIN,
    SUSPICIOUS_CONFIRM_CYCLES,
)


class BehaviorFilter:
    """
    Evita alertas por movimientos breves y normales (cabeza, acomodarse, etc.).
    Requiere persistencia minima antes de alertar o marcar sospechoso.
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._motion_cycles = 0
        self._suspicious_cycles = 0
        self._brief_spike_cycles = 0

    def motion_detected(self, intensity: int, active_pixels: bool = True) -> bool:
        """Indica si hay movimiento real, no ruido leve."""
        return intensity >= MOTION_DETECT_MIN_INTENSITY and active_pixels

    def should_alert_motion(self, intensity: int) -> bool:
        """Alerta solo con movimiento sostenido por encima del umbral."""
        if intensity < ALERT_MOTION_MIN:
            self._motion_cycles = 0
            self._brief_spike_cycles = 0
            return False

        if intensity < BRIEF_MOTION_MAX_INTENSITY:
            self._brief_spike_cycles += 1
            if self._brief_spike_cycles < MOTION_ALERT_SUSTAINED_CYCLES:
                return False
        else:
            self._brief_spike_cycles = 0

        self._motion_cycles += 1
        return self._motion_cycles >= MOTION_ALERT_SUSTAINED_CYCLES

    def should_report_suspicious(self, is_suspicious: bool, confidence: float, intensity: int) -> bool:
        """Confirma sospecha ML solo con confianza y persistencia suficientes."""
        if not is_suspicious or confidence < MIN_ML_SUSPICIOUS_CONF:
            self._suspicious_cycles = 0
            return False

        if intensity >= RISK_HIGH_MIN and confidence >= 70:
            return True

        self._suspicious_cycles += 1
        return self._suspicious_cycles >= SUSPICIOUS_CONFIRM_CYCLES

    def alert_level(self, intensity: int) -> str | None:
        """Nivel de alerta de movimiento tras filtro."""
        if intensity >= ALERT_INTENSE_MIN:
            return "intense"
        if intensity >= ALERT_ELEVATED_MIN:
            return "elevated"
        if intensity >= ALERT_MOTION_MIN:
            return "motion"
        return None
