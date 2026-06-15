"""Monitor de rendimiento: CPU, RAM y tiempo por frame."""

import time

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class PerformanceMonitor:
    """Muestrea recursos del proceso y latencia de procesamiento."""

    MAX_SAMPLES = 120

    def __init__(self) -> None:
        self._frame_times_ms: list[float] = []
        self._cpu_samples: list[float] = []
        self._ram_samples_mb: list[float] = []
        self._frame_start = 0.0
        self._process = psutil.Process() if HAS_PSUTIL else None
        if self._process is not None:
            self._process.cpu_percent()

    def mark_frame_start(self) -> None:
        self._frame_start = time.perf_counter()

    def mark_frame_end(self) -> None:
        if self._frame_start <= 0:
            return
        elapsed_ms = (time.perf_counter() - self._frame_start) * 1000.0
        self._append(self._frame_times_ms, elapsed_ms)
        if self._process is not None:
            self._append(self._cpu_samples, float(self._process.cpu_percent()))
            ram_mb = self._process.memory_info().rss / (1024 * 1024)
            self._append(self._ram_samples_mb, ram_mb)
        self._frame_start = 0.0

    @staticmethod
    def _append(bucket: list, value: float) -> None:
        bucket.append(value)
        if len(bucket) > PerformanceMonitor.MAX_SAMPLES:
            del bucket[0]

    @staticmethod
    def _avg(values: list[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)

    @property
    def avg_frame_ms(self) -> float:
        return self._avg(self._frame_times_ms)

    @property
    def avg_cpu(self) -> float:
        return self._avg(self._cpu_samples)

    @property
    def avg_ram_mb(self) -> float:
        return self._avg(self._ram_samples_mb)

    def as_dict(self) -> dict:
        from utils.constants import TARGET_FPS
        target_ms = 1000.0 / TARGET_FPS
        frame_budget_pct = round(min(self.avg_frame_ms / target_ms * 100, 999), 1) if target_ms else 0
        ram_usage_pct = 0.0
        if self.avg_ram_mb > 0:
            ram_usage_pct = round(min(self.avg_ram_mb / 4096 * 100, 100), 1)
        return {
            "avg_frame_ms": self.avg_frame_ms,
            "avg_cpu": self.avg_cpu,
            "avg_ram_mb": self.avg_ram_mb,
            "frame_budget_pct": frame_budget_pct,
            "ram_usage_pct": ram_usage_pct,
            "samples": len(self._frame_times_ms),
            "psutil_available": HAS_PSUTIL,
        }

    def reset(self) -> None:
        self._frame_times_ms.clear()
        self._cpu_samples.clear()
        self._ram_samples_mb.clear()
        self._frame_start = 0.0
