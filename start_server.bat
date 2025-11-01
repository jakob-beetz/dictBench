@echo off
echo Django Development Server starten...
echo =====================================

REM Zum Projektverzeichnis wechseln
cd /d "%~dp0"

REM Prüfen ob Virtual Environment existiert
if not exist "venv-3.11" (
    echo FEHLER: Virtual Environment nicht gefunden!
    echo Bitte erst setup_windows.bat ausführen.
    pause
    exit /b 1
)

REM Virtual Environment aktivieren
echo Virtual Environment aktivieren...
call venv-3.11\Scripts\activate.bat

REM Ins Django-Projektverzeichnis wechseln
cd propbench

REM Prüfen ob manage.py existiert
if not exist "manage.py" (
    echo FEHLER: manage.py nicht gefunden!
    echo Falsches Verzeichnis oder Setup unvollständig.
    pause
    exit /b 1
)

REM Python Version anzeigen
echo.
echo Python Version:
python --version

REM Django Version anzeigen
echo.
echo Django Version:
python -c "import django; print('Django', django.get_version())"

echo.
echo Django Development Server wird gestartet...
echo URL: http://127.0.0.1:8000/
echo Admin: http://127.0.0.1:8000/admin/
echo.
echo Zum Stoppen: Ctrl+C drücken
echo.

REM Server starten
python manage.py runserver

pause