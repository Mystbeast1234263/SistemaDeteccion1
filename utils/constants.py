"""Constantes globales de la aplicación."""

APP_NAME = "Sistema Inteligente de Detección y Análisis de Comportamientos Sospechosos"
APP_VERSION = "5.0.0-sprint5"
APP_SHORT_NAME = "SIDACS"

COLORS = {
    "bg_dark": "#0a0e17",
    "bg_panel": "#0f1624",
    "bg_card": "#141c2e",
    "border": "#1e3a5f",
    "neon_blue": "#00d4ff",
    "neon_blue_dim": "#0099cc",
    "neon_red": "#ff3366",
    "neon_red_dim": "#cc2952",
    "text_primary": "#e8f4ff",
    "text_secondary": "#7a9bb8",
    "text_muted": "#4a6278",
    "success": "#00ff88",
    "warning": "#ffaa00",
    "danger": "#ff3366",
}

VIDEO_EXTENSIONS = (
    "Archivos de video (*.mp4 *.avi *.mkv *.mov *.wmv);;"
    "Todos los archivos (*.*)"
)

DEFAULT_FPS = 60
TARGET_FPS = 60
PLAYBACK_DISPLAY_FPS = 60
WEBCAM_INDEX = 0

# Flujo óptico Farneback (Sprint 2)
FLOW_PROCESS_WIDTH = 640
FLOW_PROCESS_HEIGHT = 360
FLOW_GRID_STEP = 16
FLOW_GRID_STEP_HD = 24
FLOW_MIN_MAGNITUDE = 0.4
FLOW_MAGNITUDE_SCALE = 12.0
FLOW_SMOOTH_ALPHA = 0.35

# Nivel de riesgo según intensidad (0-100)
RISK_MEDIUM_MIN = 26
RISK_HIGH_MIN = 56

# Alertas automáticas
ALERT_MOTION_MIN = 18
ALERT_ELEVATED_MIN = 28
ALERT_INTENSE_MIN = 58
ALERT_COOLDOWN_SEC = 4.0
ALERT_MAX_ITEMS = 50

# Sprint 3 — Machine Learning y evidencia
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
MODELS_DIR = ROOT_DIR / "models"
EVIDENCE_DIR = ROOT_DIR / "evidence"
EVIDENCE_SCREENSHOTS_DIR = EVIDENCE_DIR / "screenshots"
EVIDENCE_CLIPS_DIR = EVIDENCE_DIR / "clips"
INCIDENTS_PATH = EVIDENCE_DIR / "incidents.json"
DATASET_PATH = DATASET_DIR / "dataset.csv"

DATASET_COLUMNS = [
    "timestamp",
    "intensidad_movimiento",
    "magnitud_promedio",
    "direccion_promedio",
    "cantidad_movimiento",
    "nivel_riesgo",
    "etiqueta",
]

LABEL_NORMAL = "normal"
LABEL_SOSPECHOSO = "sospechoso"

RISK_ENCODING = {"BAJO": 0, "MEDIO": 1, "ALTO": 2}

DATASET_AUTO_INTERVAL = 30
EVIDENCE_SCREENSHOT_CONF = 85.0
EVIDENCE_CLIP_CONF = 90.0
CLIP_BEFORE_SEC = 5.0
CLIP_AFTER_SEC = 5.0

# Rendimiento — video y UI (Sprint 5 fluidez)
UI_UPDATE_INTERVAL = 8
ANALYSIS_FRAME_INTERVAL = 4
ANALYSIS_FRAME_INTERVAL_HD = 6
ANALYSIS_FRAME_INTERVAL_2K = 8
HR_VIDEO_HEIGHT_THRESHOLD = 1080
UHD_VIDEO_HEIGHT_THRESHOLD = 1440
PLAYBACK_FRAME_INTERVAL = 1
EVIDENCE_FRAME_INTERVAL = 8
VIDEO_BUFFER_SIZE = 1
SUSPICIOUS_LOG_COOLDOWN_SEC = 5.0
SOUND_ALERT_COOLDOWN_SEC = 4.0

# Visualizacion fluida — 60 FPS, resolucion reducida para mantener ritmo
DISPLAY_MAX_WIDTH = 960
DISPLAY_MAX_HEIGHT = 540
DISPLAY_TARGET_FPS = 60

# Webcam — 60 FPS, resolucion media-baja para fluidez
WEBCAM_CAPTURE_WIDTH = 960
WEBCAM_CAPTURE_HEIGHT = 540
WEBCAM_TARGET_FPS = 60
WEBCAM_DROP_BUFFERS = 1

# Sprint 5 — Flujo óptico adaptativo (alta resolución)
FLOW_PROCESS_WIDTH_HD = 640
FLOW_PROCESS_HEIGHT_HD = 360
FLOW_PROCESS_WIDTH_UHD = 480
FLOW_PROCESS_HEIGHT_UHD = 270
FLOW_OVERLAY_SKIP_UHD = 2

# Sprint 5 — Reducción de falsos positivos
MOTION_DETECT_MIN_INTENSITY = 12
BRIEF_MOTION_MAX_INTENSITY = 24
MOTION_ALERT_SUSTAINED_CYCLES = 3
SUSPICIOUS_CONFIRM_CYCLES = 3
MIN_ML_SUSPICIOUS_CONF = 45.0

# Sprint 5 — Testing y documentación
TESTING_DIR = ROOT_DIR / "testing"
TEST_RESULTS_PATH = TESTING_DIR / "test_results.json"
DOCS_DIR = ROOT_DIR / "docs"
SPRINT5_TESTING_DOC = DOCS_DIR / "sprint5_testing.md"
SPRINT5_OPTIM_DOC = DOCS_DIR / "sprint5_optimizaciones.md"

# Sprint 4 — Alertas sonoras (alineado con sospechoso > 40%)
SOUND_ALERT_STRONG_CONF = 85.0

# Sprint 4 — Timeline
TIMELINE_SKIP_SEC = 10.0

# Sprint 4 — Ordenamiento de incidentes
SORT_DATE_DESC = "date_desc"
SORT_DATE_ASC = "date_asc"
SORT_RISK_DESC = "risk_desc"
SORT_CONFIDENCE_DESC = "confidence_desc"

RISK_SORT_ORDER = {"ALTO": 3, "MEDIO": 2, "BAJO": 1, "": 0}
