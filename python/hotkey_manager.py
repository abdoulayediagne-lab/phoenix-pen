"""
Global Hotkey Manager for Phoenix Pen.
Listens to system-wide keyboard shortcuts and emits thread-safe PyQt signals.
Preloads macOS accessibility bindings and provides layout-agnostic character mapping.
Atlas Standard: < 250 lines.
"""

import sys
from typing import Any
from PyQt6.QtCore import QObject, pyqtSignal

# Preload PyObjC attributes on main thread to avoid subthread lazy-import race conditions
if sys.platform == "darwin":
    try:
        import ApplicationServices, HIServices
        _ = getattr(HIServices, "AXIsProcessTrusted", None)
        _ = getattr(ApplicationServices, "AXIsProcessTrusted", None)
    except Exception:
        pass

from pynput import keyboard


class HotkeyManager(QObject):
    """Listens to global hotkeys and delivers Qt signals safely to the main loop."""

    sig_toggle_draw_fixed = pyqtSignal()
    sig_toggle_draw_vanishing = pyqtSignal()
    sig_toggle_eraser = pyqtSignal()
    sig_clear_all = pyqtSignal()
    sig_undo = pyqtSignal()
    sig_open_config = pyqtSignal()

    def __init__(self, config_mgr: Any) -> None:
        super().__init__()
        self.config_mgr = config_mgr
        self.listener: keyboard.Listener = None
        self._is_running = False

        # Modifiers tracking
        self.alt_down = False
        self.ctrl_down = False
        self.cmd_down = False
        self.shift_down = False

    def start(self) -> None:
        """Starts single robust event listener."""
        if self._is_running:
            self.stop()

        try:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.daemon = True
            self.listener.start()
            self._is_running = True
            print("[HotkeyManager] Global hotkey listener active.")
        except Exception as e:
            print(f"[HotkeyManager] Error starting listener: {e}")

    def stop(self) -> None:
        """Stops listener cleanly."""
        if self.listener and self._is_running:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None
        self._is_running = False

    def reload(self) -> None:
        self.stop()
        self.start()

    def _on_press(self, key: Any) -> None:
        """Tracks modifiers and triggers actions on key press."""
        # Track modifier keys
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            self.alt_down = True
            return
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self.ctrl_down = True
            return
        if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            self.cmd_down = True
            return
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self.shift_down = True
            return

        char = getattr(key, 'char', None)
        if not char:
            return

        char_lower = char.lower()

        # Matches: Alt+Key OR Ctrl+Alt+Key OR Cmd+Shift+Key
        is_mod_match = (
            self.alt_down
            or (self.ctrl_down and self.alt_down)
            or (self.cmd_down and self.shift_down)
        )

        if is_mod_match:
            # Encre Éphémère (v or macOS dead-key ◊)
            if char_lower == 'v' or char == '◊':
                self.sig_toggle_draw_vanishing.emit()
            # Encre Fixe (d or macOS dead-key î)
            elif char_lower == 'd' or char == 'î':
                self.sig_toggle_draw_fixed.emit()
            # Gomme (e or macOS dead-key ê)
            elif char_lower == 'e' or char == 'ê':
                self.sig_toggle_eraser.emit()
            # Tout Effacer (c or macOS dead-key ©)
            elif char_lower == 'c' or char == '©':
                self.sig_clear_all.emit()
            # Dashboard / Configuration (p or macOS dead-key π)
            elif char_lower == 'p' or char == 'π':
                self.sig_open_config.emit()

        # Undo: Cmd+Z or Ctrl+Z
        if (self.cmd_down or self.ctrl_down) and char_lower == 'z':
            self.sig_undo.emit()

    def _on_release(self, key: Any) -> None:
        """Releases modifier keys."""
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            self.alt_down = False
        elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self.ctrl_down = False
        elif key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            self.cmd_down = False
        elif key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self.shift_down = False
