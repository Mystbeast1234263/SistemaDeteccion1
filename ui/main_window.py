"""Ventana principal del sistema de monitoreo."""

import os
import time
from datetime import datetime

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ui.control_bar import ControlBar
from ui.sidebar_panel import SidebarPanel
from ui.video_panel import VideoPanel
from utils.constants import (
    ALERT_COOLDOWN_SEC,
    ALERT_ELEVATED_MIN,
    ALERT_INTENSE_MIN,
    ALERT_MAX_ITEMS,
    ALERT_MOTION_MIN,
    APP_NAME,
    APP_SHORT_NAME,
    VIDEO_EXTENSIONS,
)
from video.optical_flow import OpticalFlowAnalyzer
from video.player import VideoPlayer
from video.webcam import WebcamCapture


class MainWindow(QMainWindow):
    """Dashboard principal de monitoreo inteligente."""

    def __init__(self):
        super().__init__()
        self._video_path = ""
        self._monitoring_active = False
        self._source_mode = None  # "file" | "webcam" | None
        self._last_alert_time = 0.0
        self._last_risk_level = "BAJO"

        self.video_player = VideoPlayer(self)
        self.webcam = WebcamCapture(parent=self)
        self.motion_analyzer = OpticalFlowAnalyzer()

        self._setup_window()
        self._build_ui()
        self._connect_signals()
        self._start_clock()

    def _setup_window(self) -> None:
        self.setWindowTitle(f"{APP_SHORT_NAME} — {APP_NAME}")
        self.setMinimumSize(1280, 720)
        self.resize(1400, 820)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._create_header())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 12, 8, 16)
        left_layout.setSpacing(12)

        self.video_panel = VideoPanel()
        self.control_bar = ControlBar()

        left_layout.addWidget(self.video_panel, stretch=1)
        left_layout.addWidget(self.control_bar)

        self.sidebar = SidebarPanel()

        splitter.addWidget(left_panel)
        splitter.addWidget(self.sidebar)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([1000, 300])

        root_layout.addWidget(splitter, stretch=1)

    def _create_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("headerBar")
        header.setFixedHeight(56)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        title_block = QVBoxLayout()
        title_block.setSpacing(0)
        title = QLabel(APP_SHORT_NAME)
        title.setObjectName("appTitle")
        subtitle = QLabel(APP_NAME)
        subtitle.setObjectName("appSubtitle")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        self.status_badge = QLabel("EN LINEA")
        self.status_badge.setObjectName("statusBadge")

        self.clock_label = QLabel()
        self.clock_label.setObjectName("clockLabel")
        self.clock_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addLayout(title_block)
        layout.addStretch()
        layout.addWidget(self.status_badge)
        layout.addSpacing(24)
        layout.addWidget(self.clock_label)

        return header

    def _connect_signals(self) -> None:
        self.control_bar.btn_import.clicked.connect(self._on_import_video)
        self.control_bar.btn_webcam.clicked.connect(self._on_toggle_webcam)
        self.control_bar.btn_start.clicked.connect(self._on_start_monitoring)
        self.control_bar.btn_stop.clicked.connect(self._on_stop_analysis)
        self.control_bar.btn_history.clicked.connect(self._on_show_history)

        self.video_player.frame_ready.connect(self._on_frame_ready)
        self.video_player.playback_finished.connect(self._on_playback_finished)
        self.video_player.error_occurred.connect(self._on_video_error)

        self.webcam.frame_ready.connect(self._on_frame_ready)
        self.webcam.error_occurred.connect(self._on_video_error)
        self.webcam.started.connect(self._on_webcam_started)
        self.webcam.stopped.connect(self._on_webcam_stopped)

    def _start_clock(self) -> None:
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self) -> None:
        now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        self.clock_label.setText(now)

    def _on_import_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar video",
            "",
            VIDEO_EXTENSIONS,
        )
        if not path:
            return

        self._stop_all_sources()
        if not self.video_player.load(path):
            return

        self._video_path = path
        self._source_mode = "file"
        filename = os.path.basename(path)

        ret, frame = self._read_first_frame(path)
        if ret and frame is not None:
            self.video_panel.show_frame(
                frame,
                f"VIDEO CARGADO — {filename}",
            )

        self.control_bar.btn_start.setEnabled(True)
        self.sidebar.log_activity(f"Video importado: {filename}", "OK")
        self.sidebar.set_risk_level("BAJO")

    def _read_first_frame(self, path: str):
        import cv2

        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()
        cap.release()
        return ret, frame

    def _on_toggle_webcam(self) -> None:
        if self.webcam.is_active:
            self.webcam.stop()
            return

        self._stop_all_sources(keep_ui=True)
        if self.webcam.start():
            self._source_mode = "webcam"
            self.control_bar.btn_webcam.setText("Detener Webcam")
            self.control_bar.btn_start.setEnabled(True)
        else:
            self._source_mode = None

    def _on_webcam_started(self) -> None:
        self.video_panel.set_overlay("WEBCAM ACTIVA — TRANSMISIÓN EN VIVO")
        self.sidebar.log_activity("Webcam activada correctamente.", "OK")
        self.sidebar.set_risk_level("BAJO")
        self._update_control_state()

    def _on_webcam_stopped(self) -> None:
        self.control_bar.btn_webcam.setText("Activar Webcam")
        self.video_panel.clear_display()
        self.sidebar.log_activity("Webcam desactivada.", "INFO")
        self._monitoring_active = False
        self._source_mode = None
        self._update_control_state()

    def _on_start_monitoring(self) -> None:
        if self._source_mode == "file":
            if not self._video_path:
                QMessageBox.warning(self, "Sin video", "Importe un video antes de iniciar.")
                return
            self.video_player.seek_start()
            self.video_player.play()
            self.video_panel.set_overlay(
                f"MONITOREO ACTIVO — {os.path.basename(self._video_path)}"
            )
            self.sidebar.log_activity("Reproducción de video iniciada.", "OK")
        elif self._source_mode == "webcam":
            if not self.webcam.is_active:
                self._on_toggle_webcam()
            self.video_panel.set_overlay("MONITOREO ACTIVO — WEBCAM EN VIVO")
            self.sidebar.log_activity("Monitoreo por webcam activo.", "OK")
        else:
            QMessageBox.information(
                self,
                "Fuente requerida",
                "Importe un video o active la webcam para iniciar el monitoreo.",
            )
            return

        self._monitoring_active = True
        self._last_alert_time = 0.0
        self._last_risk_level = "BAJO"
        self.motion_analyzer.reset()
        self.sidebar.clear_alerts()
        self.status_badge.setText("ANALISIS ACTIVO")
        self.status_badge.setStyleSheet(
            "color: #00d4ff; font-size: 11px; font-weight: bold; "
            "padding: 4px 12px; background-color: #141c2e; "
            "border: 1px solid #00d4ff; border-radius: 4px;"
        )
        self.sidebar.set_movement_intensity(0)
        self.sidebar.log_activity("Flujo optico Farneback activado.", "OK")
        self._update_control_state()

    def _on_stop_analysis(self) -> None:
        self.video_player.pause()
        if self.webcam.is_active:
            self.webcam.stop()

        self._monitoring_active = False
        self.motion_analyzer.reset()
        self.status_badge.setText("EN LINEA")
        self.status_badge.setStyleSheet("")
        self.sidebar.log_activity("Analisis detenido por el operador.", "WARN")
        self.sidebar.set_movement_intensity(0)
        self.sidebar.set_risk_level("BAJO")
        self._update_control_state()

    def _on_show_history(self) -> None:
        QMessageBox.information(
            self,
            "Historial",
            "El módulo de historial estará disponible en el próximo sprint.\n\n"
            "Por ahora puede consultar el Registro de Actividades en el panel lateral.",
        )
        self.sidebar.log_activity("Consulta de historial (próximo sprint).", "INFO")

    def _on_frame_ready(self, frame) -> None:
        if frame is None or not getattr(frame, "size", 0):
            return

        display_frame = frame

        if self._monitoring_active:
            result = self.motion_analyzer.process(frame, draw_overlay=True)
            display_frame = result.annotated_frame
            self._update_motion_metrics(result)

        if self._source_mode == "file":
            if self._monitoring_active:
                label = f"ANALISIS — {os.path.basename(self._video_path)}"
            else:
                label = f"REPRODUCCION — {os.path.basename(self._video_path)}"
        elif self._source_mode == "webcam":
            if self._monitoring_active:
                label = "ANALISIS EN VIVO — WEBCAM"
            else:
                label = "WEBCAM — TRANSMISION EN VIVO"
        else:
            label = "MONITOREO"

        self.video_panel.show_frame(display_frame, label)

    def _update_motion_metrics(self, result) -> None:
        self.sidebar.set_movement_intensity(result.intensidad_movimiento)
        self.sidebar.set_risk_level(result.nivel_riesgo)

        if result.nivel_riesgo != self._last_risk_level:
            self.sidebar.log_activity(
                f"Nivel de riesgo: {result.nivel_riesgo}",
                "WARN" if result.nivel_riesgo != "BAJO" else "INFO",
            )
            self._last_risk_level = result.nivel_riesgo

        if not result.motion_detected:
            return

        now = time.time()
        if now - self._last_alert_time < ALERT_COOLDOWN_SEC:
            return

        intensity = result.intensidad_movimiento
        alert_msg = None
        log_msg = None

        if intensity >= ALERT_INTENSE_MIN:
            alert_msg = f"Movimiento intenso — {intensity}% (riesgo ALTO)"
            log_msg = f"Riesgo alto — intensidad {intensity}%"
        elif intensity >= ALERT_ELEVATED_MIN:
            alert_msg = f"Actividad elevada — {intensity}%"
            log_msg = f"Actividad elevada — intensidad {intensity}%"
        elif intensity >= ALERT_MOTION_MIN:
            alert_msg = f"Movimiento detectado — {intensity}%"
            log_msg = f"Movimiento detectado — intensidad {intensity}%"

        if alert_msg:
            self.sidebar.add_alert(alert_msg)
            self.sidebar.log_activity(log_msg, "WARN")
            self._last_alert_time = now

            if self.sidebar.alerts_list.count() > ALERT_MAX_ITEMS:
                self.sidebar.alerts_list.takeItem(self.sidebar.alerts_list.count() - 1)

    def _on_playback_finished(self) -> None:
        self.sidebar.log_activity("Reproduccion de video finalizada.", "INFO")
        self._monitoring_active = False
        self.motion_analyzer.reset()
        self.sidebar.set_movement_intensity(0)
        self.sidebar.set_risk_level("BAJO")
        self._update_control_state()

    def _on_video_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error de video", message)
        self.sidebar.log_activity(message, "ERROR")

    def _stop_all_sources(self, keep_ui: bool = False) -> None:
        self.video_player.stop()
        if self.webcam.is_active:
            self.webcam.stop()
        self._video_path = ""
        self._source_mode = None
        self._monitoring_active = False
        self.motion_analyzer.reset()
        if not keep_ui:
            self.video_panel.clear_display()
            self.control_bar.btn_webcam.setText("Activar Webcam")
        self._update_control_state()

    def _update_control_state(self) -> None:
        has_source = self._source_mode is not None or self.webcam.is_active
        self.control_bar.btn_start.setEnabled(has_source and not self._monitoring_active)
        self.control_bar.btn_stop.setEnabled(self._monitoring_active)
        self.control_bar.btn_import.setEnabled(not self.webcam.is_active)

    def closeEvent(self, event) -> None:
        self.video_player.stop()
        self.webcam.stop()
        self.motion_analyzer.reset()
        event.accept()

