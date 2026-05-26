"""Panel lateral derecho con métricas y registros."""

from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
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
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

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
    """Panel de monitoreo: riesgo, movimiento, alertas y actividades."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarPanel")
        self.setMinimumWidth(280)
        self.setMaximumWidth(340)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        header = QLabel("PANEL DE ANÁLISIS")
        header.setStyleSheet(
            f"color: {COLORS['neon_blue']}; font-size: 12px; font-weight: bold; letter-spacing: 2px;"
        )
        layout.addWidget(header)

        self.risk_card = MetricCard("NIVEL DE RIESGO", "BAJO", "riskLow")
        self.risk_card.value_label.setObjectName("riskLow")
        layout.addWidget(self.risk_card)

        movement_section = QFrame()
        movement_section.setObjectName("metricCard")
        movement_layout = QVBoxLayout(movement_section)
        movement_layout.setContentsMargins(14, 12, 14, 12)

        movement_title = QLabel("INTENSIDAD DE MOVIMIENTO")
        movement_title.setObjectName("cardTitle")
        self.movement_bar = QProgressBar()
        self.movement_bar.setObjectName("movementBar")
        self.movement_bar.setRange(0, 100)
        self.movement_bar.setValue(0)
        self.movement_value = QLabel("0%")
        self.movement_value.setObjectName("cardValue")
        self.movement_value.setAlignment(Qt.AlignCenter)
        self.movement_value.setStyleSheet(f"color: {COLORS['neon_red']}; font-size: 18px;")

        movement_layout.addWidget(movement_title)
        movement_layout.addWidget(self.movement_bar)
        movement_layout.addWidget(self.movement_value)
        layout.addWidget(movement_section)

        alerts_title = QLabel("ALERTAS DETECTADAS")
        alerts_title.setObjectName("cardTitle")
        self.alerts_list = QListWidget()
        self.alerts_list.addItem(self._placeholder_alert())
        layout.addWidget(alerts_title)
        layout.addWidget(self.alerts_list, stretch=1)

        log_title = QLabel("REGISTRO DE ACTIVIDADES")
        log_title.setObjectName("cardTitle")
        self.activity_log = QTextEdit()
        self.activity_log.setObjectName("activityLog")
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(140)
        layout.addWidget(log_title)
        layout.addWidget(self.activity_log)

        self.log_activity("Sistema iniciado. Esperando fuente de video.", "INFO")

    def _placeholder_alert(self) -> QListWidgetItem:
        item = QListWidgetItem("Sin alertas activas")
        item.setForeground(Qt.gray)
        return item

    def set_risk_level(self, level: str) -> None:
        """Actualiza el nivel de riesgo (BAJO, MEDIO, ALTO)."""
        styles = {
            "BAJO": "riskLow",
            "MEDIO": "riskMedium",
            "ALTO": "riskHigh",
        }
        key = level.upper()
        self.risk_card.set_value(key, styles.get(key, "riskLow"))
        obj_name = styles.get(key, "riskLow")
        self.risk_card.value_label.setObjectName(obj_name)
        self.risk_card.value_label.style().unpolish(self.risk_card.value_label)
        self.risk_card.value_label.style().polish(self.risk_card.value_label)

    def set_movement_intensity(self, value: int) -> None:
        """Actualiza la barra de intensidad de movimiento (0-100)."""
        value = max(0, min(100, value))
        self.movement_bar.setValue(value)
        self.movement_value.setText(f"{value}%")

    def add_alert(self, message: str) -> None:
        """Agrega una alerta a la lista."""
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
        """Registra una actividad en el log."""
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

