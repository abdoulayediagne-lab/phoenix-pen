"""
Global Hotkey Manager for Phoenix Pen.
Listens to system-wide keyboard shortcuts and emits thread-safe PyQt signals.
Supports multi-modifier combinations and macOS Alt/Dead-Key character maps (◊, î, ê, ©, π).
Atlas Standard: < 250 lines.
"""

import sys
from typing import Any, Dict
from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal


class HotkeyManager(QObject):
    """Listens to global hotkeys via pynput and delivers Qt signals safely to the main loop."""

    sig_toggle_draw_fixed = pyqtSignal()
    sig_toggle_draw_vanishing = pyqtSignal()
    sig_toggle_eraser = pyqtSignal()
    sig_clear_all = pyqtSignal()
    sig_undo = pyqtSignal()
    sig_open_config = pyqtSignal()

    def __init__(self, config_mgr: Any) -> None:
        super().__init__()
        self.config_mgr = config_mgr
        self.hotkey_listener: keyboard.GlobalHotKeys = None
        self.raw_listener: keyboard.Listener = None
        self._is_running = False

        # Modifier states
        self.alt_down = False
        self.ctrl_down = False
        self.cmd_down = False
        self.shift_down = False

    def start(self) -> None:
        """Starts global hotkey listener with dual GlobalHotKeys & dead-key interceptor."""
        if self._is_running:
            self.stop()

        hotkey_map = self._build_hotkey_map()
        try:
            self.hotkey_listener = keyboard.GlobalHotKeys(hotkey_map)
            self.hotkey_listener.start()

            # Secondary listener for macOS Dead-Keys and direct combinations
            self.raw_listener = keyboard.Listener(
                on_press=self._on_raw_press,
                on_release=self._on_raw_release
            )
            self.raw_listener.start()

            self._is_running = True
            print(f"[HotkeyManager] Global listeners active (macOS & Win ready).")
        except Exception as e:
            print(f"[HotkeyManager] Error registering hotkeys: {e}")

    def stop(self) -> None:
        """Stops listeners cleanly."""
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
            self.hotkey_listener = None

        if self.raw_listener:
            try:
                self.raw_listener.stop()
            except Exception:
                pass
            self.raw_listener = None

        self._is_running = False

    def reload(self) -> None:
        """Reloads hotkeys from configuration."""
        self.stop()
        self.start()

    def _on_raw_press(self, key: Any) -> None:
        """Tracks modifiers and intercepts macOS dead-keys (◊, î, ê, ©, π)."""
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

        # 1. Option + key (macOS French keyboard creates ◊ for v, î for d, ê for e, © for c, π for p)
        if self.alt_down and not self.ctrl_down and not self.cmd_down:
            if char in ('v', '◊'):
                self.sig_toggle_draw_vanishing.emit()
            elif char in ('d', 'î'):
                self.sig_toggle_draw_fixed.emit()
            elif char in ('e', 'ê'):
                self.sig_toggle_eraser.emit()
            elif char in ('c', '©'):
                self.sig_clear_all.emit()
            elif char in ('p', 'π'):
                self.sig_open_config.emit()

        # 2. Ctrl + Option + key (Clean non-typing shortcuts)
        elif self.ctrl_down and self.alt_down:
            if char in ('v', '◊'):
                self.sig_toggle_draw_vanishing.emit()
            elif char in ('d', 'î'):
                self.sig_toggle_draw_fixed.emit()
            elif char in ('e', 'ê'):
                self.sig_toggle_eraser.emit()
            elif char in ('c', '©'):
                self.sig_clear_all.emit()
            elif char in ('p', 'π'):
                self.sig_open_config.emit()

        # 3. Cmd+Z (macOS) or Ctrl+Z (Windows)
        elif (self.cmd_down or self.ctrl_down) and char == 'z':
            self.sig_undo.emit()

    def _on_raw_release(self, key: Any) -> None:
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            self.alt_down = False
        elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self.ctrl_down = False
        elif key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            self.cmd_down = False
        elif key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self.shift_down = False

    def _build_hotkey_map(self) -> Dict[str, Any]:
        """Maps structured hotkeys for multi-platform support."""
        mapping = {
            "<ctrl>+<alt>+d": lambda: self.sig_toggle_draw_fixed.emit(),
            "<ctrl>+<alt>+v": lambda: self.sig_toggle_draw_vanishing.emit(),
            "<ctrl>+<alt>+e": lambda: self.sig_toggle_eraser.emit(),
            "<ctrl>+<alt>+c": lambda: self.sig_clear_all.emit(),
            "<ctrl>+<alt>+p": lambda: self.sig_open_config.emit(),
            "<cmd>+<shift>+d": lambda: self.sig_toggle_draw_fixed.emit(),
            "<cmd>+<shift>+v": lambda: self.sig_toggle_draw_vanishing.emit(),
            "<cmd>+<shift>+e": lambda: self.sig_toggle_eraser.emit(),
            "<cmd>+<shift>+c": lambda: self.sig_clear_all.emit(),
            "<cmd>+<shift>+p": lambda: self.sig_open_config.emit(),
        }
        return mapping
