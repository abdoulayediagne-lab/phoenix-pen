"""
Transparent Fullscreen Overlay Window for Phoenix Pen.
Handles native click-through toggles, mouse stroke capture, eraser, and rendering loop.
Atlas Standard: < 250 lines.
"""

import sys
from typing import Any, Dict, List, Optional, Tuple
from PyQt6.QtCore import QBuffer, QIODevice, QPointF, Qt
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QMouseEvent, QPaintEvent, QPainter, QPen, QPixmap
)
from PyQt6.QtWidgets import QApplication, QWidget

from fade_manager import FadeManager
from neon_renderer import NeonRenderer
from shape_recognizer import ShapeRecognizer

MODE_CLICK_THROUGH = "click_through"
MODE_DRAW_FIXED = "draw_fixed"
MODE_DRAW_VANISHING = "draw_vanishing"
MODE_ERASER = "eraser"
Point = Tuple[float, float]


class OverlayWindow(QWidget):
    """Fullscreen translucent overlay supporting native OS click-through and neon drawing."""

    def __init__(self, config_mgr: Any) -> None:
        super().__init__()
        self.config_mgr = config_mgr
        self.mode = MODE_CLICK_THROUGH
        self.permanent_strokes: List[Dict[str, Any]] = []
        self.undo_stack: List[Dict[str, Any]] = []
        self.current_points: List[Point] = []
        self.cursor_pos: Optional[QPointF] = None

        fps = int(self.config_mgr.get("system", "fps_limit", 60))
        self.fade_manager = FadeManager(self.update, fps=fps)
        conf = float(self.config_mgr.get("drawing", "shape_confidence_threshold", 0.88))
        self.recognizer = ShapeRecognizer(confidence_threshold=conf)
        self._init_window()

    def _init_window(self) -> None:
        """Initializes frameless, translucent, always-on-top QNSWindow."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.set_mode(MODE_CLICK_THROUGH)

    def _set_native_click_through(self, ignore: bool) -> None:
        """Configures OS-level event pass-through and multi-space support."""
        if sys.platform == "darwin":
            try:
                import AppKit, objc
                view = objc.objc_object(c_void_p=int(self.winId()))
                nswin = view.window()
                if nswin is not None:
                    nswin.setCollectionBehavior_(
                        AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                        | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
                    )
                    nswin.setIgnoresMouseEvents_(ignore)
                    if ignore:
                        nswin.setLevel_(AppKit.NSFloatingWindowLevel)
                    else:
                        nswin.setLevel_(AppKit.NSStatusWindowLevel - 1)
                        nswin.makeKeyAndOrderFront_(None)
                        nswin.orderFrontRegardless()
                        AppKit.NSRunningApplication.currentApplication().activateWithOptions_(
                            AppKit.NSApplicationActivateIgnoringOtherApps
                        )
                        nswin.invalidateCursorRectsForView_(view)
            except Exception as e:
                print(f"[OverlayWindow] macOS click-through warning: {e}")

    def _create_neon_cursor(self, color_hex: str) -> Tuple[QCursor, QPixmap]:
        """Generates a hardware-rendered glowing neon dot cursor and pixmap."""
        pix = QPixmap(32, 32)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        base = QColor(color_hex) if QColor(color_hex).isValid() else QColor("#00FF87")
        glow = QColor(base)
        glow.setAlpha(140)
        p.setPen(QPen(glow, 4.0))
        p.drawEllipse(4, 4, 24, 24)
        p.setPen(QPen(base, 1.5))
        p.setBrush(QBrush(QColor(255, 255, 255, 250)))
        p.drawEllipse(10, 10, 12, 12)
        p.end()
        return QCursor(pix, 16, 16), pix

    def _apply_cocoa_cursor(self, pix: QPixmap) -> None:
        if sys.platform == "darwin":
            try:
                import AppKit, Foundation
                buf = QBuffer()
                buf.open(QIODevice.OpenModeFlag.ReadWrite)
                pix.save(buf, "PNG")
                raw = buf.data().data()
                data = Foundation.NSData.dataWithBytes_length_(raw, len(raw))
                img = AppKit.NSImage.alloc().initWithData_(data)
                AppKit.NSCursor.alloc().initWithImage_hotSpot_(
                    img, Foundation.NSMakePoint(16, 16)
                ).set()
            except Exception:
                pass

    def _restore_cocoa_cursor(self) -> None:
        if sys.platform == "darwin":
            try:
                import AppKit
                arrow = AppKit.NSCursor.arrowCursor()
                if arrow:
                    arrow.set()
            except Exception:
                pass

    def set_mode(self, new_mode: str) -> None:
        """Switches interaction mode (click-through vs drawing/eraser)."""
        self.mode = new_mode
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()

        if new_mode == MODE_CLICK_THROUGH:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self._set_native_click_through(True)
            self.cursor_pos = None
            self.unsetCursor()
            self._restore_cocoa_cursor()
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self._set_native_click_through(False)
            if new_mode == MODE_ERASER:
                QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)
                self.setCursor(Qt.CursorShape.CrossCursor)
            else:
                color = self.config_mgr.get("drawing", "active_color", "#00FF87")
                qcur, pix = self._create_neon_cursor(color)
                QApplication.setOverrideCursor(qcur)
                self.setCursor(qcur)
                self._apply_cocoa_cursor(pix)
            self.raise_()
            self.activateWindow()
        self.update()

    def toggle_mode(self, target_mode: str) -> None:
        self.set_mode(MODE_CLICK_THROUGH if self.mode == target_mode else target_mode)

    def undo(self) -> None:
        if self.permanent_strokes:
            self.undo_stack.append(self.permanent_strokes.pop())
            self.update()
        elif self.fade_manager.remove_last():
            self.update()

    def clear_all(self) -> None:
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
            w = int(self.config_mgr.get("drawing", "stroke_width", 4))
            glow = bool(self.config_mgr.get("drawing", "neon_glow", True))
            g_int = float(self.config_mgr.get("drawing", "neon_intensity", 0.75))
            shape_def = None
            if self.config_mgr.get("drawing", "shape_recognition", True):
                shape_def = self.recognizer.recognize(self.current_points)

            stroke = {
                "points": list(self.current_points), "shape": shape_def,
                "color": color, "width": w, "glow": glow, "glow_intensity": g_int
            }
            if self.mode == MODE_DRAW_FIXED:
                self.permanent_strokes.append(stroke)
            elif self.mode == MODE_DRAW_VANISHING:
                dur = float(self.config_mgr.get("drawing", "vanishing_duration", 2.0))
                spd = float(self.config_mgr.get("drawing", "fadeout_speed", 0.6))
                self.fade_manager.add_stroke(stroke, duration=dur, fade_duration=spd)

            self.current_points = []
            self.update()

    def _erase_at(self, x: float, y: float, radius: float = 20.0) -> None:
        survived = [
            s for s in self.permanent_strokes
            if not any((px - x)**2 + (py - y)**2 <= radius**2 for px, py in s.get("points", []))
        ]
        if len(survived) != len(self.permanent_strokes):
            self.permanent_strokes = survived
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        for s in self.permanent_strokes:
            self._render_single_stroke(p, s, alpha=1.0)
        for vs in self.fade_manager.strokes:
            self._render_single_stroke(p, vs.data, alpha=vs.alpha_factor)
        if self.current_points:
            path = NeonRenderer.create_smooth_path(self.current_points)
            c = self.config_mgr.get("drawing", "active_color", "#00FF87")
            w = int(self.config_mgr.get("drawing", "stroke_width", 4))
            glow = bool(self.config_mgr.get("drawing", "neon_glow", True))
            NeonRenderer.draw_neon_stroke(p, path, c, w, alpha_factor=1.0, enable_glow=glow)
        if self.mode in (MODE_DRAW_FIXED, MODE_DRAW_VANISHING) and self.cursor_pos:
            c = self.config_mgr.get("drawing", "active_color", "#00FF87")
            NeonRenderer.draw_neon_cursor_dot(p, self.cursor_pos, c, radius=6.0)

    def _render_single_stroke(self, p: QPainter, s: dict, alpha: float) -> None:
        c, w, glow = s.get("color", "#00FF87"), s.get("width", 4), s.get("glow", True)
        shape_def = s.get("shape")
        if shape_def:
            NeonRenderer.draw_shape(p, shape_def, c, w, alpha_factor=alpha, enable_glow=glow)
        else:
            path = NeonRenderer.create_smooth_path(s.get("points", []))
            NeonRenderer.draw_neon_stroke(p, path, c, w, alpha_factor=alpha, enable_glow=glow)
