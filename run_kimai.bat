@echo off
REM Avvia il Kimai Desktop Client.
REM 1. Assicurati che l'ambiente virtuale esista:
REM      python -m venv .venv
REM 2. Attivalo e lancia:
REM     .venv\Scripts\python.exe -m kemai_client

if not exist .venv\Scripts\python.exe (
    echo ERRORE: ambiente virtuale .venv non trovato.
    echo Esegui prima:  python -m venv .venv
    exit /b 1
)

.venv\Scripts\python.exe -m kemai_client
PAUSE
