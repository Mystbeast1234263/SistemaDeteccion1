"""Ventana principal del sistema de monitoreo."""

import os
import time
from datetime import datetime

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ml.dataset_manager import DatasetManager
from ml.evidence_catalog import EvidenceCatalog
from ml.evidence_manager import EvidenceManager
from ml.incident_history import IncidentHistory
from ml.model_trainer import ModelTrainer
from ml.predictor import BehaviorPredictor
from ml.segment_tracker import SegmentTracker
from ml.statistics import SessionStatistics
from ui.control_bar import ControlBar
from ui.evidence_panel import EvidencePanel
from ui.nav_bar import NavBar
from ui.sidebar_panel import SidebarPanel
from ui.timeline_bar import TimelineBar
from ui.video_panel import VideoPanel
from utils.constants import (
    ALERT_COOLDOWN_SEC,
    ALERT_ELEVATED_MIN,
    ALERT_INTENSE_MIN,
    ALERT_MAX_ITEMS,
    ALERT_MOTION_MIN,
    ANALYSIS_FRAME_INTERVAL,
    APP_NAME,
    APP_SHORT_NAME,
    DATASET_AUTO_INTERVAL,
    EVIDENCE_FRAME_INTERVAL,
    MODELS_DIR,
    SUSPICIOUS_LOG_COOLDOWN_SEC,
    UI_UPDATE_INTERVAL,
    VIDEO_EXTENSIONS,
)
from utils.sound_alerts import SoundAlertManager
from video.optical_flow import OpticalFlowAnalyzer
from video.player import VideoPlayer
from video.webcam import WebcamCapture


class MainWindow(QMainWindow):
    """Dashboard principal de monitoreo inteligente."""

    def __init__(self):
        super().__init__()
        self._video_path = ""
        self._monitoring_active = False
        self._source_mode = None
        self._last_alert_time = 0.0
        self._last_suspicious_log_time = 0.0
        self._last_risk_level = "BAJO"
        self._last_features = None
        self._last_flow_result = None
        self._last_frame = None
        self._frame_counter = 0
        self._analysis_start = 0.0
        self._webcam_elapsed = 0.0

        self.video_player = VideoPlayer(self)
        self.webcam = WebcamCapture(parent=self)
        self.motion_analyzer = OpticalFlowAnalyzer()

        self.dataset_manager = DatasetManager()
        self.model_trainer = ModelTrainer()
        self.predictor = BehaviorPredictor(self.model_trainer)
        self.evidence_manager = EvidenceManager()
        self.incident_history = IncidentHistory()
        self.evidence_catalog = EvidenceCatalog(self.incident_history)
        self.sound_alerts = SoundAlertManager()
        self.session_stats = SessionStatistics()
        self.segment_tracker = SegmentTracker()

        self._setup_window()
        self._build_ui()
        self._connect_signals()
        self._auto_load_model()
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
        self.nav_bar = NavBar()
        root_layout.addWidget(self.nav_bar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)

        self.section_stack = QStackedWidget()

        monitor_page = QWidget()
        left_layout = QVBoxLayout(monitor_page)
        left_layout.setContentsMargins(16, 12, 8, 16)
        left_layout.setSpacing(8)

        self.video_panel = VideoPanel()
        self.timeline_bar = TimelineBar()
        self.control_bar = ControlBar()

        left_layout.addWidget(self.video_panel, stretch=1)
        left_layout.addWidget(self.timeline_bar)
        left_layout.addWidget(self.control_bar)

        self.evidence_panel = EvidencePanel(self.evidence_catalog)

        self.section_stack.addWidget(monitor_page)
        self.section_stack.addWidget(self.evidence_panel)

        self.sidebar = SidebarPanel()
        self.sidebar.set_system_status("EN LINEA", active=False)

        splitter.addWidget(self.section_stack)
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
        self.control_bar.chk_sound.toggled.connect(self.sound_alerts.set_enabled)

        self.nav_bar.section_changed.connect(self._on_section_changed)
        self.evidence_panel.jump_to_video_time.connect(self._on_incident_jump_to_video)

        self.control_bar.btn_label_normal.clicked.connect(
            lambda: self._on_manual_label("normal")
        )
        self.control_bar.btn_label_suspicious.clicked.connect(
            lambda: self._on_manual_label("sospechoso")
        )
        self.control_bar.btn_train.clicked.connect(self._on_train_model)
        self.control_bar.btn_save_model.clicked.connect(self._on_save_model)
        self.control_bar.btn_load_model.clicked.connect(self._on_load_model)
        self.control_bar.btn_import_model.clicked.connect(self._on_import_model)
        self.control_bar.btn_export_model.clicked.connect(self._on_export_model)

        self.video_player.frame_ready.connect(self._on_frame_ready)
        self.video_player.playback_finished.connect(self._on_playback_finished)
        self.video_player.position_changed.connect(self._on_position_changed)
        self.video_player.error_occurred.connect(self._on_video_error)

        self.webcam.frame_ready.connect(self._on_frame_ready)
        self.webcam.error_occurred.connect(self._on_video_error)
        self.webcam.started.connect(self._on_webcam_started)
        self.webcam.stopped.connect(self._on_webcam_stopped)

        self.timeline_bar.seek_requested.connect(self._on_timeline_seek)
        self.timeline_bar.marker_clicked.connect(self._on_marker_clicked)

    def _start_clock(self) -> None:
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self) -> None:
        now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        self.clock_label.setText(now)

    def _current_time_sec(self) -> float:
        if self._source_mode == "file":
            return self.video_player.current_time
        if self._source_mode == "webcam" and self._monitoring_active:
            return time.time() - self._analysis_start
        return 0.0

    def _on_import_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar video", "", VIDEO_EXTENSIONS,
        )
        if not path:
            return

        self._stop_all_sources()
        if not self.video_player.load(path):
            return

        self._video_path = path
        self._source_mode = "file"
        filename = os.path.basename(path)

        self.timeline_bar.set_duration(self.video_player.duration)
        self.evidence_manager.frame_buffer.set_fps(self.video_player.fps)

        ret, frame = self._read_first_frame(path)
        if ret and frame is not None:
            self._last_frame = frame
            self.video_panel.show_frame(frame, f"VIDEO CARGADO — {filename}")

        self.control_bar.btn_start.setEnabled(True)
        self._update_control_state()
        self.sidebar.log_activity(f"Video importado: {filename}", "OK")
        self.sidebar.set_risk_level("BAJO")
        self.sidebar.set_system_status("VIDEO CARGADO", active=False)

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
            self.timeline_bar.reset()
            self.control_bar.btn_webcam.setText("Detener Webcam")
            self.control_bar.btn_start.setEnabled(True)
        else:
            self._source_mode = None

    def _on_webcam_started(self) -> None:
        self.video_panel.set_overlay("WEBCAM ACTIVA — TRANSMISION EN VIVO")
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
            self.sidebar.log_activity("Reproduccion de video iniciada.", "OK")
        elif self._source_mode == "webcam":
            if not self.webcam.is_active:
                self._on_toggle_webcam()
            self.video_panel.set_overlay("MONITOREO ACTIVO — WEBCAM EN VIVO")
            self.sidebar.log_activity("Monitoreo por webcam activo.", "OK")
        else:
            QMessageBox.information(
                self, "Fuente requerida",
                "Importe un video o active la webcam para iniciar el monitoreo.",
            )
            return

        self._monitoring_active = True
        self._analysis_start = time.time()
        self._frame_counter = 0
        self._last_alert_time = 0.0
        self._last_suspicious_log_time = 0.0
        self._last_risk_level = "BAJO"
        self._last_flow_result = None
        self.motion_analyzer.reset()
        self.segment_tracker.reset()
        self.session_stats.reset()
        self.evidence_manager.frame_buffer.clear()
        self.sidebar.clear_alerts()
        self.sidebar.set_prediction("ANALIZANDO...", 0)
        self.sidebar.update_statistics(self.session_stats.as_dict())

        self.status_badge.setText("ANALISIS ACTIVO")
        self.status_badge.setStyleSheet(
            "color: #00d4ff; font-size: 11px; font-weight: bold; "
            "padding: 4px 12px; background-color: #141c2e; "
            "border: 1px solid #00d4ff; border-radius: 4px;"
        )
        self.sidebar.set_system_status("ANALISIS ACTIVO", active=True)
        self.sidebar.set_movement_intensity(0)
        self.sidebar.log_activity("Flujo optico Farneback activado.", "OK")
        if self.predictor.is_ready:
            self.sidebar.log_activity("Modelo ML activo para prediccion.", "OK")
        self._update_control_state()

    def _on_stop_analysis(self) -> None:
        self.video_player.pause()
        if self.webcam.is_active:
            self.webcam.stop()

        self._monitoring_active = False
        self._last_flow_result = None
        self.motion_analyzer.reset()
        self.status_badge.setText("EN LINEA")
        self.status_badge.setStyleSheet("")
        self.sidebar.set_system_status("EN LINEA", active=False)
        self.sidebar.log_activity("Analisis detenido por el operador.", "WARN")
        self.sidebar.set_movement_intensity(0)
        self.sidebar.set_risk_level("BAJO")
        if not self.predictor.is_ready:
            self.sidebar.set_prediction("SIN MODELO", 0)
        self._update_control_state()

    def _auto_load_model(self) -> None:
        ok, msg = self.model_trainer.load_latest()
        if ok:
            self.sidebar.log_activity(msg, "OK")
            acc = self.model_trainer.metrics.get("accuracy", 0)
            self.sidebar.set_prediction("MODELO LISTO", acc if acc else 100)
        else:
            self.sidebar.log_activity(
                "Sin modelo cargado. Use Modelo > Entrenar o Cargar.", "INFO"
            )
        self._update_train_mode()

    def _update_train_mode(self) -> None:
        self.control_bar.set_train_mode(self.model_trainer.is_loaded)
        if self.model_trainer.is_loaded:
            pending = self.model_trainer.count_pending_samples(self.dataset_manager)
            if pending:
                self.sidebar.log_activity(
                    f"{pending} muestra(s) nueva(s) lista(s) para ampliar el modelo.", "INFO"
                )

    def _on_section_changed(self, index: int) -> None:
        self.section_stack.setCurrentIndex(index)
        if index == 1:
            self.evidence_panel.refresh()
        else:
            self.evidence_panel.stop_all_media()

    def _on_incident_jump_to_video(self, seconds: float) -> None:
        if self._source_mode != "file" or not self._video_path:
            return
        self.nav_bar.select_monitor()
        self.section_stack.setCurrentIndex(0)
        self._on_timeline_seek(seconds)
        self.sidebar.log_activity(
            f"Salto a incidente en {self.timeline_bar._format_time(seconds)}", "INFO"
        )

    def _register_incident(
        self,
        event_type: str,
        confidence: float = 0.0,
        file_path: str = "",
        file_type: str = "",
    ) -> None:
        self.incident_history.add_event(
            event_type=event_type,
            confidence=confidence,
            file_path=file_path,
            file_type=file_type,
            video_time_sec=self._current_time_sec(),
        )

    def _on_frame_ready(self, frame) -> None:
        if frame is None or not getattr(frame, "size", 0):
            return

        needs_control_update = self._last_frame is None
        self._last_frame = frame
        display_frame = frame

        if self._monitoring_active:
            if self._frame_counter % EVIDENCE_FRAME_INTERVAL == 0:
                self.evidence_manager.push_frame(frame)

            run_analysis = self._frame_counter % ANALYSIS_FRAME_INTERVAL == 0
            if run_analysis:
                result = self.motion_analyzer.process(frame, draw_overlay=True)
                self._last_flow_result = result
                display_frame = result.annotated_frame
            elif self._last_flow_result is not None:
                result = self._last_flow_result
                display_frame = frame
            else:
                result = self.motion_analyzer.process(frame, draw_overlay=True)
                self._last_flow_result = result
                display_frame = result.annotated_frame

            self._last_features = result
            self._frame_counter += 1

            interval = 1.0 / max(self.video_player.fps if self._source_mode == "file" else 30, 1)
            self.session_stats.add_time(interval)
            self.session_stats.add_risk_sample(result.intensidad_movimiento)

            if self._frame_counter % DATASET_AUTO_INTERVAL == 0:
                self.dataset_manager.append_auto(result)

            update_ui = self._frame_counter % UI_UPDATE_INTERVAL == 0
            if update_ui:
                self._update_motion_metrics(result)
                self._update_ml_analysis(result, display_frame)
                self.sidebar.update_statistics(self.session_stats.as_dict())

        if self._source_mode == "file":
            label = (
                f"ANALISIS — {os.path.basename(self._video_path)}"
                if self._monitoring_active
                else f"REPRODUCCION — {os.path.basename(self._video_path)}"
            )
        elif self._source_mode == "webcam":
            label = (
                "ANALISIS EN VIVO — WEBCAM"
                if self._monitoring_active
                else "WEBCAM — TRANSMISION EN VIVO"
            )
        else:
            label = "MONITOREO"

        self.video_panel.show_frame(display_frame, label)

        if needs_control_update:
            self._update_control_state()

    def _update_ml_analysis(self, result, frame) -> None:
        prediction_label = ""
        confidence = 0.0

        if self.predictor.is_ready:
            pred = self.predictor.predict(result)
            if pred:
                prediction_label = pred.label
                confidence = pred.confidence
                self.sidebar.set_prediction(pred.label, pred.confidence)

                if pred.is_suspicious:
                    self.sound_alerts.play_if_suspicious(pred.confidence, True)
                    now = time.time()
                    if now - self._last_suspicious_log_time >= SUSPICIOUS_LOG_COOLDOWN_SEC:
                        self.session_stats.add_suspicious()
                        self.sidebar.log_activity(
                            f"Comportamiento sospechoso — Confianza: {pred.confidence}%", "WARN"
                        )
                        self._register_incident(
                            "Comportamiento sospechoso",
                            confidence=pred.confidence,
                        )
                        self._last_suspicious_log_time = now
        else:
            self.sidebar.set_prediction("SIN MODELO", 0)

        current_sec = self._current_time_sec()
        segment = self.segment_tracker.add_segment(
            current_sec,
            result.nivel_riesgo,
            prediction_label,
            confidence,
        )
        if segment and self._source_mode == "file":
            self.timeline_bar.set_segments(self.segment_tracker.segments)

        if self.predictor.is_ready and confidence >= 85:
            path = self.evidence_manager.try_screenshot(frame, confidence)
            if path:
                self.session_stats.add_capture()
                self.sidebar.log_activity(f"Captura guardada: {os.path.basename(path)}", "OK")
                self._register_incident(
                    "Captura sospechosa",
                    confidence=confidence,
                    file_path=path,
                    file_type="screenshot",
                )

        fps = self.video_player.fps if self._source_mode == "file" else 30
        if self.evidence_manager.should_start_clip(confidence):
            self.evidence_manager.start_clip_collection(fps)

        clip_path = self.evidence_manager.try_finish_clip(fps)
        if clip_path:
            self.session_stats.add_clip()
            self.sidebar.log_activity(f"Clip guardado: {os.path.basename(clip_path)}", "OK")
            self._register_incident(
                "Clip sospechoso",
                confidence=confidence,
                file_path=clip_path,
                file_type="clip",
            )

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
        alert_msg = log_msg = None

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
            self.session_stats.add_alert()
            self._last_alert_time = now
            event_type = "Riesgo alto" if intensity >= ALERT_INTENSE_MIN else "Movimiento inusual"
            self._register_incident(
                event_type,
                confidence=float(intensity),
            )
            if self.sidebar.alerts_list.count() > ALERT_MAX_ITEMS:
                self.sidebar.alerts_list.takeItem(self.sidebar.alerts_list.count() - 1)

    def _features_for_labeling(self):
        """Obtiene características del frame actual (monitoreo o video pausado)."""
        if self._last_features is not None:
            return self._last_features
        if self._last_frame is not None and self._source_mode is not None:
            return self.motion_analyzer.process(self._last_frame, draw_overlay=False)
        return None

    def _on_manual_label(self, etiqueta: str) -> None:
        features = self._features_for_labeling()
        if features is None:
            QMessageBox.warning(
                self, "Sin datos",
                "Cargue un video o active la webcam y seleccione un frame antes de etiquetar.",
            )
            return
        self.dataset_manager.append_manual(features, etiqueta)
        self.sidebar.set_movement_intensity(features.intensidad_movimiento)
        self.sidebar.set_risk_level(features.nivel_riesgo)
        self.sidebar.log_activity(f"Muestra guardada como '{etiqueta}' en dataset.csv", "OK")
        counts = self.dataset_manager.count_samples()
        self.sidebar.log_activity(
            f"Dataset: {counts['total']} muestras ({counts['normal']} normal, {counts['sospechoso']} sospechoso)",
            "INFO",
        )
        if self.model_trainer.is_loaded:
            pending = self.model_trainer.count_pending_samples(self.dataset_manager)
            self.sidebar.log_activity(
                f"Puede ampliar el modelo con esta muestra ({pending} nueva(s) pendiente(s)).",
                "INFO",
            )

    def _on_train_model(self) -> None:
        continue_learning = self.model_trainer.is_loaded

        was_playing = self.video_player.is_playing
        self.video_player.pause()

        ok, msg = self.model_trainer.train(
            self.dataset_manager,
            continue_from_loaded=continue_learning,
        )
        if ok:
            QMessageBox.information(
                self,
                "Ampliar modelo" if continue_learning else "Entrenamiento",
                msg,
            )
            self.sidebar.log_activity(msg, "OK")
            acc = self.model_trainer.metrics.get("accuracy", 100)
            self.sidebar.set_prediction("MODELO LISTO", acc)
            self._update_train_mode()
        else:
            QMessageBox.warning(
                self,
                "Ampliar modelo" if continue_learning else "Entrenamiento",
                msg,
            )
            self.sidebar.log_activity(msg, "ERROR")

        if was_playing and self._monitoring_active:
            self.video_player.play()

    def _on_save_model(self) -> None:
        was_playing = self.video_player.is_playing
        self.video_player.pause()

        name, ok = QInputDialog.getText(
            self, "Guardar modelo", "Nombre del archivo:", text="modelo_v1.pkl",
        )
        if not ok or not name.strip():
            if was_playing and self._monitoring_active:
                self.video_player.play()
            return
        if not name.endswith(".pkl"):
            name += ".pkl"
        success, msg = self.model_trainer.save(name)
        if success:
            QMessageBox.information(self, "Modelo", msg)
            self.sidebar.log_activity(msg, "OK")
            self._update_train_mode()
        else:
            QMessageBox.warning(self, "Modelo", msg)

        if was_playing and self._monitoring_active:
            self.video_player.play()

    def _on_load_model(self) -> None:
        was_playing = self.video_player.is_playing
        self.video_player.pause()

        path, _ = QFileDialog.getOpenFileName(
            self, "Cargar modelo", str(MODELS_DIR), "Modelos (*.pkl)",
        )
        if not path:
            if was_playing and self._monitoring_active:
                self.video_player.play()
            return
        success, msg = self.model_trainer.load(path)
        if success:
            QMessageBox.information(self, "Modelo", msg)
            self.sidebar.log_activity(msg, "OK")
            acc = self.model_trainer.metrics.get("accuracy", 100)
            self.sidebar.set_prediction("MODELO CARGADO", acc)
            self._update_train_mode()
        else:
            QMessageBox.warning(self, "Modelo", msg)
            self.sidebar.log_activity(msg, "ERROR")

        if was_playing and self._monitoring_active:
            self.video_player.play()

    def _on_import_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar modelo", "", "Modelos (*.pkl)",
        )
        if not path:
            return
        success, msg = self.model_trainer.import_model(path)
        if success:
            QMessageBox.information(self, "Modelo", msg)
            self.sidebar.log_activity(msg, "OK")
            acc = self.model_trainer.metrics.get("accuracy", 100)
            self.sidebar.set_prediction("MODELO CARGADO", acc)
            self._update_train_mode()
        else:
            QMessageBox.warning(self, "Modelo", msg)
            self.sidebar.log_activity(msg, "ERROR")

    def _on_export_model(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar modelo", "modelo_examen_final.pkl", "Modelos (*.pkl)",
        )
        if not path:
            return
        success, msg = self.model_trainer.export_model(path)
        if success:
            QMessageBox.information(self, "Modelo", msg)
            self.sidebar.log_activity(msg, "OK")
        else:
            QMessageBox.warning(self, "Modelo", msg)

    def _on_position_changed(self, current: float, total: float) -> None:
        if self._source_mode == "file":
            self.timeline_bar.set_position(current)
            if total > 0:
                self.timeline_bar.set_duration(total)

    def _on_timeline_seek(self, seconds: float) -> None:
        if self._source_mode == "file" and self._video_path:
            was_playing = self.video_player.is_playing
            self.video_player.seek_seconds(seconds)
            if was_playing:
                self.video_player.play()

    def _on_marker_clicked(self, seconds: float) -> None:
        self._on_timeline_seek(seconds)
        self.sidebar.log_activity(
            f"Navegacion a evento: {self.timeline_bar._format_time(seconds)}", "INFO"
        )

    def _on_playback_finished(self) -> None:
        self.sidebar.log_activity("Reproduccion de video finalizada.", "INFO")
        self._monitoring_active = False
        self._last_flow_result = None
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
        self._last_frame = None
        self._last_flow_result = None
        self.motion_analyzer.reset()
        self.segment_tracker.reset()
        self.timeline_bar.reset()
        if not keep_ui:
            self.video_panel.clear_display()
            self.control_bar.btn_webcam.setText("Activar Webcam")
        self._update_control_state()

    def _update_control_state(self) -> None:
        has_source = self._source_mode is not None or self.webcam.is_active
        self.control_bar.btn_start.setEnabled(has_source and not self._monitoring_active)
        self.control_bar.btn_stop.setEnabled(self._monitoring_active)
        self.control_bar.btn_import.setEnabled(not self.webcam.is_active)
        can_label = has_source and self._last_frame is not None
        self.control_bar.set_labeling_available(can_label)

    def closeEvent(self, event) -> None:
        self.evidence_panel.stop_all_media()
        self.video_player.stop()
        self.webcam.stop()
        self._last_flow_result = None
        self.motion_analyzer.reset()
        event.accept()
