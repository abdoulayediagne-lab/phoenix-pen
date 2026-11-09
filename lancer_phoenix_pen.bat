@echo off
title Phoenix Pen - Demarrage
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXEC=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXEC=python"
)

echo Demarrage de Phoenix Pen en arriere-plan...
start "" "%PYTHON_EXEC%" "python\run.py"
exit
