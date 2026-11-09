@echo off
title Arreter Phoenix Pen
cd /d "%~dp0"

if exist "phoenix_pen.pid" (
    set /p APP_PID=<phoenix_pen.pid
    taskkill /PID %APP_PID% /F >nul 2>&1
    del /f /q phoenix_pen.pid >nul 2>&1
    echo Phoenix Pen arrete avec succes.
) else (
    taskkill /IM python.exe /FI "WINDOWTITLE eq Phoenix Pen*" /F >nul 2>&1
    echo Aucun processus trouve.
)
exit
