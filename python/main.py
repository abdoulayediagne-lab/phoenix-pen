"""
Main Application Controller for Phoenix Pen.
Orchestrates Overlay, System Tray, Hotkeys, and Configuration dialog.
Atlas Standard: < 250 lines.
"""

import sys
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication

from config_gui import ConfigWindow
from config_manager import ConfigManager
from hotkey_manager import HotkeyManager
from overlay_window import (
    MODE_DRAW_FIXED, MODE_DRAW_VANISHING, MODE_ERASER, OverlayWindow
)
from tray_app import TrayApp


class PhoenixPenApp:
    """Core controller connecting all subsystems together."""

    def __init__(self) -> None:
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 1. Config Manager
        self.config_mgr = ConfigManager()

        # 2. Translucent Fullscreen Overlay
        self.overlay = OverlayWindow(self.config_mgr)
        self._setup_screens()

        # 3. System Tray Icon
        self.tray = TrayApp(
            on_toggle_fixed=lambda: self.overlay.toggle_mode(MODE_DRAW_FIXED),
            on_toggle_vanishing=lambda: self.overlay.toggle_mode(MODE_DRAW_VANISHING),
            on_toggle_eraser=lambda: self.overlay.toggle_mode(MODE_ERASER),
            on_clear=self.overlay.clear_all,
            on_undo=self.overlay.undo,
            on_config=self.open_config,
            on_quit=self.quit
        )
        self.tray.show()

        # 4. Global Hotkey Listener
        self.hotkeys = HotkeyManager(self.config_mgr)
        self._wire_hotkeys()
        self.hotkeys.start()

        # Config dialog reference
        self.config_dialog: ConfigWindow = None

    def _setup_screens(self) -> None:
        """Adapts overlay geometry to full multi-monitor virtual desktop."""
        screen = QGuiApplication.primaryScreen()
        if screen:
            geom = screen.virtualGeometry()
            self.overlay.setGeometry(geom)
        self.overlay.show()

    def _wire_hotkeys(self) -> None:
        """Connects background thread hotkey signals to GUI methods."""
        self.hotkeys.sig_toggle_draw_fixed.connect(
            lambda: self.overlay.toggle_mode(MODE_DRAW_FIXED)
        )
        self.hotkeys.sig_toggle_draw_vanishing.connect(
            lambda: self.overlay.toggle_mode(MODE_DRAW_VANISHING)
        )
        self.hotkeys.sig_toggle_eraser.connect(
            lambda: self.overlay.toggle_mode(MODE_ERASER)
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
        """Applies configuration changes and reloads hotkeys."""
        self.hotkeys.reload()
        self.overlay.update()

    def quit(self) -> None:
        """Shuts down application cleanly."""
        print("[PhoenixPen] Shutting down...")
        self.hotkeys.stop()
        self.overlay.close()
        self.tray.hide()
        self.app.quit()

    def run(self) -> int:
        """Runs the Qt event loop."""
        print("⚡ Phoenix Pen is running in background (System Tray active).")
        return self.app.exec()


def main() -> int:
    app_controller = PhoenixPenApp()
    return app_controller.run()


if __name__ == "__main__":
    sys.exit(main())
