"""
Modern Dark-Mode Settings GUI for Phoenix Pen.
Allows configuring hotkeys, ink modes, fade duration, colors, and neon intensity.
Atlas Standard: < 250 lines.
"""

from typing import Any
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDialog, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSlider,
    QVBoxLayout
)


class ConfigWindow(QDialog):
    """Phoenix Performance branded dark configuration panel."""

    def __init__(self, config_mgr: Any) -> None:
        super().__init__()
        self.config_mgr = config_mgr
        self.setWindowTitle("⚡ Phoenix Pen — Configuration")
        self.setFixedSize(540, 680)
        self.setStyleSheet("""
            QDialog {
                background-color: #121614;
                color: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            QGroupBox {
                border: 1px solid #1E2B23;
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 14px;
                font-weight: bold;
                color: #00FF87;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QLabel {
                color: #D1D5DB;
                font-size: 13px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #1F2937;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #00A859;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00FF87;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QCheckBox {
                color: #E5E7EB;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #374151;
                background: #111827;
            }
            QCheckBox::indicator:checked {
                background: #00A859;
                border: 1px solid #00FF87;
            }
            QPushButton {
                background-color: #1A241F;
                color: #FFFFFF;
                border: 1px solid #284435;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #24352C;
                border: 1px solid #00FF87;
            }
            QPushButton#saveBtn {
                background-color: #00A859;
                color: #000000;
                font-weight: bold;
                font-size: 14px;
                border: none;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton#saveBtn:hover {
                background-color: #00FF87;
            }
        """)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Title Banner
        header = QLabel("⚡ Phoenix Pen — Paramètres & Raccourcis")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #00FF87; margin-bottom: 2px;")
        layout.addWidget(header)

        # 1. Section Encre & Rendu
        ink_group = QGroupBox("1. Modes d'Encre & Rendu")
        ink_form = QFormLayout(ink_group)

        # Fade Duration dropdown
        self.fade_combo = QComboBox()
        self.fade_combo.addItems(["1.5 secondes", "2.0 secondes (Défaut)", "3.0 secondes", "5.0 secondes"])
        current_dur = float(self.config_mgr.get("drawing", "vanishing_duration", 2.0))
        dur_idx = {1.5: 0, 2.0: 1, 3.0: 2, 5.0: 3}.get(current_dur, 1)
        self.fade_combo.setCurrentIndex(dur_idx)
        ink_form.addRow("⏳ Disparition Encre Éphémère :", self.fade_combo)

        # Stroke Width Slider
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setRange(1, 24)
        current_w = int(self.config_mgr.get("drawing", "stroke_width", 4))
        self.width_slider.setValue(current_w)
        self.width_label = QLabel(f"{current_w} px")
        self.width_slider.valueChanged.connect(lambda v: self.width_label.setText(f"{v} px"))
        w_layout = QHBoxLayout()
        w_layout.addWidget(self.width_slider)
        w_layout.addWidget(self.width_label)
        ink_form.addRow("✏️ Épaisseur du trait :", w_layout)

        # Neon Glow Checkbox
        self.glow_check = QCheckBox("Activer l'effet Néon Lumineux (Glow)")
        self.glow_check.setChecked(bool(self.config_mgr.get("drawing", "neon_glow", True)))
        ink_form.addRow(self.glow_check)

        # Shape Recognition Checkbox
        self.shape_check = QCheckBox("Reconnaissance intelligente des formes (Seuil 88%)")
        self.shape_check.setChecked(bool(self.config_mgr.get("drawing", "shape_recognition", True)))
        ink_form.addRow(self.shape_check)

        layout.addWidget(ink_group)

        # 2. Section Palette de Couleurs
        color_group = QGroupBox("2. Palette & Couleurs Lumineuses")
        color_layout = QVBoxLayout(color_group)

        palette_grid = QGridLayout()
        colors = self.config_mgr.get("palette", [])
        self.color_buttons = []
        for i, c_hex in enumerate(colors):
            btn = QPushButton()
            btn.setFixedSize(36, 28)
            btn.setStyleSheet(f"background-color: {c_hex}; border-radius: 4px; border: 1px solid #FFFFFF;")
            btn.clicked.connect(lambda _, c=c_hex: self._select_color(c))
            palette_grid.addWidget(btn, i // 5, i % 5)
            self.color_buttons.append(btn)

        color_layout.addLayout(palette_grid)

        # Custom Color Picker & Preview
        h_color = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(34, 34)
        active_c = self.config_mgr.get("drawing", "active_color", "#00FF87")
        self.color_preview.setStyleSheet(f"background-color: {active_c}; border-radius: 6px; border: 2px solid #00FF87;")
        self.active_color = active_c

        custom_btn = QPushButton("🎨 Choisir une autre couleur...")
        custom_btn.clicked.connect(self._open_custom_color_dialog)
        h_color.addWidget(self.color_preview)
        h_color.addWidget(custom_btn)
        color_layout.addLayout(h_color)
        layout.addWidget(color_group)

        # 3. Section Raccourcis Globaux
        key_group = QGroupBox("3. Raccourcis Globaux")
        key_form = QFormLayout(key_group)
        hotkeys = self.config_mgr.get("hotkeys", {})
        key_form.addRow("🖋️ Encre Fixe (Toggle) :", QLabel(f"<b>{hotkeys.get('draw_fixed', '<alt>+d')}</b>"))
        key_form.addRow("⏳ Encre Éphémère (Toggle) :", QLabel(f"<b>{hotkeys.get('draw_vanishing', '<alt>+v')}</b>"))
        key_form.addRow("🧹 Gomme :", QLabel(f"<b>{hotkeys.get('eraser', '<alt>+e')}</b>"))
        key_form.addRow("🗑️ Tout Effacer :", QLabel(f"<b>{hotkeys.get('clear_all', '<alt>+c')}</b>"))
        key_form.addRow("↩️ Annuler (Undo) :", QLabel(f"<b>{hotkeys.get('undo', '<cmd>+z')}</b>"))
        layout.addWidget(key_group)

        # 4. Save Button
        save_btn = QPushButton("💾 Enregistrer & Appliquer")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

    def _select_color(self, hex_val: str) -> None:
        self.active_color = hex_val
        self.color_preview.setStyleSheet(f"background-color: {hex_val}; border-radius: 6px; border: 2px solid #00FF87;")

    def _open_custom_color_dialog(self) -> None:
        col = QColorDialog.getColor(QColor(self.active_color), self, "Choisir une couleur néon")
        if col.isValid():
            self._select_color(col.name())

    def _save_settings(self) -> None:
        dur_map = {0: 1.5, 1: 2.0, 2: 3.0, 3: 5.0}
        selected_dur = dur_map.get(self.fade_combo.currentIndex(), 2.0)

        self.config_mgr.set("drawing", "vanishing_duration", selected_dur)
        self.config_mgr.set("drawing", "stroke_width", self.width_slider.value())
        self.config_mgr.set("drawing", "neon_glow", self.glow_check.isChecked())
        self.config_mgr.set("drawing", "shape_recognition", self.shape_check.isChecked())
        self.config_mgr.set("drawing", "active_color", self.active_color)

        self.accept()
