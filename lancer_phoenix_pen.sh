#!/bin/bash
# Lanceur officiel macOS pour Phoenix Pen
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -f "$DIR/.venv/bin/python3" ]; then
    PYTHON_EXEC="$DIR/.venv/bin/python3"
else
    PYTHON_EXEC="python3"
fi

ARCH_CMD=""
if [ "$(uname -m)" = "arm64" ] || [ "$(sysctl -in hw.optional.arm64 2>/dev/null)" = "1" ]; then
    ARCH_CMD="/usr/bin/arch -arm64"
fi

echo "⚡ Démarrage de Phoenix Pen..."
exec $ARCH_CMD "$PYTHON_EXEC" "$DIR/python/main.py" --open-dashboard "$@"
