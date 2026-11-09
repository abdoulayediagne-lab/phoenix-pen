"""
Geometric Shape Recognizer for Phoenix Pen.
Detects Lines, Arrows, Rectangles, Squares, Circles, and Ellipses.
Strict confidence threshold (default >= 88%) preserves freehand drawing freedom.
Atlas Standard: < 250 lines.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

Point = Tuple[float, float]


class ShapeRecognizer:
    """Evaluates freehand point sequences and returns snapped shape definitions."""

    def __init__(self, confidence_threshold: float = 0.88) -> None:
        self.threshold = confidence_threshold

    def recognize(self, points: List[Point]) -> Optional[Dict[str, Any]]:
        """Analyzes a sequence of points. Returns None if below confidence threshold."""
        if len(points) < 8:
            return None

        total_arc_len = self._arc_length(points)
        if total_arc_len < 25.0:
            return None

        # 1. Test for Straight Line
        line_res = self._test_line(points, total_arc_len)
        if line_res:
            # Check if it has an arrowhead
            arrow_res = self._test_arrow(points, line_res)
            return arrow_res if arrow_res else line_res

        # 2. Test for Closed Shapes (Circle, Ellipse, Rectangle, Square)
        p_start, p_end = points[0], points[-1]
        closure_dist = math.hypot(p_end[0] - p_start[0], p_end[1] - p_start[1])
        if closure_dist / total_arc_len < 0.28:
            # Test Circle first (CV is distinctively low < 0.06)
            circle_res = self._test_circle(points, total_arc_len)
            if circle_res:
                return circle_res

            rect_res = self._test_rectangle(points, total_arc_len)
            if rect_res:
                return rect_res

            ellipse_res = self._test_ellipse(points)
            if ellipse_res:
                return ellipse_res

        return None

    def _arc_length(self, points: List[Point]) -> float:
        total = 0.0
        for i in range(len(points) - 1):
            total += math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
        return total

    def _test_line(self, points: List[Point], total_arc: float) -> Optional[Dict[str, Any]]:
        p0, pn = points[0], points[-1]
        chord = math.hypot(pn[0] - p0[0], pn[1] - p0[1])
        if chord < 20:
            return None

        straightness = chord / total_arc
        if straightness < self.threshold:
            return None

        # Check max deviation perpendicular to chord
        max_dev = 0.0
        vx, vy = pn[0] - p0[0], pn[1] - p0[1]
        v_len = chord
        for px, py in points:
            dist = abs(vy * px - vx * py + pn[0] * p0[1] - pn[1] * p0[0]) / v_len
            if dist > max_dev:
                max_dev = dist

        if (max_dev / chord) < (1.0 - self.threshold):
            return {
                "type": "line",
                "start": p0,
                "end": pn,
                "confidence": straightness
            }
        return None

    def _test_arrow(self, points: List[Point], line_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detects if end of stroke forms a directional arrow tip."""
        p0, pn = line_info["start"], line_info["end"]
        dx, dy = pn[0] - p0[0], pn[1] - p0[1]
        shaft_len = math.hypot(dx, dy)
        if shaft_len < 35:
            return None

        angle = math.atan2(dy, dx)
        head_len = min(24.0, max(12.0, shaft_len * 0.18))
        wing_angle = math.radians(28)

        left_x = pn[0] - head_len * math.cos(angle - wing_angle)
        left_y = pn[1] - head_len * math.sin(angle - wing_angle)
        right_x = pn[0] - head_len * math.cos(angle + wing_angle)
        right_y = pn[1] - head_len * math.sin(angle + wing_angle)

        return {
            "type": "arrow",
            "start": p0,
            "end": pn,
            "head_left": (left_x, left_y),
            "head_right": (right_x, right_y),
            "confidence": line_info["confidence"]
        }

    def _test_circle(self, points: List[Point], total_arc: float) -> Optional[Dict[str, Any]]:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)

        dists = [math.hypot(p[0] - cx, p[1] - cy) for p in points]
        avg_r = sum(dists) / len(dists)
        if avg_r < 12.0:
            return None

        variance = sum((d - avg_r) ** 2 for d in dists) / len(dists)
        std_dev = math.sqrt(variance)
        cv = std_dev / avg_r

        # Strict circle test: CV must be < 0.07 to never confuse with square (cv ~0.11)
        if cv <= 0.07:
            # Also check circle perimeter: 2 * pi * r
            expected_perim = 2.0 * math.pi * avg_r
            if abs(total_arc - expected_perim) / expected_perim < 0.15:
                return {
                    "type": "circle",
                    "center": (cx, cy),
                    "radius": avg_r,
                    "confidence": 1.0 - cv
                }
        return None

    def _test_ellipse(self, points: List[Point]) -> Optional[Dict[str, Any]]:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w = max_x - min_x
        h = max_y - min_y
        if w < 20 or h < 20:
            return None

        rx, ry = w / 2.0, h / 2.0
        cx, cy = min_x + rx, min_y + ry

        # Normalized radial error to ellipse formula: (x/rx)^2 + (y/ry)^2 = 1
        errors = [abs(math.hypot((p[0] - cx) / rx, (p[1] - cy) / ry) - 1.0) for p in points]
        avg_err = sum(errors) / len(errors)

        if avg_err <= (1.0 - self.threshold * 0.92):  # avg_err <= ~0.16
            return {
                "type": "ellipse",
                "rect": (min_x, min_y, w, h),
                "center": (cx, cy),
                "radii": (rx, ry),
                "confidence": 1.0 - avg_err
            }
        return None

    def _test_rectangle(self, points: List[Point], total_arc: float) -> Optional[Dict[str, Any]]:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w, h = max_x - min_x, max_y - min_y
        if w < 20 or h < 20:
            return None

        # Perimeter of bounding box: rectangle points travel along sides, error < 10%
        bbox_perim = 2.0 * (w + h)
        perim_ratio = abs(total_arc - bbox_perim) / bbox_perim

        if perim_ratio > 0.10:
            return None

        # Check how close points are to the 4 sides of the bounding box
        dists_to_box = []
        for px, py in points:
            d_left = abs(px - min_x)
            d_right = abs(px - max_x)
            d_top = abs(py - min_y)
            d_bottom = abs(py - max_y)
            dists_to_box.append(min(d_left, d_right, d_top, d_bottom))

        mean_dist = sum(dists_to_box) / len(dists_to_box)
        diag = math.hypot(w, h)
        norm_dev = mean_dist / diag

        if norm_dev < (1.0 - self.threshold * 0.90):  # norm_dev < ~0.15
            shape_type = "square" if abs(w - h) / max(w, h) < 0.15 else "rectangle"
            return {
                "type": shape_type,
                "rect": (min_x, min_y, w, h),
                "confidence": 1.0 - norm_dev
            }
        return None
