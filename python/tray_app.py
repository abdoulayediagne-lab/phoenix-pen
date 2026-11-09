"""
System Tray Manager for Phoenix Pen.
Maintains background presence, system notifications, and quick-action menu.
Atlas Standard: < 250 lines.
"""

import os
from typing import Callable
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


class TrayApp(QSystemTrayIcon):
    """System Tray icon with context actions and mode toggles."""

    def __init__(
        self,
        on_toggle_fixed: Callable[[], None],
        on_toggle_vanishing: Callable[[], None],
        on_toggle_eraser: Callable[[], None],
        on_clear: Callable[[], None],
        on_undo: Callable[[], None],
        on_config: Callable[[], None],
        on_quit: Callable[[], None]
    ) -> None:
        super().__init__()
        self.on_config = on_config

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))

        self.setToolTip("⚡ Phoenix Pen (Actif en arrière-plan)")
        self._build_menu(
            on_toggle_fixed,
            on_toggle_vanishing,
            on_toggle_eraser,
            on_clear,
            on_undo,
            on_config,
            on_quit
        )
        self.activated.connect(self._on_tray_activated)

    def _build_menu(
        self,
        on_fixed: Callable[[], None],
        on_vanishing: Callable[[], None],
        on_eraser: Callable[[], None],
        on_clear: Callable[[], None],
        on_undo: Callable[[], None],
        on_config: Callable[[], None],
        on_quit: Callable[[], None]
    ) -> None:
        menu = QMenu()

        title_act = QAction("⚡ Phoenix Pen v1.0", menu)
        title_act.setEnabled(False)
        menu.addAction(title_act)
        menu.addSeparator()

        self.act_fixed = QAction("🖋️ Encre Fixe (Alt+D)", menu)
        self.act_fixed.triggered.connect(on_fixed)
        menu.addAction(self.act_fixed)

        self.act_vanishing = QAction("⏳ Encre Éphémère (Alt+V)", menu)
        self.act_vanishing.triggered.connect(on_vanishing)
        menu.addAction(self.act_vanishing)

        self.act_eraser = QAction("🧹 Gomme (Alt+E)", menu)
        self.act_eraser.triggered.connect(on_eraser)
        menu.addAction(self.act_eraser)

        menu.addSeparator()

        act_undo = QAction("↩️ Annuler (Cmd+Z)", menu)
        act_undo.triggered.connect(on_undo)
        menu.addAction(act_undo)

        act_clear = QAction("🗑️ Tout Effacer (Alt+C)", menu)
        act_clear.triggered.connect(on_clear)
        menu.addAction(act_clear)

        menu.addSeparator()

        act_cfg = QAction("⚙️ Configuration...", menu)
        act_cfg.triggered.connect(on_config)
        menu.addAction(act_cfg)

        menu.addSeparator()

        act_quit = QAction("❌ Quitter Phoenix Pen", menu)
        act_quit.triggered.connect(on_quit)
        menu.addAction(act_quit)

        self.setContextMenu(menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger):
            self.on_config()
