"""
Global Hotkey Manager for Phoenix Pen.
Listens to system-wide shortcuts with key-repeat guard and macOS native event swallowing.
Atlas Standard: < 250 lines.
"""

import sys
from typing import Any, Set
from PyQt6.QtCore import QObject, pyqtSignal

if sys.platform == "darwin":
    try:
        import ApplicationServices, HIServices, Quartz
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
        self._keys_pressed: Set[Any] = set()
        self.is_active_fn: Any = None

    def _swallow_darwin_hotkeys(self, ev_type: Any, event: Any) -> Any:
        """Swallows hotkeys on macOS so background apps do not intercept them."""
        if sys.platform != "darwin":
            return event
        try:
            import Quartz
            flags = Quartz.CGEventGetFlags(event)
            has_cmd = bool(flags & Quartz.kCGEventFlagMaskCommand)
            has_shift = bool(flags & Quartz.kCGEventFlagMaskShift)
            has_alt = bool(flags & Quartz.kCGEventFlagMaskAlternate)
            has_ctrl = bool(flags & Quartz.kCGEventFlagMaskControl)
            kc = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
            # 2: D, 9: V, 14: E, 8: C, 35: P, 6: Z, 13: W (Z on AZERTY)
            is_active = bool(self.is_active_fn and self.is_active_fn())
            # When drawing is active, swallow Cmd+Z / Ctrl+Z so editors never lose code!
            if is_active and (has_cmd or has_ctrl or has_alt) and kc in (6, 13):
                return None
            if ((has_alt and not has_cmd) or (has_cmd and has_shift)) and kc in (6, 13):
                return None
            # Cmd+D or Option+D or Cmd+Shift+D for drawing (kc 2)
            if (has_cmd or has_alt) and kc == 2:
                return None
            # Cmd+E or Option+E or Cmd+Shift+E for eraser (kc 14)
            if (has_cmd or has_alt) and kc == 14:
                return None
            # Only swallow Option+Key or Cmd+Shift+Key for V (9), C (8), P (35) — NEVER plain Cmd+C/V/P!
            if ((has_alt and not has_cmd) or (has_cmd and has_shift)) and kc in (9, 8, 35):
                return None
        except Exception:
            pass
        return event

    def start(self) -> None:
        if self._is_running:
            self.stop()
        try:
            kwargs = {
                "on_press": self._on_press,
                "on_release": self._on_release
            }
            if sys.platform == "darwin":
                kwargs["darwin_intercept"] = self._swallow_darwin_hotkeys

            self.listener = keyboard.Listener(**kwargs)
            self.listener.daemon = True
            self.listener.start()
            self._is_running = True
            print("[HotkeyManager] Global hotkey listener active (event-swallowing enabled).")
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
        self._keys_pressed.clear()

    def reload(self) -> None:
        self.stop()
        self.start()

    def _on_press(self, key: Any) -> None:
        if key == keyboard.Key.esc:
            self.sig_escape.emit()
            return

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

        vk = getattr(key, 'vk', None)
        char = getattr(key, 'char', None)
        char_lower = char.lower() if char else ''
        key_id = (vk, char_lower)

        # Key-repeat guard: only trigger ONCE per physical press down
        if key_id in self._keys_pressed:
            return
        self._keys_pressed.add(key_id)

        is_d = (vk == 2) or (char_lower == 'd') or (char == 'î')
        is_v = (vk == 9) or (char_lower == 'v') or (char == '◊')
        is_e = (vk == 14) or (char_lower == 'e') or (char == 'ê')
        is_c = (vk == 8) or (char_lower == 'c') or (char == '©')
        is_p = (vk == 35) or (char_lower == 'p') or (char == 'π')
        is_z = (vk in (6, 13)) or (char_lower == 'z')

        # Encre Fixe: Cmd+D OR Cmd+Shift+D OR Option+D
        if is_d and ((self.cmd_down and self.shift_down) or self.cmd_down or self.alt_down):
            self.sig_toggle_draw_fixed.emit()

        # Encre Éphémère: Cmd+Shift+V OR Option+V (never plain Cmd+V which is paste)
        elif is_v and ((self.cmd_down and self.shift_down) or (self.alt_down and not self.cmd_down)):
            self.sig_toggle_draw_vanishing.emit()

        # Gomme: Cmd+Shift+E OR Option+E OR Cmd+E
        elif is_e and ((self.cmd_down and self.shift_down) or self.cmd_down or self.alt_down):
            self.sig_toggle_eraser.emit()

        # Tout Effacer: Cmd+Shift+C OR Option+C (never plain Cmd+C which is copy)
        elif is_c and ((self.cmd_down and self.shift_down) or (self.alt_down and not self.cmd_down)):
            self.sig_clear_all.emit()

        # Config: Cmd+Shift+P OR Option+P (never plain Cmd+P which is print)
        elif is_p and ((self.cmd_down and self.shift_down) or (self.alt_down and not self.cmd_down)):
            self.sig_open_config.emit()

        # Undo: Cmd+Z OR Ctrl+Z OR Option+Z OR Cmd+Shift+Z
        elif is_z:
            if self.cmd_down or self.ctrl_down or self.alt_down:
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

        vk = getattr(key, 'vk', None)
        char = getattr(key, 'char', None)
        char_lower = char.lower() if char else ''
        self._keys_pressed.discard((vk, char_lower))
