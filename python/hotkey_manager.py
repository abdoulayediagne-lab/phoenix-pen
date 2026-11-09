"""
Global Hotkey Manager for Phoenix Pen.
Listens to system-wide keyboard shortcuts and emits thread-safe PyQt signals.
Atlas Standard: < 250 lines.
"""

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
        self.listener: keyboard.GlobalHotKeys = None
        self._is_running = False

    def start(self) -> None:
        """Starts global hotkey listener."""
        if self._is_running:
            self.stop()

        hotkey_map = self._build_hotkey_map()
        try:
            self.listener = keyboard.GlobalHotKeys(hotkey_map)
            self.listener.start()
            self._is_running = True
            print(f"[HotkeyManager] Global hotkeys active: {list(hotkey_map.keys())}")
        except Exception as e:
            print(f"[HotkeyManager] Error registering hotkeys: {e}")

    def stop(self) -> None:
        """Stops global hotkey listener."""
        if self.listener and self._is_running:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None
            self._is_running = False

    def reload(self) -> None:
        """Reloads hotkeys from updated configuration."""
        self.stop()
        self.start()

    def _build_hotkey_map(self) -> Dict[str, Any]:
        """Maps configured shortcuts to Qt signal emissions."""
        hotkeys = self.config_mgr.get("hotkeys", {})
        mapping = {}

        def _safe_emit(signal: pyqtSignal):
            return lambda: signal.emit()

        if "draw_fixed" in hotkeys:
            mapping[hotkeys["draw_fixed"]] = _safe_emit(self.sig_toggle_draw_fixed)

        if "draw_vanishing" in hotkeys:
            mapping[hotkeys["draw_vanishing"]] = _safe_emit(self.sig_toggle_draw_vanishing)

        if "eraser" in hotkeys:
            mapping[hotkeys["eraser"]] = _safe_emit(self.sig_toggle_eraser)

        if "clear_all" in hotkeys:
            mapping[hotkeys["clear_all"]] = _safe_emit(self.sig_clear_all)

        if "undo" in hotkeys:
            mapping[hotkeys["undo"]] = _safe_emit(self.sig_undo)

        if "open_config" in hotkeys:
            mapping[hotkeys["open_config"]] = _safe_emit(self.sig_open_config)

        return mapping
