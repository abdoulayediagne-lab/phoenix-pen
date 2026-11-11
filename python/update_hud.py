"""
Floating Update Notification Pill (UpdateHUD) for Phoenix Pen.
Polls origin/main silently every 60s in the background and pops a non-intrusive
1-click update pill at the top of the screen when a new commit is detected.
Atlas Standard: < 250 lines.
"""

import sys
import threading
import time
from typing import Any, Optional
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

import updater


class UpdateHUD(QFrame):
    """Non-activating floating pill alerting the user when a GitHub update is ready."""

    sig_check_result = pyqtSignal(dict)
    sig_apply_result = pyqtSignal(bool, str)

    def __init__(self) -> None:
        super().__init__()
        self._current_ver: Optional[str] = None
        self.dismissed_ver: Optional[str] = None
        self._is_updating = False
        self._stop_event = threading.Event()
        self._watcher_started = False

        self.sig_check_result.connect(self._on_check_result)
        self.sig_apply_result.connect(self._on_apply_result)

        self._init_window()
        self._init_ui()

    def _init_window(self) -> None:
        """Configures borderless always-on-top pill that never steals focus."""
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedSize(390, 44)
        self._set_border_color("#F59E0B")

    def _set_border_color(self, border_hex: str) -> None:
        """Updates pill border color (amber when waiting, neon green on success)."""
        self.setStyleSheet(f"""
            UpdateHUD {{
                background-color: rgba(10, 12, 16, 248);
                border: 2px solid {border_hex};
                border-radius: 22px;
            }}
            QLabel {{
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }}
            QPushButton#updateBtn {{
                background-color: #00A859;
                color: #FFFFFF;
                border: none;
                border-radius: 13px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton#updateBtn:hover {{
                background-color: #00FF87;
                color: #0B0E0D;
            }}
            QPushButton#closeBtn {{
                background: transparent;
                color: #9CA3AF;
                border: none;
                font-size: 13px;
                font-weight: bold;
                padding: 0 4px;
            }}
            QPushButton#closeBtn:hover {{
                color: #FFFFFF;
            }}
        """)

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 12, 6)
        layout.setSpacing(8)

        self.icon_lbl = QLabel("🚀")
        self.icon_lbl.setFixedWidth(20)
        layout.addWidget(self.icon_lbl)

        self.msg_lbl = QLabel("Nouvelle version disponible")
        layout.addWidget(self.msg_lbl, stretch=1)

        self.btn_update = QPushButton("Mettre à jour")
        self.btn_update.setObjectName("updateBtn")
        self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update.clicked.connect(self._trigger_install)
        layout.addWidget(self.btn_update)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("closeBtn")
        self.btn_close.setFixedSize(22, 22)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.dismiss)
        layout.addWidget(self.btn_close)

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
        self._apply_native_level()

    def _apply_native_level(self) -> None:
        """Keeps pill visible across all Spaces without activating the app on macOS."""
        if sys.platform != "darwin":
            return
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
                if hasattr(nswin, "setHidesOnDeactivate_"):
                    nswin.setHidesOnDeactivate_(False)
                if hasattr(nswin, "setFloatingPanel_"):
                    nswin.setFloatingPanel_(True)
                nswin.setLevel_(AppKit.NSStatusWindowLevel + 1)
                nswin.orderFrontRegardless()
        except Exception:
            pass

    def _position_pill(self) -> None:
        """Centers pill horizontally just below Phoenix Pen's floating bar (y=168)."""
        screen = QGuiApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.x() + (geom.width() - self.width()) // 2
            y = max(geom.y() + 10, 168)
            self.move(x, y)

    def show_update(self, remote_ver: str = "disponible") -> None:
        """Shows the update pill unless this exact version was dismissed by the user."""
        if remote_ver and remote_ver == self.dismissed_ver:
            return
        self._current_ver = remote_ver
        self._set_border_color("#F59E0B")
        self.msg_lbl.setText(f"Phoenix Pen : maj ({remote_ver})")
        self.btn_update.setVisible(True)
        self.btn_update.setEnabled(True)
        self._position_pill()
        self.show()
        self.raise_()
        self._apply_native_level()

    def dismiss(self) -> None:
        """Remembers dismissed version so the pill does not reappear until next release."""
        if self._current_ver:
            self.dismissed_ver = self._current_ver
        self.hide()

    def start_watcher(self, interval_sec: float = 60.0) -> None:
        """Starts background update polling thread (initial check after 1.5s, then 60s)."""
        if self._watcher_started:
            return
        self._watcher_started = True
        self._stop_event.clear()

        def _poll_loop() -> None:
            if self._stop_event.wait(1.5):
                return
            while not self._stop_event.is_set():
                try:
                    res = updater.check_for_updates(timeout=5)
                    self.sig_check_result.emit(res)
                except Exception:
                    pass
                if self._stop_event.wait(interval_sec):
                    break

        threading.Thread(target=_poll_loop, daemon=True).start()

    def _on_check_result(self, res: dict) -> None:
        if self._is_updating:
            return
        if res.get("has_update"):
            self.show_update(res.get("remote") or "disponible")
        elif res.get("checked") and not res.get("has_update") and self.isVisible():
            self.hide()

    def _trigger_install(self) -> None:
        if self._is_updating:
            return
        self._is_updating = True
        self.btn_update.setEnabled(False)
        self.btn_update.setVisible(False)
        self.msg_lbl.setText("⏳ Téléchargement de la mise à jour...")

        def _worker() -> None:
            try:
                ok, msg = updater.apply_update()
                self.sig_apply_result.emit(ok, msg)
            except Exception as e:
                self.sig_apply_result.emit(False, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_apply_result(self, ok: bool, msg: str) -> None:
        self._is_updating = False
        if ok:
            self._set_border_color("#00FF87")
            self.msg_lbl.setText("✅ Mis à jour ! Relance en cours...")
            QTimer.singleShot(1200, updater.restart_app)
        else:
            self.msg_lbl.setText(f"⚠️ Échec : {msg[:26]}")
            QTimer.singleShot(3000, self.hide)

    def stop(self) -> None:
        """Stops polling thread cleanly and closes pill."""
        self._stop_event.set()
        self.close()

