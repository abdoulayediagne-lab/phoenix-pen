# ⚡ Phoenix Pen — Annotation d'Écran Souveraine & Lumineuse

Alternative souveraine, ultra-rapide et moderne à **Epic Pen**, conçue sur-mesure pour l'équipe **Phoenix Performance** (**Pierre, Mathis, Abdoulaye**).

---

## 🚀 Fonctionnalités Clés

* **Ghost Mode (Zéro encombrement) :** Réside discrètement dans la barre des tâches (**System Tray**). Aucune toolbar parasite ne vient bloquer votre écran.
* **100% Piloté aux Raccourcis :** Activez le mode dessin, l'encre éphémère ou la gomme en un instant.
* **Double Mode d'Encre :**
  * **Encre Fixe (`Alt+D`) :** Pour annoter durablement une maquette, un code ou une vidéo.
  * **Encre Éphémère Fade-Away (`Alt+V`) :** Tracez votre annotation en réunion ou vidéo ; elle s'estompe avec un fondu fluide et **disparaît automatiquement** au bout de 1.5s, 2s ou 3s sans aucune action requise.
* **Rendu Visuel Néon Lumineux :** Fini les couleurs ternes de tableau d'école ! Traits brillants avec lueur néon moderne aux couleurs Phoenix (`#00A859`, `#00FF87`, `#9B6E28`, Cyan, Argenté, Bleu royal, etc.).
* **Reconnaissance Géométrique Intelligente (Seuil 88%) :** Vos rectangles, carrés, cercles, ovales, lignes droites et flèches sont automatiquement convertis en formes parfaites. Le tracé libre reste intact si vous gribouillez.
* **Performance Absolue (Zéro perte de FPS) :** Le moteur se met en veille totale (0% CPU/GPU) dès qu'aucun fondu n'est actif. Empreinte RAM `< 40 Mo`. Zéro chute de FPS en jeu ou en capture vidéo.

---

## 📁 Architecture du Projet

```text
phoenix-pen/
│
├── .agents/
│   └── AGENTS.md               # Directives de projet (Lead Dev Atlas)
├── assets/
│   └── icon.png                # Logo officiel néon vert
├── config/
│   ├── config.json             # Paramètres actifs
│   └── config.example.json     # Modèle par défaut
├── python/
│   ├── run.py                  # Point d'entrée avec PID lock
│   ├── main.py                 # Contrôleur central
│   ├── overlay_window.py       # Fenêtre transparente & gestion clic-through
│   ├── neon_renderer.py        # Moteur graphique néon multicouche
│   ├── shape_recognizer.py     # Reconnaissance vectorielle de formes
│   ├── fade_manager.py         # Moteur de disparition d'encre & veille CPU
│   ├── hotkey_manager.py       # Raccourcis globaux système
│   ├── config_gui.py           # Panneau de configuration Dark Mode
│   └── tray_app.py             # Icône barre des tâches & menu rapide
├── requirements.txt
├── lancer_phoenix_pen.sh       # Lanceur macOS
├── lancer_phoenix_pen.bat      # Lanceur Windows
├── arreter_phoenix_pen.sh
└── arreter_phoenix_pen.bat
```
