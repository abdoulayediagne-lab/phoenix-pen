"""
Automated Core Verification Test for Phoenix Pen.
Verifies Shape Recognizer precision, Fade Manager idle stop, and Config Manager.
Atlas Standard: < 250 lines.
"""

import math
import sys
from config_manager import ConfigManager
from fade_manager import FadeManager
from shape_recognizer import ShapeRecognizer


def test_shape_recognizer():
    print("[TEST] Testing Shape Recognizer...")
    recognizer = ShapeRecognizer(confidence_threshold=0.88)

    # 1. Straight Line
    line_pts = [(float(i * 10), float(i * 10)) for i in range(25)]
    res_line = recognizer.recognize(line_pts)
    assert res_line is not None, "Line recognition failed!"
    assert res_line["type"] in ("line", "arrow"), f"Expected line, got {res_line['type']}"
    print("  ✓ Straight Line detected with confidence:", res_line["confidence"])

    # 2. Perfect Circle
    cx, cy, r = 200.0, 200.0, 80.0
    circle_pts = []
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        circle_pts.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
    circle_pts.append(circle_pts[0])  # closed
    res_circle = recognizer.recognize(circle_pts)
    assert res_circle is not None, "Circle recognition failed!"
    assert res_circle["type"] == "circle", f"Expected circle, got {res_circle['type']}"
    print("  ✓ Circle detected with confidence:", res_circle["confidence"])

    # 3. Rectangle
    rect_pts = []
    # top side
    rect_pts += [(float(x), 100.0) for x in range(100, 300, 10)]
    # right side
    rect_pts += [(300.0, float(y)) for y in range(100, 250, 10)]
    # bottom side
    rect_pts += [(float(x), 250.0) for x in range(300, 100, -10)]
    # left side
    rect_pts += [(100.0, float(y)) for y in range(250, 100, -10)]
    rect_pts.append((100.0, 100.0))
    res_rect = recognizer.recognize(rect_pts)
    assert res_rect is not None, "Rectangle recognition failed!"
    assert res_rect["type"] in ("rectangle", "square"), f"Expected rectangle, got {res_rect['type']}"
    print("  ✓ Rectangle detected with confidence:", res_rect["confidence"])

    # 4. Irregular Doodle (Freedom Guard: MUST NOT be transformed!)
    doodle_pts = [(float(i * 5), float((i % 3) * 40 + i * 2)) for i in range(30)]
    res_doodle = recognizer.recognize(doodle_pts)
    assert res_doodle is None, f"Freedom guard failed! Doodle recognized as: {res_doodle}"
    print("  ✓ Irregular doodle correctly preserved without false snap.")


def test_config_manager():
    print("[TEST] Testing Config Manager...")
    mgr = ConfigManager()
    assert mgr.get("drawing", "stroke_width") is not None
    assert mgr.get("drawing", "vanishing_duration") == 2.0
    print("  ✓ Config Manager loaded default keys correctly.")


def test_fade_manager():
    print("[TEST] Testing Fade Manager...")
    repaints = 0

    def _on_rep():
        nonlocal repaints
        repaints += 1

    fade = FadeManager(_on_rep, fps=60)
    assert not fade.is_animating(), "Fade manager should be stopped initially."

    stroke = {"points": [(0, 0), (10, 10)], "color": "#00FF87", "width": 4}
    fade.add_stroke(stroke, duration=0.05, fade_duration=0.05)
    assert fade.is_animating(), "Fade manager must awaken when stroke is added."
    fade.clear()
    assert not fade.is_animating(), "Fade manager must stop when cleared (0% CPU)."
    print("  ✓ Fade Manager starts and stops accurately.")


if __name__ == "__main__":
    from PyQt6.QtCore import QCoreApplication
    app = QCoreApplication.instance() or QCoreApplication(sys.argv)

    test_shape_recognizer()
    test_config_manager()
    test_fade_manager()
    print("🎉 ALL CORE TESTS PASSED SUCCESSFULLY!")
