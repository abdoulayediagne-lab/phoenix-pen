"""
Main Application Controller for Phoenix Pen.
Orchestrates Overlay, System Tray, Floating HUD, Hotkeys, and Dashboard dialog.
Atlas Standard: < 250 lines.
"""

import sys
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication

from config_gui import ConfigWindow
from config_manager import ConfigManager
from floating_hud import FloatingHUD
from hotkey_manager import HotkeyManager
from overlay_window import (
    MODE_CLICK_THROUGH, MODE_DRAW_FIXED, MODE_DRAW_VANISHING, MODE_ERASER, OverlayWindow
)
from tray_app import TrayApp


class PhoenixPenApp:
    """Core controller connecting all subsystems together."""

    def __init__(self, open_dashboard_on_start: bool = False) -> None:
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 1. Config Manager
        self.config_mgr = ConfigManager()

        # 2. Translucent Fullscreen Overlay
        self.overlay = OverlayWindow(self.config_mgr)
        self._setup_screens()

        # 3. Floating Quick Toolbar (HUD)
        self.hud = FloatingHUD(
            on_toggle_fixed=lambda: self._set_mode(MODE_DRAW_FIXED),
            on_toggle_vanishing=lambda: self._set_mode(MODE_DRAW_VANISHING),
            on_toggle_eraser=lambda: self._set_mode(MODE_ERASER),
            on_clear=self.overlay.clear_all,
            on_undo=self.overlay.undo,
            on_dashboard=self.open_config,
            config_mgr=self.config_mgr
        )
        self._position_hud()

        # 4. System Tray Icon
        self.tray = TrayApp(
            on_toggle_fixed=lambda: self._set_mode(MODE_DRAW_FIXED),
            on_toggle_vanishing=lambda: self._set_mode(MODE_DRAW_VANISHING),
            on_toggle_eraser=lambda: self._set_mode(MODE_ERASER),
            on_clear=self.overlay.clear_all,
            on_undo=self.overlay.undo,
            on_config=self.open_config,
            on_quit=self.quit
        )
        self.tray.show()

        # 5. Global Hotkey Listener
        self.hotkeys = HotkeyManager(self.config_mgr)
        self._wire_hotkeys()
        self.hotkeys.start()

        self.config_dialog: ConfigWindow = None

        if open_dashboard_on_start or self.config_mgr.get("system", "open_dashboard_at_start", True):
            self.open_config()

    def _setup_screens(self) -> None:
        """Adapts overlay geometry to full multi-monitor virtual desktop."""
        screen = QGuiApplication.primaryScreen()
        if screen:
            self.overlay.setGeometry(screen.virtualGeometry())
        self.overlay.show()

    def _position_hud(self) -> None:
        """Positions HUD pill at top-center of primary screen and elevates its z-order."""
        if not self.config_mgr.get("system", "floating_hud", True):
            return
        screen = QGuiApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            w = 560
            x = geom.x() + (geom.width() - w) // 2
            y = geom.y() + 15
            self.hud.move(x, y)
            self.hud.show()
            self.hud.raise_()
            self.hud.set_native_window_level()

    def _set_mode(self, target_mode: str) -> None:
        """Toggles drawing mode and updates visual state of HUD."""
        if self.overlay.mode == target_mode:
            self.overlay.set_mode(MODE_CLICK_THROUGH)
            self.hud.set_active_mode(MODE_CLICK_THROUGH)
        else:
            self.overlay.set_mode(target_mode)
            self.hud.set_active_mode(target_mode)

        # Ensure HUD is always visible and on top
        if self.config_mgr.get("system", "floating_hud", True):
            self.hud.show()
            self.hud.raise_()
            self.hud.set_native_window_level()

    def _wire_hotkeys(self) -> None:
        """Connects background thread hotkey signals to GUI methods."""
        self.hotkeys.sig_toggle_draw_fixed.connect(
            lambda: self._set_mode(MODE_DRAW_FIXED)
        )
        self.hotkeys.sig_toggle_draw_vanishing.connect(
            lambda: self._set_mode(MODE_DRAW_VANISHING)
        )
        self.hotkeys.sig_toggle_eraser.connect(
            lambda: self._set_mode(MODE_ERASER)
        )
        self.hotkeys.sig_clear_all.connect(self.overlay.clear_all)
        self.hotkeys.sig_undo.connect(self.overlay.undo)
        self.hotkeys.sig_open_config.connect(self.open_config)

    def open_config(self) -> None:
        """Opens or brings configuration dialog to focus."""
        if not self.config_dialog or not self.config_dialog.isVisible():
            self.config_dialog = ConfigWindow(self.config_mgr)
            self.config_dialog.finished.connect(self._on_config_closed)
            self.config_dialog.show()
            self.config_dialog.raise_()
            self.config_dialog.activateWindow()

    def _on_config_closed(self) -> None:
        """Applies configuration changes, toggles HUD, and reloads hotkeys."""
        self.hotkeys.reload()
        if self.config_mgr.get("system", "floating_hud", True):
            self._position_hud()
        else:
            self.hud.hide()
        self.overlay.update()

    def quit(self) -> None:
        """Shuts down application cleanly."""
        print("[PhoenixPen] Shutting down...")
        self.hotkeys.stop()
        self.overlay.close()
        self.hud.close()
        self.tray.hide()
        self.app.quit()

    def run(self) -> int:
        print("⚡ Phoenix Pen is running (HUD & System Tray active).")
        return self.app.exec()


def main() -> int:
    open_dash = "--open-dashboard" in sys.argv or "-d" in sys.argv
    app_controller = PhoenixPenApp(open_dashboard_on_start=open_dash)
    return app_controller.run()


if __name__ == "__main__":
    sys.exit(main())
