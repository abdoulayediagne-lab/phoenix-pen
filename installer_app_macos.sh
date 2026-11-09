#!/usr/bin/env bash
# Script d'installation de l'application native macOS Phoenix Pen.app
# Atlas Standard: Phoenix Performance

DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_APP="$HOME/Desktop/Phoenix Pen.app"

echo "⚡ Construction de Phoenix Pen.app sur le Bureau..."

# Vérification présence AppIcon.icns
if [ ! -f "$DIR/assets/AppIcon.icns" ]; then
    echo "Génération de AppIcon.icns..."
    mkdir -p /tmp/AppIcon.iconset
    sips -z 16 16 "$DIR/assets/icon.png" --out /tmp/AppIcon.iconset/icon_16x16.png > /dev/null 2>&1
    sips -z 32 32 "$DIR/assets/icon.png" --out /tmp/AppIcon.iconset/icon_16x16@2x.png > /dev/null 2>&1
    sips -z 32 32 "$DIR/assets/icon.png" --out /tmp/AppIcon.iconset/icon_32x32.png > /dev/null 2>&1
    sips -z 64 64 "$DIR/assets/icon.png" --out /tmp/AppIcon.iconset/icon_32x32@2x.png > /dev/null 2>&1
    sips -z 128 128 "$DIR/assets/icon.png" --out /tmp/AppIcon.iconset/icon_128x128.png > /dev/null 2>&1
    sips -z 256 256 "$DIR/assets/icon.png" --out /tmp/AppIcon.iconset/icon_128x128@2x.png > /dev/null 2>&1
    sips -z 256 256 "$DIR/assets/icon.png" --out /tmp/AppIcon.iconset/icon_256x256.png > /dev/null 2>&1
    sips -z 512 512 "$DIR/assets/icon.png" --out /tmp/AppIcon.iconset/icon_256x256@2x.png > /dev/null 2>&1
    sips -z 512 512 "$DIR/assets/icon.png" --out /tmp/AppIcon.iconset/icon_512x512.png > /dev/null 2>&1
    iconutil -c icns /tmp/AppIcon.iconset -o "$DIR/assets/AppIcon.icns" > /dev/null 2>&1
    rm -rf /tmp/AppIcon.iconset
fi

mkdir -p "$DESKTOP_APP/Contents/MacOS" "$DESKTOP_APP/Contents/Resources"
cp "$DIR/assets/AppIcon.icns" "$DESKTOP_APP/Contents/Resources/AppIcon.icns"

cat << 'EOF' > "$DESKTOP_APP/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Phoenix Pen</string>
    <key>CFBundleDisplayName</key>
    <string>Phoenix Pen</string>
    <key>CFBundleIdentifier</key>
    <string>pro.phoenixperformance.pen</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>Phoenix Pen</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSUIElement</key>
    <string>0</string>
    <key>LSArchitecturePriority</key>
    <array>
        <string>arm64</string>
    </array>
</dict>
</plist>
EOF

cat << EOF > "$DESKTOP_APP/Contents/MacOS/Phoenix Pen"
#!/usr/bin/env bash
PROJECT_DIR="$DIR"
cd "\$PROJECT_DIR"
PYTHON_BIN="\$PROJECT_DIR/.venv/bin/python3"
if [ ! -f "\$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

ARCH_CMD=""
if [ "\$(uname -m)" = "arm64" ] || [ "\$(sysctl -in hw.optional.arm64 2>/dev/null)" = "1" ]; then
    ARCH_CMD="/usr/bin/arch -arm64"
fi

# Arrêter toute ancienne instance de Phoenix Pen uniquement
pkill -9 -f "phoenix-pen.*main\.py" 2>/dev/null || true
pkill -9 -f "phoenix-pen.*run\.py" 2>/dev/null || true
rm -f "\$PROJECT_DIR/phoenix_pen.pid"

# Lancer Phoenix Pen en ouvrant le Dashboard (chemin absolu pour isoler des autres apps Phoenix)
PYTHONPATH=python nohup \$ARCH_CMD "\$PYTHON_BIN" "\$PROJECT_DIR/python/main.py" --open-dashboard > /tmp/phoenix_pen.log 2>&1 &
EOF

chmod +x "$DESKTOP_APP/Contents/MacOS/Phoenix Pen"
touch "$DESKTOP_APP"

echo "=========================================================="
echo "  ✅ SUCCÈS ! 'Phoenix Pen.app' est installé sur le Bureau !"
echo "  Double-cliquez dessus pour lancer sans aucun terminal."
echo "=========================================================="
