# PropBench Windows Setup Script
# Dieses Skript automatisiert das Setup für Windows Benutzer

Write-Host "PropBench Setup Script für Windows" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Prüfen ob Python installiert ist
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python gefunden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "FEHLER: Python nicht gefunden. Bitte Python 3.11 installieren." -ForegroundColor Red
    exit 1
}

# Prüfen ob wir im richtigen Verzeichnis sind
if (-not (Test-Path "propbench\manage.py")) {
    Write-Host "FEHLER: manage.py nicht gefunden. Bitte im dictBench Hauptverzeichnis ausführen." -ForegroundColor Red
    exit 1
}

Write-Host "`nSchritt 1: Virtual Environment erstellen..." -ForegroundColor Yellow
if (Test-Path "venv-3.11") {
    Write-Host "Virtual Environment existiert bereits." -ForegroundColor Blue
} else {
    python -m venv venv-3.11
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FEHLER: Virtual Environment konnte nicht erstellt werden." -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual Environment erfolgreich erstellt." -ForegroundColor Green
}

Write-Host "`nSchritt 2: Virtual Environment aktivieren..." -ForegroundColor Yellow
& ".\venv-3.11\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNUNG: PowerShell Aktivierung fehlgeschlagen. Versuche es manuell:" -ForegroundColor Yellow
    Write-Host "Führe aus: .\venv-3.11\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "Falls das nicht funktioniert: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
    Write-Host "Oder nutze CMD: venv-3.11\Scripts\activate.bat" -ForegroundColor Cyan
}

Write-Host "`nSchritt 3: Pip upgraden..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host "`nSchritt 4: Dependencies installieren..." -ForegroundColor Yellow
Set-Location propbench
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Dependencies konnten nicht installiert werden." -ForegroundColor Red
    Write-Host "Versuche es manuell: cd propbench && pip install -r requirements.txt" -ForegroundColor Cyan
    exit 1
}

Write-Host "`nSchritt 5: Database Migration..." -ForegroundColor Yellow
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Migration fehlgeschlagen. Installiere fehlende Pakete..." -ForegroundColor Yellow
    pip install django-debug-toolbar django-json-widget
    Write-Host "Versuche Migration erneut..." -ForegroundColor Yellow
    python manage.py migrate
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FEHLER: Migration immer noch fehlgeschlagen." -ForegroundColor Red
        Write-Host "Siehe MIGRATION_FIX.md für weitere Hilfe." -ForegroundColor Cyan
        exit 1
    }
}

Write-Host "`nSetup erfolgreich abgeschlossen!" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host "`nNächste Schritte:" -ForegroundColor Cyan
Write-Host "1. Superuser erstellen: python manage.py createsuperuser" -ForegroundColor White
Write-Host "2. Development Server starten: python manage.py runserver" -ForegroundColor White
Write-Host "3. Im Browser öffnen: http://127.0.0.1:8000/admin/" -ForegroundColor White

Write-Host "`nFalls Probleme auftreten, siehe: SETUP_TROUBLESHOOTING.md" -ForegroundColor Yellow