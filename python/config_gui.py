"""
Modern Dark-Mode Settings GUI for Phoenix Pen.
Allows configuring hotkeys, ink modes, fade duration, eraser size, and neon/metallic palettes.
Atlas Standard: < 250 lines.
"""

from typing import Any, List
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDialog, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSlider,
    QVBoxLayout
)


class ConfigWindow(QDialog):
    """Phoenix Performance branded dark configuration panel with dual circular palettes."""

    def __init__(self, config_mgr: Any) -> None:
        super().__init__()
        self.config_mgr = config_mgr
        self.setWindowTitle("⚡ Phoenix Pen — Configuration & Dashboard")
        self.setFixedSize(570, 750)
        self.setStyleSheet("""
            QDialog {
                background-color: #121614;
                color: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            QGroupBox {
                border: 1px solid #1E2B23;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
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
                min-width: 180px;
            }
            QCheckBox { color: #E5E7EB; spacing: 8px; font-size: 13px; }
            QCheckBox::indicator {
                width: 16px; height: 16px;
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
                padding: 10px;
                font-size: 14px;
                border: none;
            }
            QPushButton#saveBtn:hover { background-color: #00FF87; }
        """)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        header = QLabel("⚡ Phoenix Pen — Tableau de Bord & Réglages")
        header.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        header.setStyleSheet("color: #00FF87; margin-bottom: 2px;")
        layout.addWidget(header)

        # 1. Section Encre, Gomme & Rendu
        ink_group = QGroupBox("1. Modes d'Encre, Gomme & Rendu")
        ink_form = QFormLayout(ink_group)

        self.fade_combo = QComboBox()
        self.fade_combo.addItems(["1.5 secondes", "2.0 secondes (Défaut)", "3.0 secondes", "5.0 secondes"])
        dur = float(self.config_mgr.get("drawing", "vanishing_duration", 2.0))
        self.fade_combo.setCurrentIndex({1.5: 0, 2.0: 1, 3.0: 2, 5.0: 3}.get(dur, 1))
        ink_form.addRow("⏳ Disparition Encre Éphémère :", self.fade_combo)

        # Stroke Width Slider
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setRange(1, 24)
        cw = int(self.config_mgr.get("drawing", "stroke_width", 4))
        self.width_slider.setValue(cw)
        self.width_label = QLabel(f"{cw} px")
        self.width_slider.valueChanged.connect(lambda v: self.width_label.setText(f"{v} px"))
        wl = QHBoxLayout()
        wl.addWidget(self.width_slider)
        wl.addWidget(self.width_label)
        ink_form.addRow("✏️ Épaisseur du trait :", wl)

        # Eraser Width Slider
        self.eraser_slider = QSlider(Qt.Orientation.Horizontal)
        self.eraser_slider.setRange(6, 70)
        ew = int(self.config_mgr.get("drawing", "eraser_width", 24))
        self.eraser_slider.setValue(ew)
        self.eraser_label = QLabel(f"{ew} px")
        self.eraser_slider.valueChanged.connect(lambda v: self.eraser_label.setText(f"{v} px"))
        el = QHBoxLayout()
        el.addWidget(self.eraser_slider)
        el.addWidget(self.eraser_label)
        ink_form.addRow("🧹 Épaisseur de la gomme :", el)

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

        # 2. Section Palettes de Couleurs (Ronds : Vives & Métalliques)
        pal_group = QGroupBox("2. Palettes de Couleurs (Sélection en Ronds)")
        pal_layout = QVBoxLayout(pal_group)
        pal_layout.setSpacing(6)

        # Cercle 1 : Couleurs Néon Vives
        pal_layout.addWidget(QLabel("<b>✨ Cercle 1 : Couleurs Néon Vives</b>"))
        grid1 = QHBoxLayout()
        grid1.setSpacing(8)
        c1_list = self.config_mgr.get("palette_essential", default=[
            "#00FF87", "#00A859", "#00E5FF", "#2979FF", "#FF3D00", "#FF1493", "#FFEA00", "#A855F7", "#FFFFFF"
        ])
        self.round_buttons: List[QPushButton] = []
        for c_hex in c1_list:
            btn = self._create_round_btn(c_hex, border_style="1px solid rgba(255,255,255,0.4)")
            grid1.addWidget(btn)
            self.round_buttons.append(btn)
        pal_layout.addLayout(grid1)

        # Cercle 2 : Couleurs Brillance, Or & Paillettes Métalliques
        pal_layout.addWidget(QLabel("<b>💎 Cercle 2 : Brillance, Or Solaire & Paillettes Métalliques</b>"))
        grid2 = QHBoxLayout()
        grid2.setSpacing(8)
        c2_list = self.config_mgr.get("palette_metallic", default=[
            "#FFD700", "#E5A93C", "#C59B27", "#E2E8F0", "#CBD5E1", "#38BDF8", "#F472B6", "#FB923C", "#10B981"
        ])
        for c_hex in c2_list:
            btn = self._create_round_btn(c_hex, border_style="2px solid rgba(255,215,0,0.7)")
            grid2.addWidget(btn)
            self.round_buttons.append(btn)
        pal_layout.addLayout(grid2)

        # Active Color Preview (Round Swatch) & Custom Dialog
        h_color = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(38, 38)
        self.active_color = self.config_mgr.get("drawing", "active_color", "#00FF87")
        self._update_preview(self.active_color)

        custom_btn = QPushButton("🎨 Choisir une nuance sur-mesure...")
        custom_btn.clicked.connect(self._open_custom_color_dialog)
        h_color.addWidget(QLabel("Nuance active :"))
        h_color.addWidget(self.color_preview)
        h_color.addWidget(custom_btn)
        h_color.addStretch()
        pal_layout.addLayout(h_color)
        layout.addWidget(pal_group)

        # 3. Section Raccourcis Globaux
        key_group = QGroupBox("3. Raccourcis Globaux (Mac & Windows)")
        kf = QFormLayout(key_group)
        kf.addRow("🖋️ Encre Fixe :", QLabel("<b>Cmd + D</b> ou <b>Option + D</b> (ou Cmd+Shift+D)"))
        kf.addRow("⏳ Encre Éphémère :", QLabel("<b>Cmd + Shift + V</b> ou <b>Option + V</b>"))
        kf.addRow("🧹 Gomme / Undo :", QLabel("<b>Option + E</b> (Gomme) | <b>Cmd + Z</b> (Annuler)"))
        kf.addRow("⎋ Sortie :", QLabel("<b>Échap</b> pour quitter instantanément le dessin"))
        layout.addWidget(key_group)

        # 4. Save Button
        save_btn = QPushButton("💾 Enregistrer & Appliquer")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

    def _create_round_btn(self, hex_val: str, border_style: str = "1px solid #FFFFFF") -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(36, 36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_val};
                border-radius: 18px;
                border: {border_style};
            }}
            QPushButton:hover {{
                border: 3px solid #FFFFFF;
                transform: scale(1.1);
            }}
        """)
        btn.clicked.connect(lambda _, c=hex_val: self._select_color(c))
        return btn

    def _select_color(self, hex_val: str) -> None:
        self.active_color = hex_val
        self._update_preview(hex_val)

    def _update_preview(self, hex_val: str) -> None:
        self.color_preview.setStyleSheet(
            f"background-color: {hex_val}; border-radius: 19px; border: 3px solid #00FF87;"
        )

    def _open_custom_color_dialog(self) -> None:
        col = QColorDialog.getColor(QColor(self.active_color), self, "Choisir une couleur néon")
        if col.isValid():
            self._select_color(col.name())

    def _save_settings(self) -> None:
        dur_map = {0: 1.5, 1: 2.0, 2: 3.0, 3: 5.0}
        sel_dur = dur_map.get(self.fade_combo.currentIndex(), 2.0)
        self.config_mgr.set("drawing", "vanishing_duration", sel_dur)
        self.config_mgr.set("drawing", "stroke_width", self.width_slider.value())
        self.config_mgr.set("drawing", "eraser_width", self.eraser_slider.value())
        self.config_mgr.set("drawing", "neon_glow", self.glow_check.isChecked())
        self.config_mgr.set("drawing", "shape_recognition", self.shape_check.isChecked())
        self.config_mgr.set("system", "floating_hud", self.hud_check.isChecked())
        self.config_mgr.set("drawing", "active_color", self.active_color)
        self.accept()
