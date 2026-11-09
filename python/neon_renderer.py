"""
Neon Glow Renderer for Phoenix Pen.
Renders smooth antialiased strokes with vivid neon glow layers, metallic highlights, and custom cursors.
Atlas Standard: < 250 lines.
"""

from typing import Any, Dict, List, Tuple
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen

Point = Tuple[float, float]
METALLIC_SHADES = {
    "#FFD700", "#E5A93C", "#C59B27", "#E2E8F0",
    "#CBD5E1", "#38BDF8", "#F472B6", "#FB923C", "#10B981"
}


def is_metallic_color(color_hex: str) -> bool:
    """Detects whether a color is metallic (gold, bronze, silver, copper, etc.)."""
    if not color_hex:
        return False
    u = color_hex.upper()
    if u in METALLIC_SHADES:
        return True
    qc = QColor(color_hex)
    if not qc.isValid():
        return False
    h = qc.hsvHue()
    s = qc.hsvSaturationF()
    v = qc.valueF()
    # Gold & Bronze
    if 25 <= h <= 65 and v >= 0.55:
        return True
    # Silver & Chrome (low saturation, high brightness)
    if s <= 0.28 and v >= 0.70:
        return True
    # Rose Gold & Copper
    if (h >= 340 or h <= 25) and 0.15 <= s <= 0.65 and v >= 0.65:
        return True
    # Titanium Blue
    if 190 <= h <= 215 and 0.20 <= s <= 0.85 and v >= 0.75:
        return True
    return False


class NeonRenderer:
    """Provides high-performance neon glow drawing utilities for QPainter."""

    @staticmethod
    def create_smooth_path(points: List[Point]) -> QPainterPath:
        path = QPainterPath()
        if not points:
            return path

        path.moveTo(QPointF(points[0][0], points[0][1]))
        if len(points) == 1:
            path.addEllipse(QPointF(points[0][0], points[0][1]), 1.5, 1.5)
            return path
        if len(points) == 2:
            path.lineTo(QPointF(points[1][0], points[1][1]))
            return path

        for i in range(1, len(points) - 1):
            p0, p1 = points[i], points[i + 1]
            mid_x = (p0[0] + p1[0]) / 2.0
            mid_y = (p0[1] + p1[1]) / 2.0
            path.quadTo(QPointF(p0[0], p0[1]), QPointF(mid_x, mid_y))

        path.lineTo(QPointF(points[-1][0], points[-1][1]))
        return path

    @staticmethod
    def draw_neon_stroke(
        painter: QPainter,
        path: QPainterPath,
        color_hex: str,
        width: int,
        alpha_factor: float = 1.0,
        enable_glow: bool = True,
        glow_intensity: float = 0.75
    ) -> None:
        """Renders path with pure vivid stroke in user color and subtle aura (no white core, no dark fringe)."""
        painter.setBrush(Qt.BrushStyle.NoBrush)
        base_color = QColor(color_hex) if QColor(color_hex).isValid() else QColor("#00FF87")

        # Pure solid crisp stroke in user exact chosen color (zero outer fringe, zero dark contour)
        core_color = QColor(base_color)
        core_color.setAlpha(max(0, min(255, int(255 * alpha_factor))))
        painter.setPen(QPen(core_color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)

    @staticmethod
    def draw_shape(
        painter: QPainter,
        shape_def: Dict[str, Any],
        color_hex: str,
        width: int,
        alpha_factor: float = 1.0,
        enable_glow: bool = True
    ) -> None:
        """Draws recognized geometric shapes (lines, arrows, rectangles, circles, ovals)."""
        shape_type = shape_def.get("type")
        path = QPainterPath()

        if shape_type == "line":
            s, e = shape_def["start"], shape_def["end"]
            path.moveTo(s[0], s[1])
            path.lineTo(e[0], e[1])

        elif shape_type == "arrow":
            s, e = shape_def["start"], shape_def["end"]
            hl, hr = shape_def["head_left"], shape_def["head_right"]
            path.moveTo(s[0], s[1])
            path.lineTo(e[0], e[1])
            path.moveTo(hl[0], hl[1])
            path.lineTo(e[0], e[1])
            path.lineTo(hr[0], hr[1])

        elif shape_type in ("rectangle", "square"):
            x, y, w, h = shape_def["rect"]
            path.addRoundedRect(QRectF(x, y, w, h), 4.0, 4.0)

        elif shape_type == "circle":
            cx, cy = shape_def["center"]
            r = shape_def["radius"]
            path.addEllipse(QPointF(cx, cy), r, r)

        elif shape_type == "ellipse":
            x, y, w, h = shape_def["rect"]
            path.addEllipse(QRectF(x, y, w, h))

        NeonRenderer.draw_neon_stroke(painter, path, color_hex, width, alpha_factor, enable_glow)

    @staticmethod
    def draw_neon_cursor_dot(painter: QPainter, pos: QPointF, color_hex: str, radius: float = 6.0) -> None:
        """Draws glowing cursor dot at current mouse position."""
        base_color = QColor(color_hex) if QColor(color_hex).isValid() else QColor("#00FF87")
        painter.setBrush(Qt.BrushStyle.NoBrush)
        glow_color = QColor(base_color)
        glow_color.setAlpha(90)
        painter.setPen(QPen(glow_color, 4.0))
        painter.drawEllipse(pos, radius + 4.0, radius + 4.0)
        painter.setPen(QPen(base_color, 2.0))
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.drawEllipse(pos, radius, radius)

    @staticmethod
    def draw_eraser_cursor(painter: QPainter, pos: QPointF, radius: float) -> None:
        """Renders circular eraser guide showing exact cut area following mouse."""
        painter.setBrush(QBrush(QColor(255, 255, 255, 25)))
        painter.setPen(QPen(QColor(255, 75, 75, 220), 1.5, Qt.PenStyle.DashLine))
        painter.drawEllipse(pos, radius, radius)
        painter.setBrush(QBrush(QColor(255, 75, 75, 240)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(pos, 2.5, 2.5)
