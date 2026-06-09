"""Alertas sonoras para detecciones sospechosas."""

import threading

from utils.constants import SOUND_ALERT_MIN_CONF, SOUND_ALERT_STRONG_CONF


class SoundAlertManager:
    """Reproduce pitidos según nivel de confianza (Windows: winsound)."""

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
            pass
        try:
            from PyQt5.QtMultimedia import QSound  # noqa: F401
            return "qsound"
        except ImportError:
            return "none"

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def play_for_confidence(self, confidence: float) -> None:
        if not self.enabled or confidence < SOUND_ALERT_MIN_CONF:
            return

        import time
        now = time.time()
        from utils.constants import SOUND_ALERT_COOLDOWN_SEC
        if now - self._last_play_time < SOUND_ALERT_COOLDOWN_SEC:
            return
        self._last_play_time = now

        if confidence >= SOUND_ALERT_STRONG_CONF:
            self._play_async(self._strong_alert)
        else:
            self._play_async(self._short_beep)

    def _play_async(self, func) -> None:
        threading.Thread(target=func, daemon=True).start()

    def _short_beep(self) -> None:
        if self._backend == "winsound":
            import winsound
            winsound.Beep(880, 180)
        else:
            print("\a", end="", flush=True)

    def _strong_alert(self) -> None:
        if self._backend == "winsound":
            import winsound
            for freq, duration in ((880, 200), (1100, 200), (880, 250)):
                winsound.Beep(freq, duration)
        else:
            for _ in range(3):
                print("\a", end="", flush=True)
