# 📜 Journal des Déploiements — Phoenix Pen (Lead Dev Atlas)

### [2026-11-09] - Abdoulaye (adiagne) [via Atlas] - Initialisation : Phoenix Pen v1.0
- **Action :** Création complète et déploiement du micro-logiciel souverain d'annotation d'écran Phoenix Pen, remplaçant définitivement Epic Pen au sein de l'équipe Phoenix Performance.
  - Implémentation de la fenêtre plein écran transparente et de la gestion clic-through (`overlay_window.py`).
  - Développement du moteur de rendu néon brillant avec lueur multicouche (`neon_renderer.py`).
  - Implémentation du moteur de reconnaissance géométrique non-intrusif pour lignes, flèches, cercles, ovales, rectangles et carrés avec seuil de confiance strict $\ge 88\%$ (`shape_recognizer.py`).
  - Création du gestionnaire d'encre éphémère (*fade away*) avec arrêt automatique du timer pour garantir 0% CPU au repos (`fade_manager.py`).
  - Écoute globale des raccourcis clavier via `pynput` avec dispatch thread-safe vers PyQt (`hotkey_manager.py`).
  - Création de l'interface graphique de configuration Dark Mode Phoenix (`config_gui.py`) et du menu System Tray (`tray_app.py`).
  - Ajout des lanceurs et scripts d'arrêt multi-OS (`.sh` pour macOS et `.bat` pour Windows).
- **Raison / Contexte :** Demande expresse de Pierre (Chaddouk) pour remplacer Epic Pen (interface encombrante, chutes de FPS en streaming/jeu, couleurs ternes, manque d'encre éphémère automatique).
- **Impact & Validation :** Tests unitaires automatisés validés à 100% (`test_core.py` et `test_gui.py`). 0% CPU constaté au repos, empreinte RAM < 40 Mo, aucun lag graphique.
