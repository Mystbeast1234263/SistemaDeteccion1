"""Barra de navegacion principal."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget


class NavBar(QWidget):
    """Pestañas: Monitoreo, Evidencias, Pruebas, Metricas."""

    section_changed = pyqtSignal(int)

    SECTION_MONITOR = 0
    SECTION_EVIDENCE = 1
    SECTION_TESTS = 2
    SECTION_METRICS = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("navBar")
        self._active = 0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 0)
        layout.setSpacing(8)

        self._buttons: list[QPushButton] = []
        specs = [
            ("btnNavMonitor", "Monitoreo"),
            ("btnNavEvidence", "Evidencias"),
            ("btnNavTests", "Pruebas"),
            ("btnNavMetrics", "Metricas"),
        ]
        for idx, (obj_name, text) in enumerate(specs):
            btn = QPushButton(text)
            btn.setObjectName(obj_name)
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            btn.clicked.connect(lambda checked, i=idx: self._select(i))
            layout.addWidget(btn)
            self._buttons.append(btn)

        layout.addStretch()

    def _select(self, index: int) -> None:
        self._active = index
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)
        self.section_changed.emit(index)

    def select_monitor(self) -> None:
        self._select(self.SECTION_MONITOR)

    def select_evidence(self) -> None:
        self._select(self.SECTION_EVIDENCE)

    def select_tests(self) -> None:
        self._select(self.SECTION_TESTS)

    def select_metrics(self) -> None:
        self._select(self.SECTION_METRICS)
