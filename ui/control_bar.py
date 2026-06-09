"""Barra de controles principales."""

from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget


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

        self.chk_sound = QCheckBox("Alertas sonoras")
        self.chk_sound.setObjectName("chkSoundAlerts")
        self.chk_sound.setChecked(True)

        row1.addWidget(self.btn_import)
        row1.addWidget(self.btn_webcam)
        row1.addStretch()
        row1.addWidget(self.btn_start)
        row1.addWidget(self.btn_stop)
        row1.addStretch()
        row1.addWidget(self.chk_sound)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self.btn_toggle_label = QPushButton("Etiquetar")
        self.btn_toggle_label.setObjectName("btnToggleLabel")
        self.btn_toggle_label.setCheckable(True)
        self.btn_toggle_label.setEnabled(False)

        self.label_panel = QWidget()
        self.label_panel.setObjectName("labelPanel")
        label_layout = QHBoxLayout(self.label_panel)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(8)

        self.btn_label_normal = QPushButton("Normal")
        self.btn_label_normal.setObjectName("btnLabelNormal")

        self.btn_label_suspicious = QPushButton("Sospechoso")
        self.btn_label_suspicious.setObjectName("btnLabelSuspicious")

        label_layout.addWidget(self.btn_label_normal)
        label_layout.addWidget(self.btn_label_suspicious)
        self.label_panel.setVisible(False)

        self.btn_toggle_model = QPushButton("Modelo")
        self.btn_toggle_model.setObjectName("btnToggleModel")
        self.btn_toggle_model.setCheckable(True)

        self.model_panel = QWidget()
        self.model_panel.setObjectName("modelPanel")
        model_layout = QHBoxLayout(self.model_panel)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.setSpacing(8)

        self.btn_train = QPushButton("Entrenar")
        self.btn_train.setObjectName("btnTrain")

        self.btn_save_model = QPushButton("Guardar")
        self.btn_save_model.setObjectName("btnSaveModel")

        self.btn_load_model = QPushButton("Cargar")
        self.btn_load_model.setObjectName("btnLoadModel")

        self.btn_import_model = QPushButton("Importar")
        self.btn_import_model.setObjectName("btnImportModel")

        self.btn_export_model = QPushButton("Exportar")
        self.btn_export_model.setObjectName("btnExportModel")

        model_layout.addWidget(self.btn_train)
        model_layout.addWidget(self.btn_save_model)
        model_layout.addWidget(self.btn_load_model)
        model_layout.addWidget(self.btn_import_model)
        model_layout.addWidget(self.btn_export_model)
        self.model_panel.setVisible(False)

        self.btn_toggle_label.toggled.connect(self.label_panel.setVisible)
        self.btn_toggle_model.toggled.connect(self.model_panel.setVisible)

        row2.addWidget(self.btn_toggle_label)
        row2.addWidget(self.label_panel)
        row2.addStretch()
        row2.addWidget(self.btn_toggle_model)
        row2.addWidget(self.model_panel)
        layout.addLayout(row2)

    def set_labeling_available(self, available: bool) -> None:
        """Habilita etiquetado cuando hay video o webcam con frame visible."""
        self.btn_toggle_label.setEnabled(available)
        self.btn_label_normal.setEnabled(available)
        self.btn_label_suspicious.setEnabled(available)
        if not available:
            self.btn_toggle_label.setChecked(False)
            self.label_panel.setVisible(False)
