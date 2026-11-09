"""
Interactive Color Wheels with Movable Reticles for Phoenix Pen.
Wheel 1: Full-hue Rainbow Neon Wheel.
Wheel 2: Metallic, Solar Gold, Bronze, Silver, and Shimmer Wheel.
Atlas Standard: < 250 lines.
"""

import math
from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush, QColor, QConicalGradient, QMouseEvent, QPaintEvent,
    QPainter, QPen, QRadialGradient
)
from PyQt6.QtWidgets import QWidget


class BaseColorWheel(QWidget):
    """Base class for interactive circular color wheel with reticle."""

    sig_color_changed = pyqtSignal(str)

    def __init__(self, size: int = 140) -> None:
        super().__init__()
        self.wheel_size = size
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.radius = (size / 2.0) - 7.0
        self.center = QPointF(size / 2.0, size / 2.0)
        self.reticle_pos = QPointF(self.center)
        self.current_hex = "#00FF87"
        self.is_dragging = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self._update_from_pos(event.position()); event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.is_dragging or (event.buttons() & Qt.MouseButton.LeftButton):
            self._update_from_pos(event.position()); event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.is_dragging = False; event.accept()

    def _draw_reticle(self, p: QPainter, pos: QPointF, fill_col: QColor) -> None:
        """Renders high-visibility crosshair reticle following the touch point."""
        x, y = pos.x(), pos.y()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(0, 0, 0, 200), 2.5)); p.drawEllipse(pos, 7.5, 7.5)
        p.setPen(QPen(QColor(255, 255, 255, 250), 2.0)); p.drawEllipse(pos, 7.0, 7.0)
        p.setPen(QPen(QColor(255, 255, 255, 230), 1.5))
        p.drawLine(QPointF(x - 10, y), QPointF(x - 6, y))
        p.drawLine(QPointF(x + 6, y), QPointF(x + 10, y))
        p.drawLine(QPointF(x, y - 10), QPointF(x, y - 6))
        p.drawLine(QPointF(x, y + 6), QPointF(x, y + 10))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(fill_col))
        p.drawEllipse(pos, 2.5, 2.5)

    def _update_from_pos(self, pos: QPointF) -> None:
        raise NotImplementedError


class NeonHueWheelWidget(BaseColorWheel):
    """Cercle 1 : Spectre Arc-en-Ciel Néon Vif avec Viseur Tactique."""

    def __init__(self, size: int = 140) -> None:
        super().__init__(size=size)
        self.reticle_pos = QPointF(self.center.x() + self.radius * 0.7, self.center.y())

    def paintEvent(self, event: QPaintEvent) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. Conical Hue Gradient (Full Rainbow Spectrum)
        conic = QConicalGradient(self.center, 0)
        for stop, hex_c in [
            (0.00, "#FF0055"), (0.08, "#FF5500"), (0.16, "#FFEA00"), (0.25, "#76FF03"),
            (0.33, "#00FF87"), (0.42, "#00E5FF"), (0.50, "#0091FF"), (0.60, "#2979FF"),
            (0.70, "#A855F7"), (0.82, "#FF1493"), (0.92, "#FF007F"), (1.00, "#FF0055")
        ]:
            conic.setColorAt(stop, QColor(hex_c))

        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(conic))
        p.drawEllipse(self.center, self.radius, self.radius)

        # 2. Radial Brightness Wash (White core fading to pure vivid neon)
        radial = QRadialGradient(self.center, self.radius)
        radial.setColorAt(0.0, QColor(255, 255, 255, 230))
        radial.setColorAt(0.35, QColor(255, 255, 255, 120))
        radial.setColorAt(0.75, QColor(255, 255, 255, 0))
        radial.setColorAt(1.0, QColor(0, 0, 0, 40))
        p.setBrush(QBrush(radial)); p.drawEllipse(self.center, self.radius, self.radius)

        # 3. Outer Neon Border & Reticle
        p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(QColor(0, 255, 135, 180), 2.0))
        p.drawEllipse(self.center, self.radius, self.radius)
        self._draw_reticle(p, self.reticle_pos, QColor(self.current_hex))

    def _update_from_pos(self, pos: QPointF) -> None:
        dx, dy = pos.x() - self.center.x(), pos.y() - self.center.y()
        dist = math.hypot(dx, dy)
        max_r = max(1.0, self.radius - 1.0)
        clamped_r = min(dist, max_r)
        nx, ny = (dx / dist, dy / dist) if dist > 0.001 else (1.0, 0.0)

        self.reticle_pos = QPointF(self.center.x() + nx * clamped_r, self.center.y() + ny * clamped_r)
        angle_deg = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0
        col = QColor.fromHsvF(angle_deg / 360.0, min(1.0, clamped_r / max_r), 1.0)
        self.current_hex = col.name().upper()
        self.update()
        self.sig_color_changed.emit(self.current_hex)

    def set_color_hex(self, hex_code: str) -> None:
        c = QColor(hex_code)
        if c.isValid():
            self.current_hex = hex_code.upper()
            h, s, _ = c.getHsvF()
            r = s * (self.radius - 2.0)
            ang = math.radians(h * 360.0)
            self.reticle_pos = QPointF(self.center.x() + r * math.cos(ang), self.center.y() + r * math.sin(ang))
            self.update()


class MetallicWheelWidget(BaseColorWheel):
    """Cercle 2 : Or Solaire, Argent, Bronze, Paillettes & Nuances Métalliques."""

    STOPS = [
        (0.00, QColor("#FFD700")), (0.12, QColor("#F5AF28")), (0.25, QColor("#9B6E28")),
        (0.38, QColor("#E8A598")), (0.50, QColor("#E2E8F0")), (0.62, QColor("#CBD5E1")),
        (0.75, QColor("#38BDF8")), (0.88, QColor("#10B981")), (1.00, QColor("#FFD700")),
    ]

    def __init__(self, size: int = 140) -> None:
        super().__init__(size=size)
        self.reticle_pos = QPointF(self.center.x() + self.radius * 0.75, self.center.y() - 10)

    def paintEvent(self, event: QPaintEvent) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. Conical Metallic Gradient
        conic = QConicalGradient(self.center, 0)
        for stop, col in self.STOPS:
            conic.setColorAt(stop, col)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(conic))
        p.drawEllipse(self.center, self.radius, self.radius)

        # 2. Specular Shimmer Wash
        radial = QRadialGradient(self.center, self.radius)
        radial.setColorAt(0.0, QColor(255, 255, 240, 240))
        radial.setColorAt(0.35, QColor(255, 240, 200, 110))
        radial.setColorAt(0.80, QColor(0, 0, 0, 0))
        radial.setColorAt(1.0, QColor(30, 20, 0, 60))
        p.setBrush(QBrush(radial)); p.drawEllipse(self.center, self.radius, self.radius)

        # 3. Permanent Glitter Stars (✦ Effet de scintillement)
        self._draw_sparkle(p, self.center.x() - 22, self.center.y() - 20, 4.5)
        self._draw_sparkle(p, self.center.x() + 26, self.center.y() - 12, 5.0)
        self._draw_sparkle(p, self.center.x() - 12, self.center.y() + 24, 4.0)
        self._draw_sparkle(p, self.center.x() + 18, self.center.y() + 22, 5.0)

        # 4. Outer Gold Border & Reticle
        p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(QColor(255, 215, 0, 200), 2.2))
        p.drawEllipse(self.center, self.radius, self.radius)
        self._draw_reticle(p, self.reticle_pos, QColor(self.current_hex))

    def _draw_sparkle(self, p: QPainter, x: float, y: float, size: float) -> None:
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(255, 255, 255, 220)))
        p.drawPolygon([QPointF(x, y - size), QPointF(x + size * 0.3, y), QPointF(x, y + size), QPointF(x - size * 0.3, y)])
        p.drawPolygon([QPointF(x - size, y), QPointF(x, y + size * 0.3), QPointF(x + size, y), QPointF(x, y - size * 0.3)])

    def _update_from_pos(self, pos: QPointF) -> None:
        dx, dy = pos.x() - self.center.x(), pos.y() - self.center.y()
        dist = math.hypot(dx, dy)
        max_r = max(1.0, self.radius - 1.0)
        clamped_r = min(dist, max_r)
        nx, ny = (dx / dist, dy / dist) if dist > 0.001 else (1.0, 0.0)

        self.reticle_pos = QPointF(self.center.x() + nx * clamped_r, self.center.y() + ny * clamped_r)
        t = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0 / 360.0
        base_col = self._sample_stops(t)
        wf = max(0.0, 1.0 - (clamped_r / max_r)) * 0.75
        r = min(255, int(base_col.red() * (1 - wf) + 255 * wf))
        g = min(255, int(base_col.green() * (1 - wf) + 255 * wf))
        b = min(255, int(base_col.blue() * (1 - wf) + 240 * wf))

        col = QColor(r, g, b)
        self.current_hex = col.name().upper()
        self.update()
        self.sig_color_changed.emit(self.current_hex)

    def _sample_stops(self, t: float) -> QColor:
        for i in range(len(self.STOPS) - 1):
            s0, c0 = self.STOPS[i]
            s1, c1 = self.STOPS[i + 1]
            if s0 <= t <= s1:
                ratio = (t - s0) / (s1 - s0) if (s1 > s0) else 0.0
                return QColor(
                    int(c0.red() + (c1.red() - c0.red()) * ratio),
                    int(c0.green() + (c1.green() - c0.green()) * ratio),
                    int(c0.blue() + (c1.blue() - c0.blue()) * ratio)
                )
        return self.STOPS[0][1]

    def set_color_hex(self, hex_code: str) -> None:
        self.current_hex = hex_code.upper(); self.update()
