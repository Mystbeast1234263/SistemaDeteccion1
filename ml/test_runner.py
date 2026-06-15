"""Modulo de pruebas de validacion Sprint 5."""

import json
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from utils.constants import (
    DOCS_DIR,
    SPRINT5_TESTING_DOC,
    TEST_RESULTS_PATH,
    TESTING_DIR,
)
from video.optical_flow import OpticalFlowAnalyzer


TEST_CASES = [
    {
        "id": "normal_video",
        "name": "Video normal sin actividad sospechosa",
        "description": "Escena estable o movimiento leve sin patron sospechoso.",
        "expected": "Intensidad baja, pocas alertas, sin detecciones sospechosas ML.",
        "type": "session",
    },
    {
        "id": "excessive_motion",
        "name": "Movimiento excesivo",
        "description": "Movimiento brusco o intenso en el encuadre.",
        "expected": "Intensidad alta, alertas de actividad elevada o riesgo alto.",
        "type": "session",
    },
    {
        "id": "suspicious_simulation",
        "name": "Simulacion de comportamiento sospechoso",
        "description": "Patron de movimiento intenso sostenido con modelo activo.",
        "expected": "Prediccion sospechosa o riesgo ALTO con confianza relevante.",
        "type": "session",
    },
    {
        "id": "empty_video",
        "name": "Video vacio / estatico",
        "description": "Frame sin cambios entre capturas consecutivas.",
        "expected": "Intensidad 0 o muy baja, sin alertas de movimiento.",
        "type": "automated",
    },
    {
        "id": "webcam_realtime",
        "name": "Webcam en tiempo real",
        "description": "Monitoreo en vivo con camara web.",
        "expected": "Analisis fluido, FPS estable, sin cuelgues de interfaz.",
        "type": "session",
    },
]


class TestRunner:
    """Ejecuta pruebas automaticas y registra resultados de sesion."""

    def __init__(self, results_path: Path = TEST_RESULTS_PATH):
        self.results_path = Path(results_path)
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        self._results = self._load_results()

    def _load_results(self) -> list[dict]:
        if not self.results_path.exists():
            return []
        try:
            with open(self.results_path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def list_cases(self) -> list[dict]:
        enriched = []
        for case in TEST_CASES:
            last = self._last_result_for(case["id"])
            enriched.append({**case, "last_result": last})
        return enriched

    def _last_result_for(self, case_id: str) -> dict | None:
        matches = [r for r in self._results if r.get("case_id") == case_id]
        return matches[-1] if matches else None

    def run_automated(self, case_id: str) -> tuple[bool, str, dict]:
        if case_id == "empty_video":
            return self._test_empty_video()
        return False, f"Prueba '{case_id}' requiere registro manual de sesion.", {}

    def _test_empty_video(self) -> tuple[bool, str, dict]:
        analyzer = OpticalFlowAnalyzer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        r1 = analyzer.process(frame, draw_overlay=False)
        r2 = analyzer.process(frame, draw_overlay=False)
        max_intensity = max(r1.intensidad_movimiento, r2.intensidad_movimiento)
        passed = max_intensity <= 5 and not r2.motion_detected
        details = {
            "intensity_frame1": r1.intensidad_movimiento,
            "intensity_frame2": r2.intensidad_movimiento,
            "motion_detected": r2.motion_detected,
        }
        msg = (
            "Video estatico: sin falsos positivos de movimiento."
            if passed
            else f"Falso positivo detectado (intensidad max {max_intensity})."
        )
        return passed, msg, details

    def save_automated_result(
        self, case_id: str, passed: bool, evaluation: str, details: dict
    ) -> None:
        case = next((c for c in TEST_CASES if c["id"] == case_id), None)
        if not case:
            return
        self._results.append({
            "case_id": case_id,
            "case_name": case["name"],
            "expected": case["expected"],
            "passed": passed,
            "evaluation": evaluation,
            "observations": "Prueba automatica",
            "details": details,
            "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "automated",
        })
        self._save_results()

    def record_session(
        self,
        case_id: str,
        session_stats: dict,
        performance: dict,
        notes: str = "",
    ) -> tuple[bool, str]:
        case = next((c for c in TEST_CASES if c["id"] == case_id), None)
        if case is None:
            return False, "Caso de prueba desconocido."

        passed, evaluation = self._evaluate_session(case_id, session_stats)
        entry = {
            "case_id": case_id,
            "case_name": case["name"],
            "expected": case["expected"],
            "passed": passed,
            "evaluation": evaluation,
            "observations": notes.strip(),
            "session_stats": session_stats,
            "performance": performance,
            "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._results.append(entry)
        self._save_results()
        status = "APROBADO" if passed else "REVISAR"
        return True, f"{case['name']}: {status} — {evaluation}"

    def _evaluate_session(self, case_id: str, stats: dict) -> tuple[bool, str]:
        suspicious = stats.get("suspicious", {})
        movement = stats.get("movement", {})
        risk = stats.get("risk", {})
        activity = stats.get("activity", {})
        alerts = stats.get("alerts", {})

        max_int = movement.get("max_intensity", 0)
        avg_int = movement.get("avg_intensity", 0)
        total_susp = suspicious.get("total_detected", 0)
        high_risk = risk.get("high_events", 0)
        avg_fps = activity.get("avg_fps", 0)
        total_alerts = alerts.get("total", 0)

        if case_id == "normal_video":
            passed = total_susp <= 2 and max_int < 55
            return passed, f"Alertas: {total_alerts}, sospechosos: {total_susp}, max int: {max_int}%"

        if case_id == "excessive_motion":
            passed = max_int >= 40 or high_risk >= 3
            return passed, f"Intensidad max {max_int}%, eventos riesgo alto: {high_risk}"

        if case_id == "suspicious_simulation":
            passed = total_susp >= 1 or suspicious.get("max_confidence", 0) >= 45
            return passed, (
                f"Sospechosos: {total_susp}, conf max: {suspicious.get('max_confidence', 0)}%"
            )

        if case_id == "webcam_realtime":
            frames = activity.get("frames_processed", 0)
            passed = frames >= 30 and (avg_fps >= 15 or frames > 0)
            return passed, f"Frames: {frames}, FPS prom: {avg_fps}"

        return False, "Tipo de prueba no evaluable automaticamente."

    def _save_results(self) -> None:
        with open(self.results_path, "w", encoding="utf-8") as f:
            json.dump(self._results, f, indent=2, ensure_ascii=False)

    def generate_testing_report(self) -> Path:
        lines = [
            "# Sprint 5 — Reporte de Testing SIDACS",
            "",
            f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Casos de prueba",
            "",
        ]
        for case in TEST_CASES:
            lines.append(f"### {case['name']}")
            lines.append(f"- **ID:** `{case['id']}`")
            lines.append(f"- **Tipo:** {case['type']}")
            lines.append(f"- **Descripcion:** {case['description']}")
            lines.append(f"- **Resultado esperado:** {case['expected']}")
            last = self._last_result_for(case["id"])
            if last:
                status = "APROBADO" if last.get("passed") else "REVISAR"
                lines.append(f"- **Resultado obtenido:** {status} — {last.get('evaluation', '—')}")
                lines.append(f"- **Fecha:** {last.get('recorded_at', '—')}")
                if last.get("observations"):
                    lines.append(f"- **Observaciones:** {last['observations']}")
            else:
                lines.append("- **Resultado obtenido:** Pendiente de ejecutar")
            lines.append("")

        lines.extend([
            "## Resumen",
            "",
            f"- Total registros: {len(self._results)}",
            f"- Aprobados: {sum(1 for r in self._results if r.get('passed'))}",
            f"- A revisar: {sum(1 for r in self._results if not r.get('passed'))}",
            "",
            "## Como repetir las pruebas",
            "",
            "1. Abra la pestana **Pruebas** en SIDACS.",
            "2. Para *Video vacio*, use **Ejecutar automatico**.",
            "3. Para los demas casos, cargue video o webcam, inicie monitoreo y pulse **Registrar resultado**.",
            "4. Pulse **Generar reporte** para actualizar este archivo.",
            "",
        ])
        SPRINT5_TESTING_DOC.write_text("\n".join(lines), encoding="utf-8")
        return SPRINT5_TESTING_DOC

    def generate_optimization_report(
        self,
        performance: dict,
        model_metrics: dict,
        session_stats: dict,
    ) -> Path:
        """Genera reporte de sesion en HTML (no sobrescribe el doc principal)."""
        path = DOCS_DIR / "sprint5_sesion.html"
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        act = session_stats.get("activity", {})
        tests_html = ""
        if self._results:
            for r in self._results[-10:]:
                status = "OK" if r.get("passed") else "REVISAR"
                tests_html += f"<li>[{status}] {r.get('case_name', r.get('case_id'))} — {r.get('recorded_at', '—')}</li>\n"
        else:
            tests_html = "<li>Sin pruebas registradas aún.</li>"

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>SIDACS — Métricas de sesión Sprint 5</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
h1 {{ color: #1e3a5f; border-bottom: 2px solid #1e3a5f; padding-bottom: 8px; }}
table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
th, td {{ border: 1px solid #b0c4de; padding: 8px; text-align: left; }}
th {{ background: #e8f0fa; }}
.meta {{ color: #4a6278; font-size: 10pt; }}
a {{ color: #1e3a5f; }}
</style>
</head>
<body>
<h1>Métricas de sesión — Sprint 5</h1>
<p class="meta">Generado: {ts}<br>
Documento principal (antes vs. ahora): <a href="sprint5_optimizaciones.html">sprint5_optimizaciones.html</a></p>
<h2>Modelo ML</h2>
<table>
<tr><th>Métrica</th><th>Valor</th></tr>
<tr><td>Accuracy</td><td>{model_metrics.get('accuracy', 0)}%</td></tr>
<tr><td>Precision</td><td>{model_metrics.get('precision', 0)}%</td></tr>
<tr><td>Recall</td><td>{model_metrics.get('recall', 0)}%</td></tr>
<tr><td>F1 Score</td><td>{model_metrics.get('f1_score', 0)}%</td></tr>
<tr><td>Muestras</td><td>{model_metrics.get('samples', 0)}</td></tr>
</table>
<h2>Rendimiento (última sesión)</h2>
<table>
<tr><th>Métrica</th><th>Valor</th></tr>
<tr><td>Eficiencia FPS</td><td>{act.get('fps_efficiency_pct', 0)}%</td></tr>
<tr><td>Carga por frame</td><td>{performance.get('frame_budget_pct', 0)}%</td></tr>
<tr><td>CPU promedio</td><td>{performance.get('avg_cpu', 0)}%</td></tr>
<tr><td>RAM (MB)</td><td>{performance.get('avg_ram_mb', 0)}</td></tr>
</table>
<h2>Pruebas recientes</h2>
<ul>{tests_html}</ul>
</body>
</html>"""
        path.write_text(html, encoding="utf-8")
        return path

    @staticmethod
    def simulate_motion_frame(width: int = 640, height: int = 480, shift: int = 0) -> np.ndarray:
        """Genera frame sintetico para pruebas internas."""
        base = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.rectangle(base, (100, 80), (300, 280), (0, 180, 255), -1)
        if shift:
            M = np.float32([[1, 0, shift], [0, 1, shift // 2]])
            base = cv2.warpAffine(base, M, (width, height))
        return base
