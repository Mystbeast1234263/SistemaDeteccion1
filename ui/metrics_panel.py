"""Panel de metricas avanzadas Sprint 5."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class MetricsSection(QFrame):
    """Bloque titulado de metricas."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("metricsSection")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QLabel(title)
        header.setObjectName("metricsSectionTitle")
        layout.addWidget(header)

        self.grid = QGridLayout()
        self.grid.setSpacing(8)
        self.grid.setColumnStretch(1, 1)
        layout.addLayout(self.grid)
        self._row = 0
        self._labels: dict[str, QLabel] = {}

    def set_metric(self, key: str, label: str, value: str) -> None:
        if key not in self._labels:
            name = QLabel(label)
            name.setObjectName("metricsLabel")
            val = QLabel(value)
            val.setObjectName("metricsValue")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.grid.addWidget(name, self._row, 0)
            self.grid.addWidget(val, self._row, 1)
            self._labels[key] = val
            self._row += 1
        else:
            self._labels[key].setText(value)


class MetricsPanel(QWidget):
    """Dashboard profesional de metricas en porcentajes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("metricsPanel")
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)

        title = QLabel("METRICAS AVANZADAS")
        title.setObjectName("panelTitle")
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("metricsScroll")

        content = QWidget()
        content.setObjectName("metricsContent")
        layout = QVBoxLayout(content)
        layout.setSpacing(12)

        self.sec_activity = MetricsSection("ACTIVIDAD")
        self.sec_movement = MetricsSection("MOVIMIENTO")
        self.sec_risk = MetricsSection("RIESGO")
        self.sec_suspicious = MetricsSection("COMPORTAMIENTOS SOSPECHOSOS")
        self.sec_evidence = MetricsSection("EVIDENCIAS")
        self.sec_model = MetricsSection("MODELO")
        self.sec_performance = MetricsSection("RENDIMIENTO")

        for sec in (
            self.sec_activity,
            self.sec_movement,
            self.sec_risk,
            self.sec_suspicious,
            self.sec_evidence,
            self.sec_model,
            self.sec_performance,
        ):
            layout.addWidget(sec)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    @staticmethod
    def _pct(value: float, suffix: str = "%") -> str:
        return f"{value}{suffix}"

    def update_all(
        self,
        advanced: dict,
        model: dict,
        performance: dict,
        dataset_total: int = 0,
    ) -> None:
        act = advanced.get("activity", {})
        mov = advanced.get("movement", {})
        risk = advanced.get("risk", {})
        susp = advanced.get("suspicious", {})
        ev = advanced.get("evidence", {})
        alerts = advanced.get("alerts", {})

        fps_eff = act.get("fps_efficiency_pct", 0)
        self.sec_activity.set_metric("time", "Tiempo analizado", act.get("time_analyzed", "00:00"))
        self.sec_activity.set_metric("frames", "Frames procesados", str(act.get("frames_processed", 0)))
        self.sec_activity.set_metric("fps", "Eficiencia FPS", self._pct(fps_eff))
        self.sec_activity.set_metric("sessions", "Sesiones analizadas", str(act.get("sessions_count", 0)))

        self.sec_movement.set_metric(
            "avg_i", "Intensidad promedio", mov.get("avg_intensity_pct", f"{mov.get('avg_intensity', 0)}%")
        )
        self.sec_movement.set_metric(
            "max_i", "Intensidad maxima", mov.get("max_intensity_pct", f"{mov.get('max_intensity', 0)}%")
        )
        self.sec_movement.set_metric(
            "min_i", "Intensidad minima", mov.get("min_intensity_pct", f"{mov.get('min_intensity', 0)}%")
        )
        self.sec_movement.set_metric("mag", "Magnitud promedio", str(mov.get("avg_magnitude", 0)))
        self.sec_movement.set_metric("dir", "Direccion predominante", f"{mov.get('avg_direction', 0)} deg")

        self.sec_risk.set_metric("low", "Riesgo bajo", self._pct(risk.get("low_pct", 0)))
        self.sec_risk.set_metric("med", "Riesgo medio", self._pct(risk.get("medium_pct", 0)))
        self.sec_risk.set_metric("high", "Riesgo alto", self._pct(risk.get("high_pct", 0)))
        self.sec_risk.set_metric(
            "avg_r", "Riesgo promedio", risk.get("avg_risk_pct", f"{risk.get('avg_risk', 0)}%")
        )

        self.sec_suspicious.set_metric(
            "tot", "Detecciones sospechosas", self._pct(susp.get("detect_rate_pct", 0))
        )
        self.sec_suspicious.set_metric(
            "conf", "Confianza promedio", susp.get("avg_confidence_pct", f"{susp.get('avg_confidence', 0)}%")
        )
        self.sec_suspicious.set_metric(
            "maxc", "Maxima confianza", susp.get("max_confidence_pct", f"{susp.get('max_confidence', 0)}%")
        )
        self.sec_suspicious.set_metric(
            "rate", "Tasa de predicciones ML", self._pct(susp.get("suspicious_rate", 0))
        )

        self.sec_evidence.set_metric("cap", "Capturas sobre sospechas", self._pct(ev.get("evidence_rate_pct", 0)))
        self.sec_evidence.set_metric("clip", "Clips generados", str(ev.get("clips", 0)))
        self.sec_evidence.set_metric("last", "Ultima evidencia", ev.get("last_evidence_at", "—"))

        if model.get("is_loaded"):
            self.sec_model.set_metric("acc", "Accuracy", self._pct(model.get("accuracy", 0)))
            self.sec_model.set_metric("prec", "Precision", self._pct(model.get("precision", 0)))
            self.sec_model.set_metric("rec", "Recall", self._pct(model.get("recall", 0)))
            self.sec_model.set_metric("f1", "F1 Score", self._pct(model.get("f1_score", 0)))
            samples = model.get("samples", 0)
            ds_pct = round(samples / max(dataset_total, 1) * 100, 1) if dataset_total else 100.0
            self.sec_model.set_metric("samples", "Cobertura entrenamiento", self._pct(ds_pct))
            self.sec_model.set_metric("date", "Ultimo entrenamiento", model.get("trained_at", "—"))
        else:
            for key, label, val in (
                ("acc", "Accuracy", "—"),
                ("prec", "Precision", "—"),
                ("rec", "Recall", "—"),
                ("f1", "F1 Score", "—"),
                ("samples", "Cobertura entrenamiento", "—"),
                ("date", "Ultimo entrenamiento", "—"),
            ):
                self.sec_model.set_metric(key, label, val)

        psutil_ok = performance.get("psutil_available", False)
        cpu = self._pct(performance.get("avg_cpu", 0)) if psutil_ok else "N/D"
        ram_pct = performance.get("ram_usage_pct", 0)
        ram = self._pct(ram_pct) if psutil_ok else "N/D"
        frame_pct = performance.get("frame_budget_pct", 0)
        self.sec_performance.set_metric("cpu", "Uso CPU", cpu)
        self.sec_performance.set_metric("ram", "Uso RAM estimado", ram)
        self.sec_performance.set_metric("frame", "Carga por frame", self._pct(frame_pct))
        self.sec_performance.set_metric(
            "alerts", "Tasa de alertas", self._pct(alerts.get("alert_rate_pct", 0))
        )
