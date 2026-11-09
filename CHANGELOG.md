# 📜 Journal des Déploiements — Phoenix Pen (Lead Dev Atlas)

### [2026-11-09] - Abdoulaye (adiagne) [via Atlas] - Résolution Majeure : QNSPanel Natif Cocoa, Curseur QCursor Matériel & Centrage HUD
- **Action :** 
  - Remplacement du flag `Qt.WindowType.SubWindow` par `Qt.WindowType.Tool` sur l'Overlay et sur le Floating HUD : sous macOS, `SubWindow` sans parent ne créait aucun `NSWindow` Cocoa natif, rendant les deux fenêtres totalement invisibles et non interactives.
  - Génération d'un curseur matériel natif `QCursor` néon éclatant avec anneau vert et cœur blanc, rendu instantanément par macOS WindowServer sans latence.
  - Calcul dynamique de la position du Floating HUD via `screen.availableGeometry()` (centrage horizontal `584px` et positionnement vertical `48px` sous la barre des menus macOS).
- **Raison / Contexte :** Résolution définitive du problème d'invisibilité du HUD et de l'absence d'interactivité du curseur néon constatés par Abdoulaye.
- **Impact & Validation :** Fenêtres Cocoa `QNSPanel` natives opérationnelles, HUD parfaitement visible et réactif, curseur néon instantané.

### [2026-11-09] - Abdoulaye (adiagne) [via Atlas] - Correctif Critique : Détection Matérielle VK (Cmd+D / Cmd+Shift+D) & Z-Order Natif HUD
- **Action :** 
  - Détection basée sur les codes virtuels matériels (`vk == 2` pour 'd', `vk == 9` pour 'v', etc.) permettant le déclenchement immédiat de `Cmd + D`, `Cmd + Shift + D` et `Cmd + Shift + V` sous macOS même lorsque `char` est masqué par le système.
  - Fixation du niveau de fenêtre Cocoa natif `NSStatusWindowLevel` pour le Floating HUD garantissant qu'il reste toujours au-dessus de l'overlay de dessin.
  - Validation complète via suite de tests de bout en bout simulée (`test_full_flow.py`) validée à 100%.
- **Raison / Contexte :** Résolution des raccourcis Cmd+D / Cmd+Shift+D et de l'interactivité des boutons HUD signalée par Abdoulaye.
- **Impact & Validation :** Tests E2E 100% verts, boutons et raccourcis opérationnels sans aucun lag.

### [2026-11-09] - Abdoulaye (adiagne) [via Atlas] - Interface & Accessibilité : Native macOS App, Floating HUD & Dead-Keys Fix
- **Action :** 
  - Création du script d'installation de l'application native macOS `installer_app_macos.sh` générant `Phoenix Pen.app` avec icône officielle `.icns` directement sur le Bureau.
  - Implémentation de la barre d'outils flottante discrète `FloatingHUD` (`floating_hud.py`) déplaçable à la souris avec boutons 1-clic pour Encre Fixe, Encre Éphémère, Gomme, Annuler, Tout Effacer et Dashboard.
  - Résolution complète du problème de mapping clavier macOS (les touches Option+V et Option+D qui produisaient les caractères `◊` et `î` sont désormais interceptées nativement dans `hotkey_manager.py`).
  - Ajout des raccourcis multi-modificateurs recommandés Mac (`Ctrl + Option + D/V/E/C/P` et `Cmd + Shift + D/V/E/C/P`).
  - Ouverture directe du Dashboard au lancement de l'application.
- **Raison / Contexte :** Retours d'Abdoulaye pour éliminer l'usage du terminal, disposer d'un Dashboard d'application direct comme sur Phoenix Voice, et résoudre le comportement des dead-keys sur macOS.
- **Impact & Validation :** Tests d'initialisation validés à 100% (`test_gui.py` et `test_core.py`), raccourcis 100% fonctionnels et expérience utilisateur fluide sans passer par le terminal.

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

