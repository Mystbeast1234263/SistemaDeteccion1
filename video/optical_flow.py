"""Detección de movimiento mediante Flujo Óptico Farneback (OpenCV)."""

from dataclasses import dataclass

import cv2
import numpy as np

from utils.constants import (
    FLOW_GRID_STEP,
    FLOW_MAGNITUDE_SCALE,
    FLOW_MIN_MAGNITUDE,
    FLOW_PROCESS_HEIGHT,
    FLOW_PROCESS_WIDTH,
    FLOW_SMOOTH_ALPHA,
    RISK_HIGH_MIN,
    RISK_MEDIUM_MIN,
)


@dataclass
class MotionFeatures:
    """Características de movimiento expuestas para UI y futuros sprints de ML."""

    intensidad_movimiento: int
    magnitud_promedio: float
    direccion_promedio: float
    cantidad_movimiento: float
    nivel_riesgo: str
    motion_detected: bool
    annotated_frame: np.ndarray


class OpticalFlowAnalyzer:
    """
    Analiza movimiento entre frames consecutivos con cv2.calcOpticalFlowFarneback.
    Calcula magnitud, dirección, intensidad y genera visualización de vectores.
    """

    def __init__(self):
        self._prev_gray = None
        self._smoothed_intensity = 0.0
        self._frame_count = 0

    def reset(self) -> None:
        """Reinicia el estado (nueva fuente o fin de análisis)."""
        self._prev_gray = None
        self._smoothed_intensity = 0.0
        self._frame_count = 0

    @property
    def last_features(self) -> MotionFeatures | None:
        return getattr(self, "_last_features", None)

    def process(self, frame: np.ndarray, draw_overlay: bool = True) -> MotionFeatures:
        """Procesa un frame BGR y devuelve métricas + frame anotado."""
        self._frame_count += 1
        h, w = frame.shape[:2]

        scale = min(FLOW_PROCESS_WIDTH / w, FLOW_PROCESS_HEIGHT / h, 1.0)
        proc_w = max(1, int(w * scale))
        proc_h = max(1, int(h * scale))
        small = cv2.resize(frame, (proc_w, proc_h))
        gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (5, 5), 0)

        output = frame.copy() if draw_overlay else frame

        if self._prev_gray is None or self._prev_gray.shape != gray.shape:
            self._prev_gray = gray
            features = self._build_features(
                intensity=0,
                avg_magnitude=0.0,
                avg_direction=0.0,
                motion_amount=0.0,
                risk_level="BAJO",
                motion_detected=False,
                frame=output,
            )
            self._last_features = features
            return features

        flow = cv2.calcOpticalFlowFarneback(
            self._prev_gray,
            gray,
            None,
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
        )
        self._prev_gray = gray

        fx = flow[..., 0]
        fy = flow[..., 1]
        magnitude, angle = cv2.cartToPolar(fx, fy)

        active_mask = magnitude > FLOW_MIN_MAGNITUDE
        active_count = int(np.count_nonzero(active_mask))
        total_pixels = magnitude.size

        if active_count > 0:
            avg_magnitude = float(np.mean(magnitude[active_mask]))
            avg_direction = self._circular_mean_degrees(angle[active_mask])
            motion_amount = float(active_count / total_pixels * 100.0)
        else:
            avg_magnitude = 0.0
            avg_direction = 0.0
            motion_amount = 0.0

        raw_intensity = min(avg_magnitude * FLOW_MAGNITUDE_SCALE, 100.0)
        if self._frame_count <= 15:
            raw_intensity *= self._frame_count / 15.0

        self._smoothed_intensity = (
            FLOW_SMOOTH_ALPHA * raw_intensity
            + (1.0 - FLOW_SMOOTH_ALPHA) * self._smoothed_intensity
        )
        intensity = int(round(self._smoothed_intensity))
        risk_level = self._risk_from_intensity(intensity)
        motion_detected = intensity >= 8 and active_count > 0

        if draw_overlay:
            self._draw_flow_vectors(output, flow, magnitude, proc_w, proc_h)
            self._draw_hud(output, intensity, risk_level, avg_magnitude, avg_direction)

        features = self._build_features(
            intensity=intensity,
            avg_magnitude=avg_magnitude,
            avg_direction=avg_direction,
            motion_amount=motion_amount,
            risk_level=risk_level,
            motion_detected=motion_detected,
            frame=output,
        )
        self._last_features = features
        return features

    def _build_features(
        self,
        intensity: int,
        avg_magnitude: float,
        avg_direction: float,
        motion_amount: float,
        risk_level: str,
        motion_detected: bool,
        frame: np.ndarray,
    ) -> MotionFeatures:
        return MotionFeatures(
            intensidad_movimiento=intensity,
            magnitud_promedio=round(avg_magnitude, 4),
            direccion_promedio=round(avg_direction, 2),
            cantidad_movimiento=round(motion_amount, 2),
            nivel_riesgo=risk_level,
            motion_detected=motion_detected,
            annotated_frame=frame,
        )

    @staticmethod
    def _circular_mean_degrees(angles_rad: np.ndarray) -> float:
        sin_sum = float(np.mean(np.sin(angles_rad)))
        cos_sum = float(np.mean(np.cos(angles_rad)))
        deg = np.degrees(np.arctan2(sin_sum, cos_sum))
        return deg + 360.0 if deg < 0 else deg

    @staticmethod
    def _risk_from_intensity(intensity: int) -> str:
        if intensity >= RISK_HIGH_MIN:
            return "ALTO"
        if intensity >= RISK_MEDIUM_MIN:
            return "MEDIO"
        return "BAJO"

    def _draw_flow_vectors(
        self,
        frame: np.ndarray,
        flow: np.ndarray,
        magnitude: np.ndarray,
        proc_w: int,
        proc_h: int,
    ) -> None:
        h, w = frame.shape[:2]
        scale_x = w / proc_w
        scale_y = h / proc_h
        step = FLOW_GRID_STEP

        for y in range(0, proc_h, step):
            for x in range(0, proc_w, step):
                mag = magnitude[y, x]
                if mag < FLOW_MIN_MAGNITUDE:
                    continue

                x1 = int(x * scale_x)
                y1 = int(y * scale_y)
                x2 = int((x + flow[y, x, 0]) * scale_x)
                y2 = int((y + flow[y, x, 1]) * scale_y)

                color = self._vector_color(mag)
                cv2.arrowedLine(frame, (x1, y1), (x2, y2), color, 1, tipLength=0.35)
                cv2.circle(frame, (x1, y1), 2, color, -1, lineType=cv2.LINE_AA)

    @staticmethod
    def _vector_color(magnitude: float) -> tuple:
        if magnitude > 4.0:
            return (51, 51, 255)
        if magnitude > 2.0:
            return (0, 170, 255)
        return (255, 212, 0)

    @staticmethod
    def _draw_hud(
        frame: np.ndarray,
        intensity: int,
        risk_level: str,
        avg_magnitude: float,
        avg_direction: float,
    ) -> None:
        cv2.rectangle(frame, (8, 8), (290, 58), (10, 14, 23), -1)
        cv2.putText(
            frame,
            f"FLUJO OPTICO | INT: {intensity}% | RIESGO: {risk_level}",
            (14, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 212, 255),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"MAG: {avg_magnitude:.2f}  DIR: {avg_direction:.0f} deg",
            (14, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 212, 0),
            1,
            cv2.LINE_AA,
        )
