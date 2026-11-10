"""
Main Application Controller for Phoenix Pen.
Orchestrates Multi-Screen Overlays, System Tray, Floating HUD, Hotkeys, and Dashboard dialog.
Atlas Standard: < 250 lines.
"""

import fcntl
import os
import signal
import subprocess
import sys
import time
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

_LOCK_FILE = "/tmp/phoenix_pen.lock"
_PID_FILE = "/tmp/phoenix_pen.pid"
_lock_fd = None


def _enforce_single_instance() -> None:
    """Ensures only ONE instance of Phoenix Pen runs at any time."""
    global _lock_fd
    my_pid = os.getpid()
    if os.path.exists(_PID_FILE):
        try:
            with open(_PID_FILE, "r") as f: old_pid = int(f.read().strip())
            if old_pid != my_pid: os.kill(old_pid, signal.SIGKILL)
        except Exception: pass
    try:
        out = subprocess.check_output(["pgrep", "-f", "phoenix-pen.*main\\.py"], text=True)
        for line in out.strip().splitlines():
            if int(line.strip()) != my_pid: os.kill(int(line.strip()), signal.SIGKILL)
    except Exception: pass
    try:
        _lock_fd = open(_LOCK_FILE, "w"); fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with open(_PID_FILE, "w") as f: f.write(str(my_pid))
    except (IOError, OSError): sys.exit(0)


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
            lambda: self._set_mode(MODE_DRAW_FIXED), lambda: self._set_mode(MODE_DRAW_VANISHING),
            lambda: self._set_mode(MODE_ERASER), self.clear_all, self.undo, self.open_config,
            self.config_mgr, self.toggle_hud
        )
        self._position_hud()

        # 4. System Tray Icon
        self.tray = TrayApp(
            lambda: self._set_mode(MODE_DRAW_FIXED), lambda: self._set_mode(MODE_DRAW_VANISHING),
            lambda: self._set_mode(MODE_ERASER), self.clear_all, self.undo, self.open_config,
            self.quit, self.toggle_hud, self.trigger_update
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
        self.hotkeys.sig_toggle_hud.connect(self.toggle_hud)
        self.hotkeys.sig_escape.connect(self._on_escape)

    def toggle_hud(self) -> None:
        """Toggles HUD visibility on/off."""
        if self.hud.isVisible(): self.hud.hide()
        else: self.hud.show(); self.hud.raise_(); self.hud.set_native_window_level()

    def trigger_update(self) -> None:
        """Opens dashboard updater section directly."""
        self.open_config()
        if self.config_dialog and hasattr(self.config_dialog, "updater_card"):
            self.config_dialog.updater_card.check_updates()

    def _on_escape(self) -> None:
        """Escape cancels drawing mode and returns to click-through navigation."""
        if any(ov.mode != MODE_CLICK_THROUGH for ov in self.overlays):
            self._set_mode(MODE_CLICK_THROUGH)

    def open_config(self) -> None:
        if any(ov.mode != MODE_CLICK_THROUGH for ov in self.overlays):
            self._set_mode(MODE_CLICK_THROUGH)
        if self.config_dialog and self.config_dialog.isVisible():
            self.config_dialog.close(); self.config_dialog = None
            return
        if self.config_dialog:
            try: self.config_dialog.close()
            except Exception: pass
            self.config_dialog = None
        self.config_dialog = ConfigWindow(self.config_mgr)
        self.config_dialog.finished.connect(self._on_config_closed)
        cur = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if cur:
            g = cur.availableGeometry()
            self.config_dialog.move(g.x() + max(20, (g.width() - 580) // 2), g.y() + max(40, (g.height() - 790) // 2))
        self.config_dialog.show(); self.config_dialog.raise_(); self.config_dialog.activateWindow()
        if sys.platform == "darwin":
            try:
                import AppKit
                AppKit.NSApp.activateIgnoringOtherApps_(True)
            except Exception: pass

    def _on_config_closed(self) -> None:
        self.config_dialog = None
        if self.config_mgr.get("system", "floating_hud", True): self._position_hud()
        else: self.hud.hide()
        for ov in self.overlays: ov.update()

    def quit(self) -> None:
        print("[PhoenixPen] Shutting down...")
        self.hotkeys.stop()
        for ov in self.overlays: ov.close()
        self.hud.close(); self.tray.hide()
        try: os.remove(_PID_FILE)
        except OSError: pass
        self.app.quit()

    def run(self) -> int:
        print("⚡ Phoenix Pen is running (HUD & System Tray active).")
        return self.app.exec()


def main() -> int:
    _enforce_single_instance()
    open_dash = "--open-dashboard" in sys.argv or "-d" in sys.argv
    app_controller = PhoenixPenApp(open_dashboard_on_start=open_dash)
    return app_controller.run()


if __name__ == "__main__":
    sys.exit(main())
