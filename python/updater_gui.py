"""
Updater GUI Card Component for Phoenix Pen.
Features real-time GitHub update detection and 1-click upgrade button.
Atlas Standard: < 250 lines.
"""

import threading
from typing import Callable, Optional
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
)

import updater


class UpdaterCard(QGroupBox):
    """Sleek dark-glass update card for Phoenix Pen settings."""

    sig_status = pyqtSignal(str, str, bool)  # text, color, enable_update_btn

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("4. Mises à Jour & Version", parent)
        self.sig_status.connect(self._update_ui_state)
        self._init_ui()
        QTimer.singleShot(600, self.check_updates)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Header: Version badge
        header_row = QHBoxLayout()
        title_lbl = QLabel("Phoenix Pen")
        title_lbl.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 13px;")
        local_hash = updater.get_local_commit()
        self.badge_lbl = QLabel(f"v{updater.__version__} ({local_hash})")
        self.badge_lbl.setStyleSheet(
            "background-color: #1A1E27; color: #00E5FF; font-weight: bold; "
            "border-radius: 4px; padding: 2px 8px; font-size: 11px;"
        )
        header_row.addWidget(title_lbl)
        header_row.addStretch()
        header_row.addWidget(self.badge_lbl)
        layout.addLayout(header_row)

        # Status text
        self.status_lbl = QLabel("Prêt à vérifier les mises à jour...")
        self.status_lbl.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        layout.addWidget(self.status_lbl)

        # Buttons row
        btn_row = QHBoxLayout()
        self.btn_check = QPushButton("🔍 Vérifier")
        self.btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check.setStyleSheet(
            "background-color: #20242F; color: #FFFFFF; border: 1px solid #2D3342; "
            "border-radius: 6px; padding: 5px 12px; font-size: 12px; font-weight: 600;"
        )
        self.btn_check.clicked.connect(self.check_updates)
        btn_row.addWidget(self.btn_check)

        self.btn_update = QPushButton("🚀 Mettre à jour en 1 clic")
        self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update.setStyleSheet(
            "background-color: #00A859; color: #FFFFFF; border: 1px solid #00FF87; "
            "border-radius: 6px; padding: 5px 14px; font-size: 12px; font-weight: bold;"
        )
        self.btn_update.setVisible(False)
        self.btn_update.clicked.connect(self.do_apply_update)
        btn_row.addWidget(self.btn_update)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _update_ui_state(self, text: str, color: str, show_btn: bool) -> None:
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"color: {color}; font-size: 12px;")
        self.btn_update.setVisible(show_btn)
        self.btn_check.setEnabled(True)

    def check_updates(self) -> None:
        self.btn_check.setEnabled(False)
        self.status_lbl.setText("Vérification en cours sur GitHub...")
        self.status_lbl.setStyleSheet("color: #00E5FF; font-size: 12px;")

        def _bg():
            res = updater.check_for_updates(timeout=6)
            if res.get("has_update"):
                msg = f"⭐ Nouvelle version disponible ({res['remote']}) ! Cliquez pour installer."
                self.sig_status.emit(msg, "#00FF87", True)
            elif res.get("checked"):
                self.sig_status.emit(f"✓ Votre application est à jour ({res['local']}).", "#9CA3AF", False)
            else:
                self.sig_status.emit(f"⚠️ {res.get('message', 'Indisponible')}", "#F59E0B", False)

        threading.Thread(target=_bg, daemon=True).start()

    def do_apply_update(self) -> None:
        self.btn_update.setEnabled(False)
        self.btn_check.setEnabled(False)
        self.status_lbl.setText("Téléchargement et application de la mise à jour...")
        self.status_lbl.setStyleSheet("color: #00E5FF; font-size: 12px;")

        def _bg():
            success, msg = updater.apply_update()
            if success:
                self.sig_status.emit(f"✅ {msg} : Redémarrage en cours...", "#00FF87", False)
                QTimer.singleShot(1000, updater.restart_app)
            else:
                self.sig_status.emit(f"❌ {msg}", "#EF4444", True)
                self.btn_update.setEnabled(True)

        threading.Thread(target=_bg, daemon=True).start()
