"""Barra de controles principales."""

from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget


class ControlBar(QWidget):
    """Botones de control: importar, monitoreo, detener, historial y webcam."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlBar")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self.btn_import = QPushButton("Importar Video")
        self.btn_import.setObjectName("btnImport")

        self.btn_webcam = QPushButton("Activar Webcam")
        self.btn_webcam.setObjectName("btnWebcam")

        self.btn_start = QPushButton("Iniciar Monitoreo")
        self.btn_start.setObjectName("btnStart")

        self.btn_stop = QPushButton("Detener Análisis")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setEnabled(False)

        self.btn_history = QPushButton("Historial")
        self.btn_history.setObjectName("btnHistory")

        layout.addWidget(self.btn_import)
        layout.addWidget(self.btn_webcam)
        layout.addStretch()
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)
        layout.addStretch()
        layout.addWidget(self.btn_history)

