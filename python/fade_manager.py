"""
Fade-Away / Vanishing Ink Manager for Phoenix Pen.
Tracks lifecycle of temporary ink strokes and enforces ZERO CPU/GPU usage at rest.
Atlas Standard: < 250 lines.
"""

import time
from typing import Callable, List, Optional
from PyQt6.QtCore import QObject, QTimer


class VanishingStroke:
    """Represents a temporary stroke with automated fade-out interpolation."""

    def __init__(self, stroke_data: dict, duration: float = 2.0, fade_duration: float = 0.6) -> None:
        self.data = stroke_data
        self.duration = duration
        self.fade_duration = fade_duration
        self.created_at = time.time()
        self.alpha_factor = 1.0
        self.is_dead = False

    def update(self, now: float) -> float:
        """Calculates current alpha factor (1.0 -> 0.0). Returns current alpha."""
        elapsed = now - self.created_at
        if elapsed < self.duration:
            self.alpha_factor = 1.0
        else:
            fade_elapsed = elapsed - self.duration
            if fade_elapsed >= self.fade_duration:
                self.alpha_factor = 0.0
                self.is_dead = True
            else:
                # Smooth quadratic ease-out
                t = fade_elapsed / self.fade_duration
                self.alpha_factor = max(0.0, 1.0 - (t * t))
        return self.alpha_factor


class FadeManager(QObject):
    """Manages active vanishing strokes and starts/stops 60 FPS animation timer on-demand."""

    def __init__(self, on_repaint_needed: Callable[[], None], fps: int = 60) -> None:
        super().__init__()
        self._on_repaint = on_repaint_needed
        self.strokes: List[VanishingStroke] = []

        self.timer = QTimer(self)
        interval_ms = max(10, int(1000 / fps))
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self._on_tick)

    def add_stroke(self, stroke_data: dict, duration: float = 2.0, fade_duration: float = 0.6) -> None:
        """Registers a new temporary vanishing stroke and awakens the timer."""
        v_stroke = VanishingStroke(stroke_data, duration, fade_duration)
        self.strokes.append(v_stroke)

        if not self.timer.isActive():
            self.timer.start()

    def clear(self) -> None:
        """Removes all vanishing strokes and shuts down the timer."""
        self.strokes.clear()
        if self.timer.isActive():
            self.timer.stop()
        self._on_repaint()

    def remove_last(self) -> bool:
        """Removes the most recent vanishing stroke."""
        if self.strokes:
            self.strokes.pop()
            if not self.strokes and self.timer.isActive():
                self.timer.stop()
            self._on_repaint()
            return True
        return False

    def is_animating(self) -> bool:
        """Returns True if any stroke is actively fading."""
        return self.timer.isActive()

    def _on_tick(self) -> None:
        """Animation loop tick: updates alphas and shuts down timer if all dead."""
        if not self.strokes:
            self.timer.stop()
            self._on_repaint()
            return

        now = time.time()
        alive_strokes = []

        for stroke in self.strokes:
            stroke.update(now)
            if not stroke.is_dead:
                alive_strokes.append(stroke)

        self.strokes = alive_strokes

        # Trigger redraw
        self._on_repaint()

        # ZERO CPU OPTIMIZATION: Stop timer immediately when empty
        if not self.strokes:
            self.timer.stop()
