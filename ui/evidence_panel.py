"""Centro de evidencias: capturas, clips e historial de incidentes."""

import os

import cv2
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ml.evidence_catalog import EvidenceCatalog, EvidenceItem
from ml.incident_history import IncidentRecord
from ui.timeline_bar import TimelineBar
from utils.constants import (
    SORT_CONFIDENCE_DESC,
    SORT_DATE_ASC,
    SORT_DATE_DESC,
    SORT_RISK_DESC,
)
from video.frame_utils import frame_to_pixmap


class ClipViewer(QWidget):
    """Reproductor embebido de clips con barra de tiempo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._capture = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._path = ""
        self._fps = 30.0
        self._duration = 0.0
        self._display_w = 640
        self._display_h = 360
        self._playing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.display = QLabel("Seleccione un clip para reproducir")
        self.display.setObjectName("evidenceViewer")
        self.display.setAlignment(Qt.AlignCenter)
        self.display.setMinimumSize(640, 360)
        self.display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.display, stretch=1)

        self.timeline = TimelineBar()
        self.timeline.setEnabled(False)
        self.timeline.seek_requested.connect(self.seek_seconds)
        layout.addWidget(self.timeline)

        controls = QHBoxLayout()
        self.btn_play = QPushButton("Reproducir")
        self.btn_play.setObjectName("btnEvidencePlay")
        self.btn_pause = QPushButton("Pausar")
        self.btn_pause.setObjectName("btnEvidencePause")
        self.btn_stop = QPushButton("Detener")
        self.btn_stop.setObjectName("btnEvidenceStop")
        self.btn_play.clicked.connect(self.play)
        self.btn_pause.clicked.connect(self.pause)
        self.btn_stop.clicked.connect(self.stop)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.btn_pause)
        controls.addWidget(self.btn_stop)
        controls.addStretch()
        layout.addLayout(controls)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w = max(self.display.width(), 640)
        h = max(self.display.height(), 360)
        if abs(w - self._display_w) > 8 or abs(h - self._display_h) > 8:
            self._display_w = w
            self._display_h = h

    def load(self, path: str) -> None:
        self.stop()
        self._path = path
        self._release_capture()

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            self.display.setText("No se pudo abrir el clip")
            self.timeline.setEnabled(False)
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        self._fps = fps if fps and fps > 0 else 30.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._duration = total / self._fps if self._fps else 0.0
        self.timeline.set_duration(self._duration)
        self.timeline.set_position(0)
        self.timeline.setEnabled(True)

        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None:
            self._show_frame(frame)
        else:
            self.display.setText(f"Clip: {os.path.basename(path)}")

    def play(self) -> None:
        if not self._path:
            return
        if self._capture is None:
            self._capture = cv2.VideoCapture(self._path)
        if not self._capture.isOpened():
            self.display.setText("No se pudo abrir el clip")
            return
        self._playing = True
        self._timer.start(max(1, int(1000 / self._fps)))

    def pause(self) -> None:
        self._playing = False
        self._timer.stop()

    def stop(self) -> None:
        self._playing = False
        self._timer.stop()
        self._release_capture()
        if self._path:
            self.timeline.set_position(0)
            cap = cv2.VideoCapture(self._path)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    self._show_frame(frame)
                cap.release()

    def seek_seconds(self, seconds: float) -> None:
        if not self._path:
            return
        was_playing = self._playing
        self.pause()
        if self._capture is None:
            self._capture = cv2.VideoCapture(self._path)
        if not self._capture.isOpened():
            return

        seconds = max(0.0, min(seconds, self._duration))
        frame_idx = int(seconds * self._fps)
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self._capture.read()
        if ret and frame is not None:
            self._show_frame(frame)
            self.timeline.set_position(seconds)
        if was_playing:
            self.play()

    def _next_frame(self) -> None:
        if self._capture is None:
            return
        ret, frame = self._capture.read()
        if not ret:
            self.pause()
            return
        self._show_frame(frame)
        current = self._capture.get(cv2.CAP_PROP_POS_FRAMES) / self._fps
        self.timeline.set_position(current)

    def _show_frame(self, frame) -> None:
        pixmap = frame_to_pixmap(frame, self._display_w, self._display_h, fast=True)
        if not pixmap.isNull():
            self.display.setPixmap(pixmap)
            self.display.setText("")

    def _release_capture(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def clear(self) -> None:
        self.stop()
        self._path = ""
        self._duration = 0.0
        self.timeline.reset()
        self.display.setPixmap(QPixmap())
        self.display.setText("Seleccione un clip para reproducir")


class EvidencePanel(QWidget):
    """Sección Evidencias con capturas, clips e incidentes."""

    jump_to_video_time = pyqtSignal(float)

    def __init__(self, catalog: EvidenceCatalog, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.setObjectName("evidencePanel")
        self._screenshots: list[EvidenceItem] = []
        self._clips: list[EvidenceItem] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 8, 16)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Ordenar:"))
        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("evidenceSortCombo")
        self.sort_combo.addItem("Fecha (reciente)", SORT_DATE_DESC)
        self.sort_combo.addItem("Fecha (antigua)", SORT_DATE_ASC)
        self.sort_combo.addItem("Sospechoso (alto primero)", SORT_RISK_DESC)
        self.sort_combo.addItem("Confianza (alta primero)", SORT_CONFIDENCE_DESC)
        self.sort_combo.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.sort_combo)
        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.setObjectName("btnEvidenceRefresh")
        self.btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("evidenceTabs")

        self.tab_screenshots = self._create_media_tab(is_clip=False)
        self.tab_clips = self._create_media_tab(is_clip=True)
        self.tab_incidents = self._create_incidents_tab()

        self.tabs.addTab(self.tab_screenshots["widget"], "Capturas")
        self.tabs.addTab(self.tab_clips["widget"], "Clips")
        self.tabs.addTab(self.tab_incidents, "Incidentes")
        layout.addWidget(self.tabs, stretch=1)

    def _create_media_tab(self, is_clip: bool) -> dict:
        container = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        item_list = QListWidget()
        item_list.setObjectName("evidenceList")
        item_list.setIconSize(QSize(96, 54))
        item_list.setMinimumWidth(220)
        item_list.setMaximumWidth(300)
        item_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        viewer = QLabel("Seleccione un elemento de la lista")
        viewer.setObjectName("evidenceViewer")
        viewer.setAlignment(Qt.AlignCenter)
        viewer.setMinimumSize(640, 360)
        viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        clip_viewer = ClipViewer() if is_clip else None
        right = clip_viewer if is_clip else viewer

        splitter.addWidget(item_list)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 740])

        tab_layout = QVBoxLayout(container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(splitter)

        item_list.currentItemChanged.connect(
            lambda cur, _prev: self._on_media_selected(cur, right, is_clip)
        )

        return {
            "widget": container,
            "list": item_list,
            "viewer": viewer,
            "clip_viewer": clip_viewer,
            "splitter": splitter,
        }

    def _create_incidents_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.incident_list = QListWidget()
        self.incident_list.setObjectName("incidentList")
        self.incident_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.incident_list.currentItemChanged.connect(self._on_incident_selected)
        layout.addWidget(self.incident_list, stretch=2)

        self.incident_detail = QLabel("Seleccione un incidente")
        self.incident_detail.setObjectName("incidentDetail")
        self.incident_detail.setWordWrap(True)
        self.incident_detail.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.incident_detail.setMinimumHeight(80)
        layout.addWidget(self.incident_detail, stretch=0)

        return container

    def show_tab(self, index: int) -> None:
        if 0 <= index < self.tabs.count():
            self.tabs.setCurrentIndex(index)

    def refresh(self) -> None:
        sort_key = self.sort_combo.currentData()
        self._screenshots = self.catalog.sort_items(
            self.catalog.get_screenshots(), sort_key
        )
        self._clips = self.catalog.sort_items(self.catalog.get_clips(), sort_key)
        incidents = self.catalog.get_incidents(sort_key)

        self._populate_media_list(self.tab_screenshots["list"], self._screenshots)
        self._populate_media_list(self.tab_clips["list"], self._clips)
        self._populate_incidents(incidents)

    def _populate_media_list(self, list_widget: QListWidget, items: list[EvidenceItem]) -> None:
        list_widget.blockSignals(True)
        list_widget.clear()
        for item in items:
            text = (
                f"{item.date} {item.time}\n"
                f"{item.event_type}\n"
                f"Conf: {item.confidence:.0f}% | Sospechoso: {item.suspicious_label}"
            )
            lw_item = QListWidgetItem(text)
            lw_item.setData(Qt.UserRole, str(item.path))
            lw_item.setData(Qt.UserRole + 1, item.kind)

            if item.kind == "screenshot" and item.path.exists():
                pixmap = QPixmap(str(item.path))
                if not pixmap.isNull():
                    icon = QIcon(pixmap.scaled(96, 54, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    lw_item.setIcon(icon)
            list_widget.addItem(lw_item)

        if list_widget.count() == 0:
            placeholder = QListWidgetItem("Sin evidencias en esta categoría")
            placeholder.setFlags(Qt.NoItemFlags)
            list_widget.addItem(placeholder)
        list_widget.blockSignals(False)

    def _populate_incidents(self, incidents: list[IncidentRecord]) -> None:
        self.incident_list.blockSignals(True)
        self.incident_list.clear()
        for inc in incidents:
            text = (
                f"{inc.time_display} — {inc.event_type}\n"
                f"Confianza: {inc.confidence:.0f}% | Sospechoso: {inc.suspicious_label}"
            )
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, inc)
            self.incident_list.addItem(item)
        if self.incident_list.count() == 0:
            placeholder = QListWidgetItem("Sin incidentes registrados")
            placeholder.setFlags(Qt.NoItemFlags)
            self.incident_list.addItem(placeholder)
        self.incident_list.blockSignals(False)

    def _on_media_selected(self, current: QListWidgetItem, viewer, is_clip: bool) -> None:
        if current is None or not current.data(Qt.UserRole):
            return
        path = current.data(Qt.UserRole)
        if not os.path.isfile(path):
            return

        if is_clip and isinstance(viewer, ClipViewer):
            viewer.load(path)
        elif isinstance(viewer, QLabel):
            pixmap = QPixmap(path)
            if pixmap.isNull():
                viewer.setText("No se pudo cargar la imagen")
                return
            w = max(viewer.width(), 640)
            h = max(viewer.height(), 360)
            viewer.setPixmap(
                pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            viewer.setText("")

    def _on_incident_selected(self, current: QListWidgetItem, _prev) -> None:
        if current is None:
            return
        inc = current.data(Qt.UserRole)
        if not isinstance(inc, IncidentRecord):
            self.incident_detail.setText(str(current.text()))
            return

        detail = (
            f"<b>{inc.time_display} — {inc.event_type}</b><br>"
            f"Fecha: {inc.datetime}<br>"
            f"Confianza: {inc.confidence:.1f}%<br>"
            f"Sospechoso: {inc.suspicious_label}<br>"
            f"Tipo: {inc.event_type}<br>"
        )
        if inc.file_path:
            detail += f"Archivo: {os.path.basename(inc.file_path)}<br>"
        if inc.video_time_sec > 0:
            detail += f"Posición en video: {inc.video_time_sec:.1f} s"
        self.incident_detail.setText(detail)

        if inc.video_time_sec > 0:
            self.jump_to_video_time.emit(inc.video_time_sec)

    def stop_all_media(self) -> None:
        clip_viewer = self.tab_clips.get("clip_viewer")
        if clip_viewer:
            clip_viewer.pause()
