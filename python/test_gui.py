"""
GUI Component Initialization Test for Phoenix Pen.
Verifies OverlayWindow, ConfigWindow, and TrayApp can be created without runtime exceptions.
Atlas Standard: < 250 lines.
"""

import sys
from PyQt6.QtWidgets import QApplication
from config_gui import ConfigWindow
from config_manager import ConfigManager
from overlay_window import MODE_CLICK_THROUGH, MODE_DRAW_FIXED, OverlayWindow
from tray_app import TrayApp


def test_gui_components():
    app = QApplication.instance() or QApplication(sys.argv)
    cfg = ConfigManager()

    print("[TEST] Initializing OverlayWindow...")
    overlay = OverlayWindow(cfg)
    assert overlay.mode == MODE_CLICK_THROUGH
    overlay.set_mode(MODE_DRAW_FIXED)
    assert overlay.mode == MODE_DRAW_FIXED
    overlay.undo()
    overlay.clear_all()
    print("  ✓ OverlayWindow verified.")

    print("[TEST] Initializing ConfigWindow...")
    config_win = ConfigWindow(cfg)
    assert "Phoenix Pen" in config_win.windowTitle()
    print("  ✓ ConfigWindow verified.")

    print("[TEST] Initializing FloatingHUD...")
    from floating_hud import FloatingHUD
    hud = FloatingHUD(
        on_toggle_fixed=lambda: None,
        on_toggle_vanishing=lambda: None,
        on_toggle_eraser=lambda: None,
        on_clear=lambda: None,
        on_undo=lambda: None,
        on_dashboard=lambda: None,
        config_mgr=cfg
    )
    assert hud.btn_fixed is not None
    print("  ✓ FloatingHUD verified.")

    print("[TEST] Initializing TrayApp...")
    tray = TrayApp(
        on_toggle_fixed=lambda: None,
        on_toggle_vanishing=lambda: None,
        on_toggle_eraser=lambda: None,
        on_clear=lambda: None,
        on_undo=lambda: None,
        on_config=lambda: None,
        on_quit=lambda: None
    )
    assert tray.toolTip().startswith("⚡ Phoenix Pen")
    print("  ✓ TrayApp verified.")

    print("[TEST] Initializing UpdateHUD...")
    from update_hud import UpdateHUD
    update_hud = UpdateHUD()
    update_hud.show_update("abc1234")
    assert update_hud.isVisible()
    update_hud.dismiss()
    assert not update_hud.isVisible()
    update_hud.show_update("abc1234")
    assert not update_hud.isVisible(), "Dismissed version must stay hidden"
    update_hud.stop()
    print("  ✓ UpdateHUD verified.")

    print("🎉 ALL GUI COMPONENTS INITIALIZED SUCCESSFULLY!")


if __name__ == "__main__":
    test_gui_components()

