"""
Neon Glow Renderer for Phoenix Pen.
Renders ultra-smooth Catmull-Rom cubic Bézier strokes, snapped geometry, and high-DPI cursors.
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
    """Detects whether a color is metallic (gold, bronze, silver, copper, titanium)."""
    if not color_hex:
        return False
    if color_hex.upper() in METALLIC_SHADES:
        return True
    qc = QColor(color_hex)
    if not qc.isValid():
        return False
    h, s, v = qc.hsvHue(), qc.hsvSaturationF(), qc.valueF()
    if 25 <= h <= 65 and v >= 0.55:
        return True
    if s <= 0.28 and v >= 0.70:
        return True
    if (h >= 340 or h <= 25) and 0.15 <= s <= 0.65 and v >= 0.65:
        return True
    if 190 <= h <= 215 and 0.20 <= s <= 0.85 and v >= 0.75:
        return True
    return False


class NeonRenderer:
    """Provides high-performance, ultra-smooth curve drawing utilities for QPainter."""

    @staticmethod
    def create_smooth_path(points: List[Point]) -> QPainterPath:
        """Transforms raw input points into continuous C1 cubic Bézier splines (Catmull-Rom)."""
        path = QPainterPath()
        if not points:
            return path

        # 1. Distance filter: eliminate micro-jitter (< 1.5px distance)
        filtered: List[Point] = [points[0]]
        for p in points[1:]:
            dx, dy = p[0] - filtered[-1][0], p[1] - filtered[-1][1]
            if dx * dx + dy * dy >= 2.25:
                filtered.append(p)
        if len(filtered) < len(points) and points[-1] != filtered[-1]:
            filtered.append(points[-1])

        n = len(filtered)
        if n == 1:
            path.addEllipse(QPointF(filtered[0][0], filtered[0][1]), 1.5, 1.5)
            return path
        if n == 2:
            path.moveTo(QPointF(filtered[0][0], filtered[0][1]))
            path.lineTo(QPointF(filtered[1][0], filtered[1][1]))
            return path

        # 2. Catmull-Rom to Cubic Bézier conversion
        path.moveTo(QPointF(filtered[0][0], filtered[0][1]))
        for i in range(n - 1):
            p0 = filtered[max(i - 1, 0)]
            p1 = filtered[i]
            p2 = filtered[i + 1]
            p3 = filtered[min(i + 2, n - 1)]

            cp1_x = p1[0] + (p2[0] - p0[0]) / 6.0
            cp1_y = p1[1] + (p2[1] - p0[1]) / 6.0
            cp2_x = p2[0] - (p3[0] - p1[0]) / 6.0
            cp2_y = p2[1] - (p3[1] - p1[1]) / 6.0
            path.cubicTo(QPointF(cp1_x, cp1_y), QPointF(cp2_x, cp2_y), QPointF(p2[0], p2[1]))
        return path

    @staticmethod
    def draw_neon_stroke(
        painter: QPainter,
        path: QPainterPath,
        color_hex: str,
        width: int,
        alpha_factor: float = 1.0,
        enable_glow: bool = False,
        glow_intensity: float = 0.75
    ) -> None:
        """Renders pure, crisp, solid strokes in user's color with antialiased round caps."""
        painter.setBrush(Qt.BrushStyle.NoBrush)
        base_color = QColor(color_hex) if QColor(color_hex).isValid() else QColor("#00FF87")

        if enable_glow and width >= 4:
            glow_col = QColor(base_color)
            glow_col.setAlpha(max(0, min(255, int(50 * glow_intensity * alpha_factor))))
            painter.setPen(QPen(glow_col, width + 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawPath(path)

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
        enable_glow: bool = False
    ) -> None:
        """Renders snapped geometric shapes (lines, arrows, rectangles, circles, ovals)."""
        shape_type = shape_def.get("type")
        path = QPainterPath()

        if shape_type == "line":
            s, e = shape_def["start"], shape_def["end"]
            path.moveTo(s[0], s[1]); path.lineTo(e[0], e[1])
        elif shape_type == "arrow":
            s, e = shape_def["start"], shape_def["end"]
            hl, hr = shape_def["head_left"], shape_def["head_right"]
            path.moveTo(s[0], s[1]); path.lineTo(e[0], e[1])
            path.moveTo(hl[0], hl[1]); path.lineTo(e[0], e[1]); path.lineTo(hr[0], hr[1])
        elif shape_type in ("rectangle", "square"):
            x, y, w, h = shape_def["rect"]
            path.addRoundedRect(QRectF(x, y, w, h), 4.0, 4.0)
        elif shape_type == "circle":
            cx, cy, r = shape_def["center"][0], shape_def["center"][1], shape_def["radius"]
            path.addEllipse(QPointF(cx, cy), r, r)
        elif shape_type == "ellipse":
            x, y, w, h = shape_def["rect"]
            path.addEllipse(QRectF(x, y, w, h))

        NeonRenderer.draw_neon_stroke(painter, path, color_hex, width, alpha_factor, enable_glow)

    @staticmethod
    def draw_neon_cursor_dot(painter: QPainter, pos: QPointF, color_hex: str, radius: float = 5.0) -> None:
        """Draws glowing cursor dot at current mouse position."""
        base_color = QColor(color_hex) if QColor(color_hex).isValid() else QColor("#00FF87")
        painter.setBrush(Qt.BrushStyle.NoBrush)
        glow_color = QColor(base_color); glow_color.setAlpha(90)
        painter.setPen(QPen(glow_color, 3.0))
        painter.drawEllipse(pos, radius + 3.0, radius + 3.0)
        painter.setPen(QPen(base_color, 1.5))
        painter.setBrush(QBrush(QColor(255, 255, 255, 245)))
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
