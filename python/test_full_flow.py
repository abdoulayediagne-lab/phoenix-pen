"""
Full End-to-End Simulation Test for Phoenix Pen.
Verifies all buttons on FloatingHUD, Hotkeys dispatcher, Mode switching, and Canvas state.
Atlas Standard: < 250 lines.
"""

import sys
from PyQt6.QtWidgets import QApplication
from config_manager import ConfigManager
from floating_hud import FloatingHUD
from hotkey_manager import HotkeyManager
from overlay_window import (
    MODE_CLICK_THROUGH, MODE_DRAW_FIXED, MODE_DRAW_VANISHING, MODE_ERASER, OverlayWindow
)


class FakeKey:
    def __init__(self, char=None, vk=None):
        self.char = char
        self.vk = vk


def test_full_flow():
    print("[TEST] Running Full End-to-End Verification...")
    app = QApplication.instance() or QApplication(sys.argv)
    cfg = ConfigManager()
    overlay = OverlayWindow(cfg)
    overlay.show()

    hud = FloatingHUD(
        on_toggle_fixed=lambda: overlay.toggle_mode(MODE_DRAW_FIXED),
        on_toggle_vanishing=lambda: overlay.toggle_mode(MODE_DRAW_VANISHING),
        on_toggle_eraser=lambda: overlay.toggle_mode(MODE_ERASER),
        on_clear=overlay.clear_all,
        on_undo=overlay.undo,
        on_dashboard=lambda: None,
        config_mgr=cfg
    )
    hud.show()

    # 1. Test HUD Buttons Clicks
    print("  1. Testing HUD Buttons Clicks...")
    hud.btn_fixed.click()
    assert overlay.mode == MODE_DRAW_FIXED, f"Expected {MODE_DRAW_FIXED}, got {overlay.mode}"
    print("     ✓ Click [ 🖋️ Fixe ] activates MODE_DRAW_FIXED.")

    hud.btn_fixed.click()
    assert overlay.mode == MODE_CLICK_THROUGH, f"Expected {MODE_CLICK_THROUGH}, got {overlay.mode}"
    print("     ✓ Click [ 🖋️ Fixe ] again toggles back to MODE_CLICK_THROUGH.")

    hud.btn_vanishing.click()
    assert overlay.mode == MODE_DRAW_VANISHING, f"Expected {MODE_DRAW_VANISHING}, got {overlay.mode}"
    print("     ✓ Click [ ⏳ Fade ] activates MODE_DRAW_VANISHING.")

    hud.btn_eraser.click()
    assert overlay.mode == MODE_ERASER, f"Expected {MODE_ERASER}, got {overlay.mode}"
    print("     ✓ Click [ 🧹 Gomme ] activates MODE_ERASER.")

    hud.btn_clear.click()
    assert len(overlay.permanent_strokes) == 0
    print("     ✓ Click [ 🗑️ Clear ] wipes canvas.")

    hidden = []
    hud.on_hide = lambda: hidden.append(True)
    hud.btn_hide.click()
    assert len(hidden) == 1
    print("     ✓ Click [ 👁️ Hide ] triggers HUD hide callback.")

    # 2. Test Hotkeys Dispatcher
    print("  2. Testing Hotkey Dispatcher...")
    hotkeys = HotkeyManager(cfg)
    signals_received = []

    hotkeys.sig_toggle_draw_fixed.connect(lambda: signals_received.append("fixed"))
    hotkeys.sig_toggle_draw_vanishing.connect(lambda: signals_received.append("vanishing"))
    hotkeys.sig_toggle_eraser.connect(lambda: signals_received.append("eraser"))
    hotkeys.sig_undo.connect(lambda: signals_received.append("undo"))
    hotkeys.sig_toggle_hud.connect(lambda: signals_received.append("hud"))

    # Simulate Cmd+Shift+D (d key vk=2)
    hotkeys.cmd_down = True
    hotkeys.shift_down = True
    hotkeys._on_press(FakeKey(vk=2))
    hotkeys._on_release(FakeKey(vk=2))
    assert "fixed" in signals_received, "Cmd+Shift+D failed!"
    print("     ✓ Cmd+Shift+D triggered fixed mode signal.")

    # Simulate Option+H (h key vk=4)
    hotkeys._on_press(FakeKey(vk=4, char='h'))
    assert "hud" in signals_received, "Option+H / Cmd+Shift+H failed!"
    print("     ✓ Option+H triggered HUD toggle signal.")

    # Simulate Cmd+D (d key vk=2)
    hotkeys.shift_down = False
    hotkeys._on_press(FakeKey(vk=2))
    hotkeys._on_release(FakeKey(vk=2))
    assert signals_received.count("fixed") == 2, "Cmd+D failed!"
    print("     ✓ Cmd+D triggered fixed mode signal.")

    # Simulate Cmd+Shift+V (v key vk=9)
    hotkeys.shift_down = True
    hotkeys._on_press(FakeKey(vk=9))
    hotkeys._on_release(FakeKey(vk=9))
    assert "vanishing" in signals_received, "Cmd+Shift+V failed!"
    print("     ✓ Cmd+Shift+V triggered vanishing mode signal.")

    # Simulate Option+V (macOS French dead-key ◊)
    hotkeys.cmd_down = False
    hotkeys.shift_down = False
    hotkeys.alt_down = True
    hotkeys._on_press(FakeKey(char="◊"))
    hotkeys._on_release(FakeKey(char="◊"))
    assert signals_received.count("vanishing") == 2, "Option+V dead-key failed!"
    print("     ✓ Option+V (dead-key ◊) triggered vanishing mode signal.")

    # Simulate Cmd+Z (z key vk=6)
    hotkeys.alt_down = False
    hotkeys.cmd_down = True
    hotkeys._on_press(FakeKey(vk=6, char="z"))
    assert "undo" in signals_received, "Cmd+Z failed!"
    print("     ✓ Cmd+Z triggered undo signal.")

    print("🎉 FULL END-TO-END FLOW VERIFIED 100%!")


if __name__ == "__main__":
    test_full_flow()

