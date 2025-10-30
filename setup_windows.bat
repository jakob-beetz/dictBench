@echo off
echo PropBench Windows CMD Setup Script
echo ==================================

REM Prüfen ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python nicht gefunden. Bitte Python 3.11 installieren.
    pause
    exit /b 1
)

echo Python gefunden.

REM Prüfen ob manage.py existiert
if not exist "propbench\manage.py" (
    echo FEHLER: manage.py nicht gefunden. Bitte im dictBench Hauptverzeichnis ausfuehren.
    pause
    exit /b 1
)

echo.
echo Schritt 1: Virtual Environment erstellen...
if exist "venv-3.11" (
    echo Virtual Environment existiert bereits.
) else (
    python -m venv venv-3.11
    if errorlevel 1 (
        echo FEHLER: Virtual Environment konnte nicht erstellt werden.
        pause
        exit /b 1
    )
    echo Virtual Environment erfolgreich erstellt.
)

echo.
echo Schritt 2: Virtual Environment aktivieren...
call venv-3.11\Scripts\activate.bat
if errorlevel 1 (
    echo FEHLER: Virtual Environment konnte nicht aktiviert werden.
    pause
    exit /b 1
)

echo.
echo Schritt 3: Pip upgraden...
python -m pip install --upgrade pip

echo.
echo Schritt 4: Dependencies installieren...
cd propbench
pip install -r requirements.txt
if errorlevel 1 (
    echo FEHLER: Dependencies konnten nicht installiert werden.
    echo Versuche es manuell: cd propbench ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo Schritt 5: Database Migration...
python manage.py migrate
if errorlevel 1 (
    echo FEHLER: Migration fehlgeschlagen.
    echo Installiere fehlende Pakete...
    pip install django-debug-toolbar django-json-widget
    echo Versuche Migration erneut...
    python manage.py migrate
    if errorlevel 1 (
        echo FEHLER: Migration immer noch fehlgeschlagen.
        echo Siehe MIGRATION_FIX.md fuer weitere Hilfe.
        pause
        exit /b 1
    )
)

echo.
echo Setup erfolgreich abgeschlossen!
echo =========================
echo.
echo Naechste Schritte:
echo 1. Superuser erstellen: python manage.py createsuperuser
echo 2. Development Server starten: python manage.py runserver
echo 3. Im Browser oeffnen: http://127.0.0.1:8000/admin/
echo.
echo Falls Probleme auftreten, siehe: SETUP_TROUBLESHOOTING.md
pause