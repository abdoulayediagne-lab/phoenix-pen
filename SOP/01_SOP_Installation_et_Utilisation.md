# 📋 SOP 01 — Installation et Utilisation de Phoenix Pen

## 1. Objectif
Guider l'installation, le paramétrage et l'utilisation quotidienne de **Phoenix Pen** sur macOS et Windows 11.

---

## 2. Installation Rapide

### Sur macOS :
```bash
cd /Users/abdou26/phoenix-dev/phoenix-pen
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./lancer_phoenix_pen.sh
```

### Sur Windows :
Double-cliquez simplement sur :
```text
lancer_phoenix_pen.bat
```

---

## 3. Raccourcis Clavier par Défaut

| Action | Raccourci macOS | Raccourci Windows | Description |
| :--- | :--- | :--- | :--- |
| **Encre Fixe** | `Alt + D` | `Alt + D` | Active/Désactive le tracé permanent sur l'écran |
| **Encre Éphémère** | `Alt + V` | `Alt + V` | Tracé qui s'estompe et disparaît après X secondes |
| **Gomme** | `Alt + E` | `Alt + E` | Efface les traits permanents au survol |
| **Tout Effacer** | `Alt + C` | `Alt + C` | Nettoie instantanément l'intégralité de l'écran |
| **Annuler (Undo)** | `Cmd + Z` | `Ctrl + Z` | Annule le dernier trait tracé |
| **Configuration** | `Alt + P` | `Alt + P` | Ouvre le panneau de réglages néon et raccourcis |

---

## 4. Dépannage & Arrêt
Pour arrêter l'application :
- **macOS :** Exécuter `./arreter_phoenix_pen.sh` ou faire un clic droit sur l'icône dans la barre des menus > *Quitter*.
- **Windows :** Exécuter `arreter_phoenix_pen.bat` ou clic droit System Tray > *Quitter*.

