"""Captura automática de evidencia: screenshots y clips."""

import time
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from utils.constants import (
    CLIP_AFTER_SEC,
    CLIP_BEFORE_SEC,
    EVIDENCE_CLIPS_DIR,
    EVIDENCE_SCREENSHOTS_DIR,
    EVIDENCE_SCREENSHOT_CONF,
    EVIDENCE_CLIP_CONF,
)


class FrameRingBuffer:
    """Buffer circular de frames para clips de evidencia."""

    def __init__(self, max_seconds: float = 6.0, fps: float = 30.0):
        self._maxlen = max(1, int(max_seconds * fps))
        self._buffer: deque = deque(maxlen=self._maxlen)
        self._fps = fps

    def set_fps(self, fps: float) -> None:
        self._fps = fps if fps > 0 else 30.0
        self._maxlen = max(1, int((CLIP_BEFORE_SEC + 1) * self._fps))
        old = list(self._buffer)
        self._buffer = deque(old[-self._maxlen:], maxlen=self._maxlen)

    def append(self, frame: np.ndarray) -> None:
        self._buffer.append(frame.copy())

    def get_before_frames(self) -> list:
        before_count = int(CLIP_BEFORE_SEC * self._fps)
        frames = list(self._buffer)
        return frames[-before_count:] if before_count < len(frames) else frames

    def clear(self) -> None:
        self._buffer.clear()


class EvidenceManager:
    """Guarda capturas PNG y clips MP4 en evidence/screenshots y evidence/clips."""

    def __init__(self):
        self.screenshots_dir = Path(EVIDENCE_SCREENSHOTS_DIR)
        self.clips_dir = Path(EVIDENCE_CLIPS_DIR)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        self.frame_buffer = FrameRingBuffer()
        self._clip_collecting = False
        self._clip_frames: list = []
        self._clip_target = 0
        self._last_screenshot = 0.0
        self._screenshot_cooldown = 3.0

    def push_frame(self, frame: np.ndarray) -> None:
        self.frame_buffer.append(frame)
        if self._clip_collecting and len(self._clip_frames) < self._clip_target:
            self._clip_frames.append(frame.copy())

    def try_screenshot(self, frame: np.ndarray, confidence: float) -> str | None:
        if confidence < EVIDENCE_SCREENSHOT_CONF:
            return None

        now = time.time()
        if now - self._last_screenshot < self._screenshot_cooldown:
            return None

        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".png"
        path = self.screenshots_dir / filename
        cv2.imwrite(str(path), frame)
        self._last_screenshot = now
        return str(path)

    def start_clip_collection(self, fps: float) -> None:
        self._clip_collecting = True
        self._clip_frames = self.frame_buffer.get_before_frames()
        self._clip_target = len(self._clip_frames) + int(CLIP_AFTER_SEC * fps)
        self.frame_buffer.set_fps(fps)

    def try_finish_clip(self, fps: float) -> str | None:
        if not self._clip_collecting:
            return None
        if len(self._clip_frames) < self._clip_target:
            return None

        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".mp4"
        path = self.clips_dir / filename
        if not self._clip_frames:
            self._clip_collecting = False
            return None

        h, w = self._clip_frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(path), fourcc, fps, (w, h))
        for f in self._clip_frames:
            writer.write(f)
        writer.release()

        self._clip_collecting = False
        self._clip_frames.clear()
        return str(path)

    def should_start_clip(self, confidence: float) -> bool:
        return confidence >= EVIDENCE_CLIP_CONF and not self._clip_collecting
