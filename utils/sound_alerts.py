"""Alertas sonoras para detecciones sospechosas."""

import threading
import time

from utils.constants import SOUND_ALERT_COOLDOWN_SEC, SOUND_ALERT_STRONG_CONF
from utils.suspicious_labels import SUSPICIOUS_MIN_CONF


class SoundAlertManager:
    """Reproduce alertas cuando el modelo detecta comportamiento sospechoso."""

    def __init__(self):
        self.enabled = True
        self._last_play_time = 0.0
        self._backend = self._detect_backend()

    @staticmethod
    def _detect_backend() -> str:
        try:
            import winsound  # noqa: F401
            return "winsound"
        except ImportError:
            return "none"

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def play_if_suspicious(self, confidence: float, is_suspicious: bool) -> None:
        """Suena cuando la prediccion es sospechosa o confianza > 40%."""
        if not self.enabled:
            return
        if not is_suspicious and confidence <= SUSPICIOUS_MIN_CONF:
            return

        now = time.time()
        if now - self._last_play_time < SOUND_ALERT_COOLDOWN_SEC:
            return
        self._last_play_time = now

        if confidence >= SOUND_ALERT_STRONG_CONF:
            self._play_async(self._alarm_alert)
        else:
            self._play_async(self._suspicious_alert)

    def _play_async(self, func) -> None:
        threading.Thread(target=func, daemon=True).start()

    def _suspicious_alert(self) -> None:
        """Doble pitido — sospechoso moderado."""
        if self._backend == "winsound":
            import winsound
            try:
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except RuntimeError:
                pass
            time.sleep(0.12)
            winsound.Beep(988, 160)
            time.sleep(0.08)
            winsound.Beep(1175, 200)
        else:
            print("\a\a", end="", flush=True)

    def _alarm_alert(self) -> None:
        """Secuencia intensa — sospechoso confirmado (>= 85%)."""
        if self._backend == "winsound":
            import winsound
            try:
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except RuntimeError:
                pass
            time.sleep(0.15)
            for freq, duration in ((880, 180), (1100, 180), (1320, 220), (1100, 180)):
                winsound.Beep(freq, duration)
                time.sleep(0.05)
        else:
            for _ in range(4):
                print("\a", end="", flush=True)
                time.sleep(0.1)
