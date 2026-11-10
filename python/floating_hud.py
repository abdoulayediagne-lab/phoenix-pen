"""
Floating HUD Pill / Quick Toolbar for Phoenix Pen.
Draggable, always-on-top, semi-translucent bar with 1-click tool toggles and Dashboard button.
Atlas Standard: < 250 lines.
"""

import sys
from typing import Any, Callable
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton


class FloatingHUD(QFrame):
    """Sleek floating pill widget providing visual tool buttons and Dashboard launcher."""

    def __init__(
        self,
        on_toggle_fixed: Callable[[], None],
        on_toggle_vanishing: Callable[[], None],
        on_toggle_eraser: Callable[[], None],
        on_clear: Callable[[], None],
        on_undo: Callable[[], None],
        on_dashboard: Callable[[], None],
        config_mgr: Any
    ) -> None:
        super().__init__()
        self.config_mgr = config_mgr
        self.drag_position = QPoint()

        # Callbacks
        self.on_toggle_fixed = on_toggle_fixed
        self.on_toggle_vanishing = on_toggle_vanishing
        self.on_toggle_eraser = on_toggle_eraser
        self.on_clear = on_clear
        self.on_undo = on_undo
        self.on_dashboard = on_dashboard

        self._init_window()
        self._init_ui()

    def _init_window(self) -> None:
        """Configures floating tool window properties using Tool window type."""
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedHeight(48)
        self.setFixedWidth(560)
        self.setStyleSheet("""
            FloatingHUD {
                background-color: rgba(13, 15, 18, 245);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 24px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 16);
                color: #E5E7EB;
                border: 1px solid rgba(255, 255, 255, 22);
                border-radius: 16px;
                padding: 4px 12px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 36);
                border: 1px solid rgba(255, 255, 255, 50);
                color: #FFFFFF;
            }
            QPushButton[active="true"] {
                background-color: #00A859;
                border: 1.5px solid #00FF87;
                color: #FFFFFF;
            }
            QPushButton#dashBtn {
                background-color: rgba(255, 255, 255, 22);
                color: #E5E7EB;
                border: 1px solid rgba(255, 255, 255, 30);
            }
            QPushButton#dashBtn:hover {
                background-color: rgba(255, 255, 255, 45);
                border: 1px solid rgba(255, 255, 255, 60);
                color: #FFFFFF;
            }
        """)

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
        self.set_native_window_level()

    def set_native_window_level(self) -> None:
        """Forces macOS Window Level to Status bar and joins all spaces."""
        if sys.platform == "darwin":
            try:
                import AppKit, objc
                view = objc.objc_object(c_void_p=int(self.winId()))
                nswin = view.window()
                if nswin is not None:
                    behavior = (
                        AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                        | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
                        | AppKit.NSWindowCollectionBehaviorStationary
                        | AppKit.NSWindowCollectionBehaviorIgnoresCycle
                    )
                    nswin.setCollectionBehavior_(behavior)
                    if hasattr(nswin, "setStyleMask_"):
                        nswin.setStyleMask_(nswin.styleMask() | AppKit.NSWindowStyleMaskNonactivatingPanel)
                    if hasattr(nswin, "setHidesOnDeactivate_"): nswin.setHidesOnDeactivate_(False)
                    if hasattr(nswin, "setFloatingPanel_"): nswin.setFloatingPanel_(True)
                    if hasattr(nswin, "setBecomesKeyOnlyIfNeeded_"): nswin.setBecomesKeyOnlyIfNeeded_(False)
                    nswin.setLevel_(AppKit.NSStatusWindowLevel)
                    nswin.orderFrontRegardless()
            except Exception as e:
                print(f"[FloatingHUD] macOS level error: {e}")

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)

        # Drag handle / Brand logo
        self.brand_lbl = QLabel("⚡")
        self.brand_lbl.setToolTip("⚡ Phoenix Pen — Poignée de déplacement\n• Glissez pour déplacer la barre\n• Cliquez pour ouvrir le Dashboard")
        self.brand_lbl.setCursor(Qt.CursorShape.SizeAllCursor)
        self.brand_lbl.setStyleSheet("color: #00FF87; font-size: 15px; font-weight: bold; padding: 0 4px;")
        layout.addWidget(self.brand_lbl)

        # 1. Encre Fixe
        self.btn_fixed = QPushButton("🖋️ Fixe")
        self.btn_fixed.setToolTip("Encre Fixe (Cmd+D ou Cmd+Shift+D)")
        self.btn_fixed.clicked.connect(self._handle_fixed)
        layout.addWidget(self.btn_fixed)

        # 2. Encre Éphémère
        self.btn_vanishing = QPushButton("⏳ Fade")
        self.btn_vanishing.setToolTip("Encre Éphémère (Cmd+Shift+V ou Option+V)")
        self.btn_vanishing.clicked.connect(self._handle_vanishing)
        layout.addWidget(self.btn_vanishing)

        # 3. Gomme
        self.btn_eraser = QPushButton("🧹 Gomme")
        self.btn_eraser.setToolTip("Gomme (Cmd+Shift+E ou Alt+E)")
        self.btn_eraser.clicked.connect(self._handle_eraser)
        layout.addWidget(self.btn_eraser)

        # 4. Undo
        self.btn_undo = QPushButton("↩️")
        self.btn_undo.setToolTip("Annuler (Cmd+Z)")
        self.btn_undo.clicked.connect(self.on_undo)
        layout.addWidget(self.btn_undo)

        # 5. Clear All
        self.btn_clear = QPushButton("🗑️")
        self.btn_clear.setToolTip("Tout Effacer (Cmd+Shift+C)")
        self.btn_clear.clicked.connect(self.on_clear)
        layout.addWidget(self.btn_clear)

        # 6. Dashboard
        self.btn_dash = QPushButton("⚙️ Dashboard")
        self.btn_dash.setObjectName("dashBtn")
        self.btn_dash.setToolTip("Ouvrir les réglages Phoenix Pen")
        self.btn_dash.clicked.connect(self.on_dashboard)
        layout.addWidget(self.btn_dash)

    def set_active_mode(self, mode: str) -> None:
        """Updates visual state of buttons based on current mode."""
        self.btn_fixed.setProperty("active", "true" if mode == "draw_fixed" else "false")
        self.btn_vanishing.setProperty("active", "true" if mode == "draw_vanishing" else "false")
        self.btn_eraser.setProperty("active", "true" if mode == "eraser" else "false")

        # Force stylesheet refresh
        for btn in (self.btn_fixed, self.btn_vanishing, self.btn_eraser):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _handle_fixed(self) -> None:
        self.on_toggle_fixed()

    def _handle_vanishing(self) -> None:
        self.on_toggle_vanishing()

    def _handle_eraser(self) -> None:
        self.on_toggle_eraser()

    # Draggable Window support & Brand click
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and getattr(self, "_press_pos", None):
            if (event.globalPosition().toPoint() - self._press_pos).manhattanLength() < 5:
                if self.childAt(event.pos()) == self.brand_lbl:
                    self.on_dashboard()
            self._press_pos = None
        super().mouseReleaseEvent(event)
