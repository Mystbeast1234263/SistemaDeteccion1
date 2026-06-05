"""Barra de controles principales."""

from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget


class ControlBar(QWidget):
    """Botones de control: video, monitoreo, ML y etiquetado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlBar")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(10)

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

        row1.addWidget(self.btn_import)
        row1.addWidget(self.btn_webcam)
        row1.addStretch()
        row1.addWidget(self.btn_start)
        row1.addWidget(self.btn_stop)
        row1.addStretch()
        row1.addWidget(self.btn_history)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self.btn_label_normal = QPushButton("Guardar como Normal")
        self.btn_label_normal.setObjectName("btnLabelNormal")

        self.btn_label_suspicious = QPushButton("Guardar como Sospechoso")
        self.btn_label_suspicious.setObjectName("btnLabelSuspicious")

        self.btn_train = QPushButton("Entrenar Modelo")
        self.btn_train.setObjectName("btnTrain")

        self.btn_save_model = QPushButton("Guardar Modelo")
        self.btn_save_model.setObjectName("btnSaveModel")

        self.btn_load_model = QPushButton("Cargar Modelo")
        self.btn_load_model.setObjectName("btnLoadModel")

        self.btn_import_model = QPushButton("Importar Modelo")
        self.btn_import_model.setObjectName("btnImportModel")

        self.btn_export_model = QPushButton("Exportar Modelo")
        self.btn_export_model.setObjectName("btnExportModel")

        row2.addWidget(self.btn_label_normal)
        row2.addWidget(self.btn_label_suspicious)
        row2.addStretch()
        row2.addWidget(self.btn_train)
        row2.addWidget(self.btn_save_model)
        row2.addWidget(self.btn_load_model)
        row2.addWidget(self.btn_import_model)
        row2.addWidget(self.btn_export_model)
        layout.addLayout(row2)
