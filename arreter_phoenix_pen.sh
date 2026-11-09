#!/bin/bash
# Arrêt propre de Phoenix Pen
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PID_FILE="$DIR/phoenix_pen.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "⚡ Phoenix Pen (PID $PID) arrêté avec succès."
    else
        echo "⚠️ Le processus n'était plus actif."
    fi
    rm -f "$PID_FILE"
fi

pkill -9 -f "phoenix-pen.*main\.py" 2>/dev/null || true
pkill -9 -f "phoenix-pen.*run\.py" 2>/dev/null || true
echo "⚡ Phoenix Pen arrêté."
