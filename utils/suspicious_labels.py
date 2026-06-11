"""Etiquetas de sospecha basadas en confianza del modelo."""

SUSPICIOUS_MIN_CONF = 40.0
SUSPICIOUS_HIGH_CONF = 85.0

LABEL_NORMAL = "NORMAL"
LABEL_SOSPECHOSO = "SOSPECHOSO"
LABEL_SOSPECHOSO_ALTO = "SOSPECHOSO ALTO"

SUSPICIOUS_SORT_ORDER = {
    LABEL_SOSPECHOSO_ALTO: 4,
    LABEL_SOSPECHOSO: 3,
    "ALTO": 3,
    "MEDIO": 2,
    "BAJO": 1,
    LABEL_NORMAL: 0,
    "": 0,
}


def suspicious_label_from_confidence(confidence: float) -> str:
    """Deriva etiqueta legible para el usuario según confianza ML."""
    conf = float(confidence)
    if conf >= SUSPICIOUS_HIGH_CONF:
        return LABEL_SOSPECHOSO_ALTO
    if conf > SUSPICIOUS_MIN_CONF:
        return LABEL_SOSPECHOSO
    return LABEL_NORMAL


def format_suspicious_display(confidence: float, stored: str = "") -> str:
    """Muestra sospecha segun confianza; corrige registros viejos con BAJO + alta confianza."""
    label = suspicious_label_from_confidence(confidence)
    if label != LABEL_NORMAL:
        return label
    upper = (stored or "").upper()
    if upper in (LABEL_SOSPECHOSO, LABEL_SOSPECHOSO_ALTO):
        return upper
    if upper in ("ALTO", "MEDIO"):
        return LABEL_SOSPECHOSO if upper == "MEDIO" else LABEL_SOSPECHOSO_ALTO
    return LABEL_NORMAL
