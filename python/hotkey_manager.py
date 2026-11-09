"""
Global Hotkey Manager for Phoenix Pen.
Listens to system-wide keyboard shortcuts and emits thread-safe PyQt signals.
Supports multi-modifier combinations, virtual keycodes (vk), and dead-keys on macOS & Windows.
Atlas Standard: < 250 lines.
"""

import sys
from typing import Any
from PyQt6.QtCore import QObject, pyqtSignal

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
    sig_escape = pyqtSignal()

    def __init__(self, config_mgr: Any) -> None:
        super().__init__()
        self.config_mgr = config_mgr
        self.listener: keyboard.Listener = None
        self._is_running = False

        self.alt_down = False
        self.ctrl_down = False
        self.cmd_down = False
        self.shift_down = False

    def start(self) -> None:
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
        # Escape cancels drawing/eraser mode
        if key == keyboard.Key.esc:
            self.sig_escape.emit()
            return

        # 1. Track modifier keys
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

        # 2. Extract hardware vk & unicode char
        vk = getattr(key, 'vk', None)
        char = getattr(key, 'char', None)
        char_lower = char.lower() if char else ''

        is_d = (vk == 2) or (char_lower == 'd') or (char == 'î')
        is_v = (vk == 9) or (char_lower == 'v') or (char == '◊')
        is_e = (vk == 14) or (char_lower == 'e') or (char == 'ê')
        is_c = (vk == 8) or (char_lower == 'c') or (char == '©')
        is_p = (vk == 35) or (char_lower == 'p') or (char == 'π')
        is_z = (vk in (6, 13)) or (char_lower == 'z')

        # 3. Trigger Actions Based on Active Modifiers
        if is_d:
            if (self.cmd_down and self.shift_down) or self.cmd_down or self.alt_down:
                self.sig_toggle_draw_fixed.emit()

        elif is_v:
            if (self.cmd_down and self.shift_down) or self.alt_down or (self.ctrl_down and self.alt_down):
                self.sig_toggle_draw_vanishing.emit()

        elif is_e:
            if (self.cmd_down and self.shift_down) or self.cmd_down or self.alt_down:
                self.sig_toggle_eraser.emit()

        elif is_c:
            if (self.cmd_down and self.shift_down) or self.alt_down or (self.ctrl_down and self.alt_down):
                self.sig_clear_all.emit()

        elif is_p:
            if (self.cmd_down and self.shift_down) or self.cmd_down or self.alt_down:
                self.sig_open_config.emit()

        elif is_z:
            if self.cmd_down or self.ctrl_down:
                self.sig_undo.emit()

    def _on_release(self, key: Any) -> None:
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            self.alt_down = False
        elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self.ctrl_down = False
        elif key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            self.cmd_down = False
        elif key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self.shift_down = False
