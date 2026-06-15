"""Panel de pruebas de validacion Sprint 5."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class TestCaseCard(QFrame):
    """Tarjeta de un caso de prueba."""

    run_automated = pyqtSignal(str)
    record_session = pyqtSignal(str)

    def __init__(self, case: dict, parent=None):
        super().__init__(parent)
        self.case_id = case["id"]
        self.setObjectName("testCaseCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        title = QLabel(case["name"])
        title.setObjectName("testCaseTitle")
        layout.addWidget(title)

        desc = QLabel(case["description"])
        desc.setObjectName("testCaseDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        expected = QLabel(f"Esperado: {case['expected']}")
        expected.setObjectName("testCaseExpected")
        expected.setWordWrap(True)
        layout.addWidget(expected)

        last = case.get("last_result")
        if last:
            status = "APROBADO" if last.get("passed") else "REVISAR"
            result_lbl = QLabel(
                f"Ultimo: {status} — {last.get('evaluation', '')} ({last.get('recorded_at', '')})"
            )
        else:
            result_lbl = QLabel("Ultimo: sin registrar")
        result_lbl.setObjectName("testCaseResult")
        result_lbl.setWordWrap(True)
        layout.addWidget(result_lbl)

        btn_row = QHBoxLayout()
        if case.get("type") == "automated":
            btn_auto = QPushButton("Ejecutar automatico")
            btn_auto.setObjectName("btnTestAuto")
            btn_auto.clicked.connect(lambda: self.run_automated.emit(self.case_id))
            btn_row.addWidget(btn_auto)
        else:
            btn_rec = QPushButton("Registrar resultado")
            btn_rec.setObjectName("btnTestRecord")
            btn_rec.clicked.connect(lambda: self.record_session.emit(self.case_id))
            btn_row.addWidget(btn_rec)
        btn_row.addStretch()
        layout.addLayout(btn_row)


class TestPanel(QWidget):
    """Seccion de pruebas con casos documentados y generacion de reportes."""

    run_automated = pyqtSignal(str)
    record_session = pyqtSignal(str)
    generate_reports = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("testPanel")
        self._cards: list[TestCaseCard] = []
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(10)

        header_row = QHBoxLayout()
        title = QLabel("MODULO DE TESTING")
        title.setObjectName("panelTitle")
        header_row.addWidget(title)
        header_row.addStretch()
        self.btn_reports = QPushButton("Generar reportes")
        self.btn_reports.setObjectName("btnGenerateReports")
        self.btn_reports.clicked.connect(self.generate_reports.emit)
        header_row.addWidget(self.btn_reports)
        outer.addLayout(header_row)

        hint = QLabel(
            "Ejecute pruebas automaticas o registre resultados tras monitorear video/webcam. "
            "Los resultados se guardan en testing/test_results.json."
        )
        hint.setObjectName("testHint")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._cases_container = QWidget()
        self._cases_layout = QVBoxLayout(self._cases_container)
        self._cases_layout.setSpacing(10)
        scroll.setWidget(self._cases_container)
        outer.addWidget(scroll, stretch=1)

        self.log_output = QTextEdit()
        self.log_output.setObjectName("testLog")
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        self.log_output.setPlaceholderText("Registro de pruebas...")
        outer.addWidget(self.log_output)

    def set_cases(self, cases: list[dict]) -> None:
        while self._cases_layout.count():
            item = self._cases_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()
        for case in cases:
            card = TestCaseCard(case)
            card.run_automated.connect(self.run_automated.emit)
            card.record_session.connect(self.record_session.emit)
            self._cases_layout.addWidget(card)
            self._cards.append(card)
        self._cases_layout.addStretch()

    def append_log(self, message: str) -> None:
        self.log_output.append(message)
