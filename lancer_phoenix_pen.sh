#!/bin/bash
# Lanceur officiel macOS pour Phoenix Pen
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -f "$DIR/.venv/bin/python3" ]; then
    PYTHON_EXEC="$DIR/.venv/bin/python3"
else
    PYTHON_EXEC="python3"
fi

echo "⚡ Démarrage de Phoenix Pen..."
exec "$PYTHON_EXEC" "$DIR/python/run.py" "$@"
