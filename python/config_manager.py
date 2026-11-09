"""
Configuration Manager for Phoenix Pen.
Handles loading, saving, defaults, and hot-reloading of settings.
Atlas Standard: < 250 lines.
"""

import json
import os
from typing import Any, Callable, Dict, List

DEFAULT_CONFIG: Dict[str, Any] = {
    "hotkeys": {
        "draw_fixed": "<cmd>+d",
        "draw_vanishing": "<alt>+v",
        "eraser": "<alt>+e",
        "clear_all": "<alt>+c",
        "undo": "<cmd>+z",
        "open_config": "<alt>+p"
    },
    "drawing": {
        "stroke_width": 4,
        "eraser_width": 24,
        "active_color": "#00FF87",
        "neon_glow": True,
        "neon_intensity": 0.75,
        "vanishing_duration": 2.0,
        "fadeout_speed": 0.6,
        "shape_recognition": True,
        "shape_confidence_threshold": 0.88,
        "cursor_dot": True,
        "cursor_dot_size": 10
    },
    "palette_essential": [
        "#00FF87", "#00A859", "#00E5FF", "#2979FF",
        "#FF3D00", "#FF1493", "#FFEA00", "#A855F7", "#FFFFFF"
    ],
    "palette_metallic": [
        "#FFD700", "#E5A93C", "#C59B27", "#E2E8F0",
        "#CBD5E1", "#38BDF8", "#F472B6", "#FB923C", "#10B981"
    ],
    "palette": [
        "#00FF87", "#00A859", "#9B6E28", "#00E5FF",
        "#2979FF", "#E0E0E0", "#FF1493", "#FFEA00", "#FF3D00"
    ],
    "system": {
        "start_at_login": False,
        "fps_limit": 60,
        "floating_hud": True,
        "open_dashboard_at_start": False
    }
}


class ConfigManager:
    """Manages application settings persisted in config/config.json."""

    def __init__(self, config_path: str = None) -> None:
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_path = os.path.join(base_dir, "config", "config.json")
            self.example_path = os.path.join(base_dir, "config", "config.example.json")
        else:
            self.config_path = config_path
            self.example_path = config_path + ".example"

        self.config: Dict[str, Any] = {}
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self.load()

    def load(self) -> Dict[str, Any]:
        """Loads configuration from file or creates it from defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.config = self._merge_defaults(loaded, DEFAULT_CONFIG)
                    return self.config
            except Exception as e:
                print(f"[ConfigManager] Error reading config: {e}. Falling back to default.")

        self.config = json.loads(json.dumps(DEFAULT_CONFIG))
        self.save()
        return self.config

    def _merge_defaults(self, current: Dict[str, Any], default: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merges defaults for missing keys."""
        res = json.loads(json.dumps(default))
        for key, val in current.items():
            if isinstance(val, dict) and key in res and isinstance(res[key], dict):
                res[key] = self._merge_defaults(val, res[key])
            else:
                res[key] = val
        return res

    def save(self) -> bool:
        """Saves current configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self._notify_listeners()
            return True
        except Exception as e:
            print(f"[ConfigManager] Failed to save config: {e}")
            return False

    def get(self, section: str, key: Any = None, default: Any = None) -> Any:
        """Gets a configuration value. Supports get('section', 'key', default) or get('root_key', default)."""
        if key is None or not isinstance(key, str):
            fallback = key if key is not None else default
            return self.config.get(section, fallback)

        sec_val = self.config.get(section)
        if isinstance(sec_val, dict):
            return sec_val.get(key, default)
        return default

    def set(self, section: str, key: str, value: Any) -> None:
        """Sets a configuration value and saves."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()

    def add_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Registers a listener called when config is updated."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def _notify_listeners(self) -> None:
        for cb in self._listeners:
            try:
                cb(self.config)
            except Exception as e:
                print(f"[ConfigManager] Listener error: {e}")
