"""Barra de navegación principal Monitoreo / Evidencias."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget


class NavBar(QWidget):
    """Pestañas de sección sin reemplazar la pantalla principal."""

    section_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("navBar")
        self._active = 0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 0)
        layout.setSpacing(8)

        self.btn_monitor = QPushButton("Monitoreo")
        self.btn_monitor.setObjectName("btnNavMonitor")
        self.btn_monitor.setCheckable(True)
        self.btn_monitor.setChecked(True)

        self.btn_evidence = QPushButton("Evidencias")
        self.btn_evidence.setObjectName("btnNavEvidence")
        self.btn_evidence.setCheckable(True)

        self.btn_monitor.clicked.connect(lambda: self._select(0))
        self.btn_evidence.clicked.connect(lambda: self._select(1))

        layout.addWidget(self.btn_monitor)
        layout.addWidget(self.btn_evidence)
        layout.addStretch()

    def _select(self, index: int) -> None:
        self._active = index
        self.btn_monitor.setChecked(index == 0)
        self.btn_evidence.setChecked(index == 1)
        self.section_changed.emit(index)

    def select_evidence(self) -> None:
        self._select(1)

    def select_monitor(self) -> None:
        self._select(0)
