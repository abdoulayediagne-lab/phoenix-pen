"""
Modern Dark-Mode Settings GUI for Phoenix Pen.
Features dual interactive circular color wheels (Neon & Metallic) with reticles,
dynamic sliders (1-100px stroke, 6-200px eraser), and live instant update.
Atlas Standard: < 250 lines.
"""

from typing import Any, List
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout
)

from color_wheel import MetallicWheelWidget, NeonHueWheelWidget


class ConfigWindow(QDialog):
    """Phoenix Performance branded dark configuration panel with dual interactive color wheels."""

    def __init__(self, config_mgr: Any) -> None:
        super().__init__()
        self.config_mgr = config_mgr
        self.setWindowTitle("⚡ Phoenix Pen — Configuration & Dashboard")
        self.setFixedSize(580, 790)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.active_color = self.config_mgr.get("drawing", "active_color", "#00FF87")
        self.setStyleSheet("""
            QDialog {
                background-color: #0D0F12;
                color: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            QGroupBox {
                border: 1px solid #1F232B;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: bold;
                color: #00FF87;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QLabel { color: #D1D5DB; font-size: 13px; }
            QSlider::groove:horizontal {
                height: 6px;
                background: #1F2937;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00FF87;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QComboBox {
                background-color: #1A231E;
                color: #FFFFFF;
                border: 1px solid #2D3E33;
                border-radius: 6px;
                padding: 4px 8px;
                min-width: 170px;
            }
            QCheckBox { color: #E5E7EB; spacing: 8px; font-size: 12px; }
            QCheckBox::indicator {
                width: 15px; height: 15px;
                border: 1px solid #00A859;
                border-radius: 4px;
                background: #1A231E;
            }
            QCheckBox::indicator:checked { background: #00FF87; }
            QPushButton#saveBtn {
                background-color: #00A859;
                color: #0B0E0D;
                font-weight: bold;
                border-radius: 8px;
                padding: 9px;
                font-size: 14px;
                border: none;
            }
            QPushButton#saveBtn:hover { background-color: #00FF87; }
        """)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QLabel("⚡ Phoenix Pen — Tableau de Bord & Réglages")
        header.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        header.setStyleSheet("color: #00FF87; margin-bottom: 2px;")
        layout.addWidget(header)

        # 1. Section Encre, Gomme & Rendu
        ink_group = QGroupBox("1. Modes d'Encre, Gomme & Rendu")
        ink_form = QFormLayout(ink_group)
        ink_form.setSpacing(6)

        self.fade_combo = QComboBox()
        self.fade_combo.addItems(["1.5 secondes", "2.0 secondes (Défaut)", "3.0 secondes", "5.0 secondes"])
        dur = float(self.config_mgr.get("drawing", "vanishing_duration", 2.0))
        self.fade_combo.setCurrentIndex({1.5: 0, 2.0: 1, 3.0: 2, 5.0: 3}.get(dur, 1))
        self.fade_combo.currentIndexChanged.connect(self._on_fade_changed)
        ink_form.addRow("⏳ Disparition Encre :", self.fade_combo)

        # Sliders: Stroke Width & Eraser Width
        self.width_slider = QSlider(Qt.Orientation.Horizontal); self.width_slider.setRange(1, 100)
        cw = int(self.config_mgr.get("drawing", "stroke_width", 4)); self.width_slider.setValue(cw)
        self.width_label = QLabel(f"{cw} px"); self.width_slider.valueChanged.connect(self._on_width_changed)
        wl = QHBoxLayout(); wl.addWidget(self.width_slider); wl.addWidget(self.width_label)
        ink_form.addRow("✏️ Épaisseur du trait (1-100px) :", wl)

        self.eraser_slider = QSlider(Qt.Orientation.Horizontal); self.eraser_slider.setRange(6, 150)
        ew = int(self.config_mgr.get("drawing", "eraser_width", 24)); self.eraser_slider.setValue(ew)
        self.eraser_label = QLabel(f"{ew} px"); self.eraser_slider.valueChanged.connect(self._on_eraser_changed)
        el = QHBoxLayout(); el.addWidget(self.eraser_slider); el.addWidget(self.eraser_label)
        ink_form.addRow("🧹 Épaisseur de la gomme (6-150px) :", el)

        self.glow_check = QCheckBox("Activer l'effet Néon Lumineux (Glow multicouche)")
        self.glow_check.setChecked(bool(self.config_mgr.get("drawing", "neon_glow", True)))
        ink_form.addRow(self.glow_check)

        self.shape_check = QCheckBox("Reconnaissance intelligente des formes (Seuil 88%)")
        self.shape_check.setChecked(bool(self.config_mgr.get("drawing", "shape_recognition", True)))
        ink_form.addRow(self.shape_check)

        self.hud_check = QCheckBox("Afficher la barre flottante rapide (HUD Capsule)")
        self.hud_check.setChecked(bool(self.config_mgr.get("system", "floating_hud", True)))
        ink_form.addRow(self.hud_check)
        layout.addWidget(ink_group)

        # 2. Section Roues Chromatiques Interactives (Néon & Métallique)
        pal_group = QGroupBox("2. Roues Chromatiques Interactives (Viseur Tactique Direct)")
        pal_layout = QVBoxLayout(pal_group)
        pal_layout.setSpacing(6)

        wheels_row = QHBoxLayout()
        # Wheel 1: Neon Rainbow
        w1_box = QVBoxLayout()
        w1_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        w1_lbl = QLabel("<b>✨ Spectre Néon & Vives</b>")
        w1_lbl.setStyleSheet("color: #00FF87; font-size: 12px;")
        self.neon_wheel = NeonHueWheelWidget(size=140)
        self.neon_wheel.sig_color_changed.connect(self._select_color)
        w1_box.addWidget(w1_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        w1_box.addWidget(self.neon_wheel, alignment=Qt.AlignmentFlag.AlignCenter)
        wheels_row.addLayout(w1_box)

        # Wheel 2: Metallic Gold & Shimmer
        w2_box = QVBoxLayout()
        w2_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        w2_lbl = QLabel("<b>💎 Or Solaire, Argent & Brillance</b>")
        w2_lbl.setStyleSheet("color: #FFD700; font-size: 12px;")
        self.metallic_wheel = MetallicWheelWidget(size=140)
        self.metallic_wheel.sig_color_changed.connect(self._select_color)
        w2_box.addWidget(w2_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        w2_box.addWidget(self.metallic_wheel, alignment=Qt.AlignmentFlag.AlignCenter)
        wheels_row.addLayout(w2_box)
        pal_layout.addLayout(wheels_row)

        # Active Color Indicator & Swatches
        preview_row = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(36, 36)
        self.color_hex_lbl = QLabel(self.active_color)
        self.color_hex_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #FFFFFF;")
        self._update_preview(self.active_color)

        preview_row.addWidget(QLabel("Nuance active (Direct) :"))
        preview_row.addWidget(self.color_preview)
        preview_row.addWidget(self.color_hex_lbl)
        preview_row.addSpacing(10)

        # Quick Pastilles (Phoenix Favorites)
        favs = ["#00FF87", "#00A859", "#00E5FF", "#2979FF", "#FF3D00", "#FF1493", "#FFD700", "#E2E8F0"]
        for c_hex in favs:
            btn = QPushButton()
            btn.setFixedSize(26, 26)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"background-color: {c_hex}; border-radius: 13px; border: 1.5px solid rgba(255,255,255,0.4);")
            btn.clicked.connect(lambda _, c=c_hex: self._select_color(c))
            preview_row.addWidget(btn)
        preview_row.addStretch()
        pal_layout.addLayout(preview_row)
        layout.addWidget(pal_group)

        # 3. Section Raccourcis Globaux
        key_group = QGroupBox("3. Raccourcis Globaux")
        kf = QFormLayout(key_group)
        kf.setSpacing(4)
        kf.addRow("🖋️ Encre Fixe :", QLabel("<b>Cmd + D</b> ou <b>Option + D</b> (ou Cmd+Shift+D)"))
        kf.addRow("⏳ Encre Éphémère :", QLabel("<b>Cmd + Shift + V</b> ou <b>Option + V</b>"))
        kf.addRow("🧹 Gomme / Undo :", QLabel("<b>Option + E</b> (Gomme) | <b>Cmd + Z</b> (Annuler direct)"))
        kf.addRow("⎋ Sortie :", QLabel("<b>Échap</b> pour reprendre la souris sans dessiner"))
        layout.addWidget(key_group)

        # 4. Save Button
        save_btn = QPushButton("💾 Enregistrer & Fermer")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

    def _on_fade_changed(self, idx: int) -> None:
        self.config_mgr.set("drawing", "vanishing_duration", {0: 1.5, 1: 2.0, 2: 3.0, 3: 5.0}.get(idx, 2.0))

    def _on_width_changed(self, val: int) -> None:
        self.width_label.setText(f"{val} px"); self.config_mgr.set("drawing", "stroke_width", val)

    def _on_eraser_changed(self, val: int) -> None:
        self.eraser_label.setText(f"{val} px"); self.config_mgr.set("drawing", "eraser_width", val)

    def _select_color(self, hex_val: str) -> None:
        self.active_color = hex_val.upper(); self._update_preview(self.active_color)
        self.config_mgr.set("drawing", "active_color", self.active_color)

    def _update_preview(self, hex_val: str) -> None:
        self.color_preview.setStyleSheet(f"background-color: {hex_val}; border-radius: 18px; border: 2.5px solid #00FF87;")
        self.color_hex_lbl.setText(hex_val)

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
        try:
            import AppKit, objc
            nswin = objc.objc_object(c_void_p=int(self.winId())).window()
            if nswin is not None:
                nswin.setCollectionBehavior_(AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary | AppKit.NSWindowCollectionBehaviorStationary)
                nswin.setLevel_(AppKit.NSStatusWindowLevel + 2)
                nswin.orderFrontRegardless()
                nswin.makeKeyAndOrderFront_(None)
                AppKit.NSApp.activateIgnoringOtherApps_(True)
        except Exception: pass

    def _save_settings(self) -> None:
        dur = {0: 1.5, 1: 2.0, 2: 3.0, 3: 5.0}.get(self.fade_combo.currentIndex(), 2.0)
        self.config_mgr.set("drawing", "vanishing_duration", dur)
        for k, v in [("stroke_width", self.width_slider.value()), ("eraser_width", self.eraser_slider.value()), ("neon_glow", self.glow_check.isChecked()), ("shape_recognition", self.shape_check.isChecked()), ("active_color", self.active_color)]:
            self.config_mgr.set("drawing", k, v)
        self.config_mgr.set("system", "floating_hud", self.hud_check.isChecked()); self.accept()
