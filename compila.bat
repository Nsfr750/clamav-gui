@echo off
REM Script di compilazione per ClamAV GUI
REM Crea un eseguibile Windows con tutte le dipendenze

echo ========================================
echo    COMPILATORE ClamAV GUI
echo ========================================
echo.
echo Descrizione: Antivirus Interface con Scanning Avanzato
echo Autore: Nsfr750
echo Copyright: (C) 2025 Nsfr750 - Tutti i diritti riservati
echo ========================================
echo.

REM Verifica se Python è disponibile
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non trovato. Assicurati che Python sia installato e nel PATH.
    pause
    exit /b 1
)

REM Verifica se siamo nella directory corretta
if not exist "compile_app.py" (
    echo ❌ File compile_app.py non trovato nella directory corrente.
    echo   Eseguire questo script dalla directory principale del progetto.
    pause
    exit /b 1
)

echo 🔍 Verifica ambiente...
echo.

REM Chiedi opzioni all'utente
echo Scegli le opzioni di compilazione:
echo.
echo 1^) Compilazione normale (raccomandata)
echo 2^) Compilazione debug (con console)
echo 3^) Pulisci e ricompila tutto
echo 4^) Compilazione senza UPX (no compressione)
echo.
set /p choice="Scegli un'opzione (1-4) [default: 1]: "

set "debug=false"
set "clean=false"
set "noupx=false"

if "%choice%"=="2" (
    set "debug=true"
    echo ✅ Modalità debug selezionata
) else if "%choice%"=="3" (
    set "clean=true"
    echo ✅ Pulizia abilitata
) else if "%choice%"=="4" (
    set "noupx=true"
    echo ✅ UPX disabilitato
) else (
    echo ✅ Modalità normale selezionata
)

echo.
echo 🚀 Avvio compilazione...
echo.

REM Esegui il compilatore Python
python compile_app.py %debug% %clean% %noupx%

if errorlevel 1 (
    echo.
    echo ❌ Compilazione fallita!
    pause
    exit /b 1
)

echo.
echo 🎉 Compilazione completata con successo!
echo.
echo 📦 Il package eseguibile è disponibile in: dist\ClamAV-GUI\
echo.
echo Premi un tasto per uscire...
pause >nul
