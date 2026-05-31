"""Constantes globales de la aplicación."""

APP_NAME = "Sistema Inteligente de Detección y Análisis de Comportamientos Sospechosos"
APP_VERSION = "2.0.0-sprint2"
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

DEFAULT_FPS = 30
WEBCAM_INDEX = 0

# Flujo óptico Farneback (Sprint 2)
FLOW_PROCESS_WIDTH = 640
FLOW_PROCESS_HEIGHT = 360
FLOW_GRID_STEP = 16
FLOW_MIN_MAGNITUDE = 0.4
FLOW_MAGNITUDE_SCALE = 12.0
FLOW_SMOOTH_ALPHA = 0.35

# Nivel de riesgo según intensidad (0-100)
RISK_MEDIUM_MIN = 26
RISK_HIGH_MIN = 56

# Alertas automáticas
ALERT_MOTION_MIN = 15
ALERT_ELEVATED_MIN = 26
ALERT_INTENSE_MIN = 56
ALERT_COOLDOWN_SEC = 4.0
ALERT_MAX_ITEMS = 50

