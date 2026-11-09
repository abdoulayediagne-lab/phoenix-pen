"""
Transparent Fullscreen Overlay Window for Phoenix Pen.
Handles click-through toggles, mouse stroke capture, eraser, and rendering loop.
Atlas Standard: < 250 lines.
"""

from typing import Any, Dict, List, Optional, Tuple
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QMouseEvent, QPaintEvent, QPainter
from PyQt6.QtWidgets import QWidget

from fade_manager import FadeManager
from neon_renderer import NeonRenderer
from shape_recognizer import ShapeRecognizer

MODE_CLICK_THROUGH = "click_through"
MODE_DRAW_FIXED = "draw_fixed"
MODE_DRAW_VANISHING = "draw_vanishing"
MODE_ERASER = "eraser"

Point = Tuple[float, float]


class OverlayWindow(QWidget):
    """Fullscreen translucent overlay supporting click-through and neon drawing."""

    def __init__(self, config_mgr: Any) -> None:
        super().__init__()
        self.config_mgr = config_mgr
        self.mode = MODE_CLICK_THROUGH

        # Drawing state & stacks
        self.permanent_strokes: List[Dict[str, Any]] = []
        self.undo_stack: List[Dict[str, Any]] = []
        self.current_points: List[Point] = []
        self.cursor_pos: Optional[QPointF] = None

        # Managers
        fps = int(self.config_mgr.get("system", "fps_limit", 60))
        self.fade_manager = FadeManager(self.update, fps=fps)
        conf_thresh = float(self.config_mgr.get("drawing", "shape_confidence_threshold", 0.88))
        self.recognizer = ShapeRecognizer(confidence_threshold=conf_thresh)

        self._init_window()

    def _init_window(self) -> None:
        """Initializes frameless, translucent, always-on-top window."""
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.set_mode(MODE_CLICK_THROUGH)

    def set_mode(self, new_mode: str) -> None:
        """Switches interaction mode (click-through vs drawing/eraser)."""
        self.mode = new_mode
        if new_mode == MODE_CLICK_THROUGH:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.cursor_pos = None
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            if self.config_mgr.get("drawing", "cursor_dot", True):
                self.setCursor(Qt.CursorShape.BlankCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
        self.update()

    def toggle_mode(self, target_mode: str) -> None:
        """Toggles between target drawing mode and click-through navigation."""
        if self.mode == target_mode:
            self.set_mode(MODE_CLICK_THROUGH)
        else:
            self.set_mode(target_mode)

    def undo(self) -> None:
        """Reverts the last permanent stroke or vanishing stroke."""
        if self.permanent_strokes:
            stroke = self.permanent_strokes.pop()
            self.undo_stack.append(stroke)
            self.update()
        elif self.fade_manager.remove_last():
            self.update()

    def clear_all(self) -> None:
        """Instantly wipes all strokes from the screen."""
        self.permanent_strokes.clear()
        self.undo_stack.clear()
        self.fade_manager.clear()
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            if self.mode == MODE_ERASER:
                self._erase_at(pos.x(), pos.y())
            else:
                self.current_points = [(pos.x(), pos.y())]
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position()
        self.cursor_pos = pos
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.mode == MODE_ERASER:
                self._erase_at(pos.x(), pos.y())
            elif self.mode in (MODE_DRAW_FIXED, MODE_DRAW_VANISHING):
                self.current_points.append((pos.x(), pos.y()))
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.current_points:
            color = self.config_mgr.get("drawing", "active_color", "#00FF87")
            width = int(self.config_mgr.get("drawing", "stroke_width", 4))
            enable_glow = bool(self.config_mgr.get("drawing", "neon_glow", True))
            glow_intensity = float(self.config_mgr.get("drawing", "neon_intensity", 0.75))

            shape_def = None
            if self.config_mgr.get("drawing", "shape_recognition", True):
                shape_def = self.recognizer.recognize(self.current_points)

            stroke_dict = {
                "points": list(self.current_points),
                "shape": shape_def,
                "color": color,
                "width": width,
                "glow": enable_glow,
                "glow_intensity": glow_intensity
            }

            if self.mode == MODE_DRAW_FIXED:
                self.permanent_strokes.append(stroke_dict)
            elif self.mode == MODE_DRAW_VANISHING:
                dur = float(self.config_mgr.get("drawing", "vanishing_duration", 2.0))
                fade_speed = float(self.config_mgr.get("drawing", "fadeout_speed", 0.6))
                self.fade_manager.add_stroke(stroke_dict, duration=dur, fade_duration=fade_speed)

            self.current_points = []
            self.update()

    def _erase_at(self, x: float, y: float, radius: float = 20.0) -> None:
        """Removes permanent strokes located within eraser radius."""
        survived = []
        for s in self.permanent_strokes:
            hit = False
            for px, py in s.get("points", []):
                if (px - x) ** 2 + (py - y) ** 2 <= radius ** 2:
                    hit = True
                    break
            if not hit:
                survived.append(s)
        if len(survived) != len(self.permanent_strokes):
            self.permanent_strokes = survived
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # 1. Render Permanent Strokes
        for s in self.permanent_strokes:
            self._render_single_stroke(painter, s, alpha=1.0)

        # 2. Render Vanishing Strokes
        for vs in self.fade_manager.strokes:
            self._render_single_stroke(painter, vs.data, alpha=vs.alpha_factor)

        # 3. Render Current Live Freehand Stroke
        if self.current_points:
            path = NeonRenderer.create_smooth_path(self.current_points)
            color = self.config_mgr.get("drawing", "active_color", "#00FF87")
            w = int(self.config_mgr.get("drawing", "stroke_width", 4))
            glow = bool(self.config_mgr.get("drawing", "neon_glow", True))
            NeonRenderer.draw_neon_stroke(painter, path, color, w, alpha_factor=1.0, enable_glow=glow)

        # 4. Render Neon Cursor Dot
        if self.mode != MODE_CLICK_THROUGH and self.cursor_pos:
            color = self.config_mgr.get("drawing", "active_color", "#00FF87")
            w = int(self.config_mgr.get("drawing", "stroke_width", 4))
            dot_rad = max(4.0, w / 2.0 + 3.0)
            NeonRenderer.draw_neon_cursor_dot(painter, self.cursor_pos, color, radius=dot_rad)

    def _render_single_stroke(self, painter: QPainter, stroke_data: dict, alpha: float) -> None:
        """Renders either recognized shape or freehand path."""
        color = stroke_data.get("color", "#00FF87")
        width = stroke_data.get("width", 4)
        glow = stroke_data.get("glow", True)
        shape_def = stroke_data.get("shape")

        if shape_def:
            NeonRenderer.draw_shape(painter, shape_def, color, width, alpha_factor=alpha, enable_glow=glow)
        else:
            path = NeonRenderer.create_smooth_path(stroke_data.get("points", []))
            NeonRenderer.draw_neon_stroke(painter, path, color, width, alpha_factor=alpha, enable_glow=glow)
