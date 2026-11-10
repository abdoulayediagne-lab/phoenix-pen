"""
Main Application Controller for Phoenix Pen.
Orchestrates Multi-Screen Overlays, System Tray, Floating HUD, Hotkeys, and Dashboard dialog.
Atlas Standard: < 250 lines.
"""

import sys
from typing import List
from PyQt6.QtGui import QCursor, QGuiApplication
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
    """Core controller connecting all subsystems across all physical screens."""

    def __init__(self, open_dashboard_on_start: bool = False) -> None:
        if sys.platform == "darwin":
            try:
                import AppKit
                AppKit.NSApplication.sharedApplication().setActivationPolicy_(
                    AppKit.NSApplicationActivationPolicyAccessory
                )
            except Exception: pass

        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 1. Config Manager
        self.config_mgr = ConfigManager()

        # 2. Translucent Fullscreen Overlays (Multi-Screen Matrix)
        self.overlays: List[OverlayWindow] = []
        self._setup_screens()

        # 3. Floating Quick Toolbar (HUD)
        self.hud = FloatingHUD(
            on_toggle_fixed=lambda: self._set_mode(MODE_DRAW_FIXED),
            on_toggle_vanishing=lambda: self._set_mode(MODE_DRAW_VANISHING),
            on_toggle_eraser=lambda: self._set_mode(MODE_ERASER),
            on_clear=self.clear_all,
            on_undo=self.undo,
            on_dashboard=self.open_config,
            config_mgr=self.config_mgr
        )
        self._position_hud()

        # 4. System Tray Icon
        self.tray = TrayApp(
            on_toggle_fixed=lambda: self._set_mode(MODE_DRAW_FIXED),
            on_toggle_vanishing=lambda: self._set_mode(MODE_DRAW_VANISHING),
            on_toggle_eraser=lambda: self._set_mode(MODE_ERASER),
            on_clear=self.clear_all,
            on_undo=self.undo,
            on_config=self.open_config,
            on_quit=self.quit
        )
        self.tray.show()

        # 5. Global Hotkey Listener
        self.hotkeys = HotkeyManager(self.config_mgr)
        self.hotkeys.is_active_fn = lambda: any(ov.mode != MODE_CLICK_THROUGH for ov in self.overlays)
        self._wire_hotkeys()
        self.hotkeys.start()

        self.config_dialog: ConfigWindow = None
        if open_dashboard_on_start or self.config_mgr.get("system", "open_dashboard_at_start", False):
            self.open_config()

    @property
    def overlay(self) -> OverlayWindow:
        """Legacy helper pointing to primary overlay."""
        return self.overlays[0] if self.overlays else None

    def _setup_screens(self) -> None:
        """Creates fullscreen overlay for EACH physical monitor."""
        for ov in self.overlays:
            try: ov.close()
            except Exception: pass
        self.overlays.clear()

        for s in QGuiApplication.screens():
            ov = OverlayWindow(self.config_mgr, target_screen=s)
            ov.setGeometry(s.geometry())
            ov.show()
            ov._adapt_to_active_screen()
            ov._set_native_click_through(True)
            self.overlays.append(ov)

    def _position_hud(self) -> None:
        """Positions HUD pill cleanly below Phoenix Voice (y=112) with zero overlap."""
        if not self.config_mgr.get("system", "floating_hud", True):
            return
        screen = QGuiApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            w = 560
            x = geom.x() + (geom.width() - w) // 2
            y = 112  # Perfectly spaced below Phoenix Voice (which sits at y=55..99)
            self.hud.move(x, y)
            self.hud.show()
            self.hud.raise_()
            self.hud.set_native_window_level()

    def _set_mode(self, target_mode: str) -> None:
        """Toggles drawing mode across ALL physical screens simultaneously."""
        if self.config_dialog and self.config_dialog.isVisible():
            self.config_dialog.hide()

        cur_mode = self.overlays[0].mode if self.overlays else MODE_CLICK_THROUGH
        new_mode = MODE_CLICK_THROUGH if cur_mode == target_mode else target_mode
        cur_screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()

        for ov in self.overlays:
            ov.set_mode(new_mode)
            if new_mode != MODE_CLICK_THROUGH and ov.target_screen == cur_screen:
                ov.focus_active()

        self.hud.set_active_mode(new_mode)

        if self.config_mgr.get("system", "floating_hud", True):
            self.hud.show()
            self.hud.raise_()
            self.hud.set_native_window_level()

    def undo(self) -> None:
        """Undoes the most recent stroke across all active screen overlays."""
        for ov in reversed(self.overlays):
            if ov.permanent_strokes or ov.fade_manager.strokes:
                ov.undo()
                return
        if self.overlays:
            self.overlays[0].undo()

    def clear_all(self) -> None:
        """Clears all strokes across all screens."""
        for ov in self.overlays:
            ov.clear_all()

    def _wire_hotkeys(self) -> None:
        """Connects hotkey signals to application actions."""
        self.hotkeys.sig_toggle_draw_fixed.connect(lambda: self._set_mode(MODE_DRAW_FIXED))
        self.hotkeys.sig_toggle_draw_vanishing.connect(lambda: self._set_mode(MODE_DRAW_VANISHING))
        self.hotkeys.sig_toggle_eraser.connect(lambda: self._set_mode(MODE_ERASER))
        self.hotkeys.sig_clear_all.connect(self.clear_all)
        self.hotkeys.sig_undo.connect(self.undo)
        self.hotkeys.sig_open_config.connect(self.open_config)
        self.hotkeys.sig_escape.connect(self._on_escape)

    def _on_escape(self) -> None:
        """Escape cancels drawing mode and returns to click-through navigation."""
        if any(ov.mode != MODE_CLICK_THROUGH for ov in self.overlays):
            self._set_mode(MODE_CLICK_THROUGH)

    def open_config(self) -> None:
        if any(ov.mode != MODE_CLICK_THROUGH for ov in self.overlays):
            self._set_mode(MODE_CLICK_THROUGH)
        if not self.config_dialog:
            self.config_dialog = ConfigWindow(self.config_mgr)
            self.config_dialog.finished.connect(self._on_config_closed)
        self.config_dialog.show()
        self.config_dialog.raise_()
        self.config_dialog.activateWindow()

    def _on_config_closed(self) -> None:
        if self.config_mgr.get("system", "floating_hud", True):
            self._position_hud()
        else:
            self.hud.hide()
        for ov in self.overlays:
            ov.update()

    def quit(self) -> None:
        print("[PhoenixPen] Shutting down...")
        self.hotkeys.stop()
        for ov in self.overlays:
            ov.close()
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
