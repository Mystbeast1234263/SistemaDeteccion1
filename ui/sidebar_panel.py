"""Panel lateral derecho con métricas, ML y registros."""

from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from utils.constants import COLORS


class MetricCard(QFrame):
    """Tarjeta de métrica individual."""

    def __init__(self, title: str, value: str = "--", value_object_name: str = "cardValue", parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName(value_object_name)
        self.value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, text: str, style_class: str = "") -> None:
        self.value_label.setText(text)
        self.value_label.setProperty("class", style_class)


class SidebarPanel(QWidget):
    """Panel de monitoreo: riesgo, movimiento, predicción ML, alertas y estadísticas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarPanel")
        self.setMinimumWidth(280)
        self.setMaximumWidth(360)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("sidebarScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.viewport().setObjectName("sidebarViewport")

        content = QWidget()
        content.setObjectName("sidebarContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("PANEL DE ANÁLISIS")
        header.setObjectName("sidebarHeader")
        layout.addWidget(header)

        self.status_card = MetricCard("ESTADO DEL SISTEMA", "EN LINEA", "systemOnline")
        self.status_card.value_label.setObjectName("systemOnline")
        layout.addWidget(self.status_card)

        self.risk_card = MetricCard("NIVEL DE RIESGO", "BAJO", "riskLow")
        self.risk_card.value_label.setObjectName("riskLow")
        layout.addWidget(self.risk_card)

        movement_section = QFrame()
        movement_section.setObjectName("metricCard")
        movement_layout = QVBoxLayout(movement_section)
        movement_layout.setContentsMargins(14, 10, 14, 10)

        movement_title = QLabel("INTENSIDAD DE MOVIMIENTO")
        movement_title.setObjectName("cardTitle")
        self.movement_bar = QProgressBar()
        self.movement_bar.setObjectName("movementBar")
        self.movement_bar.setRange(0, 100)
        self.movement_value = QLabel("0%")
        self.movement_value.setObjectName("metricValueRed")
        self.movement_value.setAlignment(Qt.AlignCenter)

        movement_layout.addWidget(movement_title)
        movement_layout.addWidget(self.movement_bar)
        movement_layout.addWidget(self.movement_value)
        layout.addWidget(movement_section)

        self.prediction_card = MetricCard("PREDICCION", "SIN MODELO", "cardValue")
        layout.addWidget(self.prediction_card)

        conf_section = QFrame()
        conf_section.setObjectName("metricCard")
        conf_layout = QVBoxLayout(conf_section)
        conf_layout.setContentsMargins(14, 10, 14, 10)
        conf_title = QLabel("CONFIANZA")
        conf_title.setObjectName("cardTitle")
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setObjectName("confidenceBar")
        self.confidence_bar.setRange(0, 100)
        self.confidence_value = QLabel("0%")
        self.confidence_value.setObjectName("metricValueBlue")
        self.confidence_value.setAlignment(Qt.AlignCenter)
        conf_layout.addWidget(conf_title)
        conf_layout.addWidget(self.confidence_bar)
        conf_layout.addWidget(self.confidence_value)
        layout.addWidget(conf_section)

        self.alerts_count_card = MetricCard("ALERTAS ACTIVAS", "0", "alertCount")
        self.alerts_count_card.value_label.setObjectName("alertCount")
        layout.addWidget(self.alerts_count_card)

        stats_title = QLabel("ESTADISTICAS DE SESION")
        stats_title.setObjectName("cardTitle")
        layout.addWidget(stats_title)

        self.stats_labels = {}
        for key, label in [
            ("total_alerts", "Total alertas"),
            ("total_suspicious", "Total sospechosos"),
            ("time_analyzed", "Tiempo analizado"),
            ("avg_risk", "Riesgo promedio"),
            ("captures", "Capturas"),
            ("clips", "Clips"),
        ]:
            frame = QFrame()
            frame.setObjectName("statRow")
            row = QHBoxLayout(frame)
            row.setContentsMargins(10, 6, 10, 6)
            name_lbl = QLabel(label)
            name_lbl.setObjectName("statLabel")
            val_lbl = QLabel("0")
            val_lbl.setObjectName("statValue")
            val_lbl.setAlignment(Qt.AlignRight)
            row.addWidget(name_lbl)
            row.addWidget(val_lbl)
            layout.addWidget(frame)
            self.stats_labels[key] = val_lbl

        alerts_title = QLabel("ALERTAS DETECTADAS")
        alerts_title.setObjectName("cardTitle")
        self.alerts_list = QListWidget()
        self.alerts_list.setMaximumHeight(120)
        self.alerts_list.addItem(self._placeholder_alert())
        layout.addWidget(alerts_title)
        layout.addWidget(self.alerts_list)

        log_title = QLabel("REGISTRO DE ACTIVIDADES")
        log_title.setObjectName("cardTitle")
        self.activity_log = QTextEdit()
        self.activity_log.setObjectName("activityLog")
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(120)
        layout.addWidget(log_title)
        layout.addWidget(self.activity_log)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.log_activity("Sistema iniciado. Esperando fuente de video.", "INFO")

    def _placeholder_alert(self) -> QListWidgetItem:
        item = QListWidgetItem("Sin alertas activas")
        item.setForeground(Qt.gray)
        return item

    def set_system_status(self, status: str, active: bool = False) -> None:
        self.status_card.set_value(status)
        obj = "systemActive" if active else "systemOnline"
        self.status_card.value_label.setObjectName(obj)
        self.status_card.value_label.style().unpolish(self.status_card.value_label)
        self.status_card.value_label.style().polish(self.status_card.value_label)

    def set_alert_count(self, count: int) -> None:
        self.alerts_count_card.set_value(str(count))

    def set_risk_level(self, level: str) -> None:
        styles = {"BAJO": "riskLow", "MEDIO": "riskMedium", "ALTO": "riskHigh"}
        key = level.upper()
        self.risk_card.set_value(key, styles.get(key, "riskLow"))
        obj_name = styles.get(key, "riskLow")
        self.risk_card.value_label.setObjectName(obj_name)
        self.risk_card.value_label.style().unpolish(self.risk_card.value_label)
        self.risk_card.value_label.style().polish(self.risk_card.value_label)

    def set_movement_intensity(self, value: int) -> None:
        value = max(0, min(100, value))
        self.movement_bar.setValue(value)
        self.movement_value.setText(f"{value}%")

    def set_prediction(self, label: str, confidence: float = 0.0) -> None:
        self.prediction_card.set_value(label)
        obj = "cardValue"
        if label == "SOSPECHOSO":
            obj = "predictionSuspicious"
        elif label == "NORMAL":
            obj = "predictionNormal"
        elif label in ("SIN MODELO", "ANALIZANDO..."):
            obj = "predictionMuted"
        self.prediction_card.value_label.setObjectName(obj)
        self.prediction_card.value_label.style().unpolish(self.prediction_card.value_label)
        self.prediction_card.value_label.style().polish(self.prediction_card.value_label)

        conf = int(confidence)
        self.confidence_bar.setValue(conf)
        self.confidence_value.setText(f"{conf}%")

    def update_statistics(self, stats: dict) -> None:
        for key, lbl in self.stats_labels.items():
            lbl.setText(str(stats.get(key, "0")))
        if "total_alerts" in stats:
            self.set_alert_count(int(stats.get("total_alerts", 0)))

    def add_alert(self, message: str) -> None:
        if self.alerts_list.count() == 1:
            first = self.alerts_list.item(0)
            if first and "Sin alertas" in first.text():
                self.alerts_list.clear()

        timestamp = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"[{timestamp}] {message}")
        self.alerts_list.insertItem(0, item)

    def clear_alerts(self) -> None:
        self.alerts_list.clear()
        self.alerts_list.addItem(self._placeholder_alert())

    def log_activity(self, message: str, level: str = "INFO") -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color_map = {
            "INFO": COLORS["text_secondary"],
            "WARN": COLORS["warning"],
            "ERROR": COLORS["danger"],
            "OK": COLORS["success"],
        }
        color = color_map.get(level.upper(), COLORS["text_secondary"])
        entry = (
            f'<span style="color:{COLORS["neon_blue_dim"]}">[{timestamp}]</span> '
            f'<span style="color:{color}">[{level}]</span> {message}'
        )
        self.activity_log.append(entry)
