# PropBench Setup & Troubleshooting Guide

## Häufige Setup-Probleme und Lösungen

### Problem 1: Virtual Environment Aktivierung schlägt fehl (PowerShell)

**Fehlermeldung:**

```
venv-3.11\Scripts\activate.bat : Das Modul "venv-3.11" konnte nicht geladen werden
```

**Ursache:** PowerShell interpretiert den Backslash als Modul-Separator statt als Pfad.

**Lösungen:**

#### Option A: Vollständigen Pfad verwenden

```powershell
.\venv-3.11\Scripts\Activate.ps1
```

#### Option B: In CMD wechseln

```powershell
cmd
venv-3.11\Scripts\activate.bat
```

#### Option C: Ausführungsrichtlinie ändern (falls Activate.ps1 nicht funktioniert)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv-3.11\Scripts\Activate.ps1
```

### Problem 2: Django/Module Import Fehler

**Fehlermeldung:**

```
ModuleNotFoundError: No module named 'jazzmin'
ImportError: Couldn't import Django. Are you sure it's installed?
```

**Ursache:** Das Virtual Environment ist nicht aktiviert oder Dependencies sind nicht installiert.

**Lösung Schritt für Schritt:**

1. **Virtual Environment erstellen und aktivieren:**

```powershell
# PowerShell
python -m venv venv-3.11
.\venv-3.11\Scripts\Activate.ps1

# Oder in CMD
python -m venv venv-3.11
venv-3.11\Scripts\activate.bat
```

2. **Pip upgraden:**

```powershell
python -m pip install --upgrade pip
```

3. **Dependencies installieren:**

```powershell
cd propbench
pip install -r requirements.txt
```

4. **Prüfen ob Virtual Environment aktiv ist:**

```powershell
python -c "import sys; print(sys.prefix)"
# Sollte den venv-3.11 Pfad anzeigen
```

### Problem 3: Pfad-Navigation in PowerShell

**Fehlermeldung:**

```
d:\ : Die Benennung "d:\" wurde nicht als Name eines Cmdlet erkannt
```

**Lösung:**

```powershell
# Korrekte Pfad-Navigation in PowerShell
Set-Location D:\
# Oder einfacher:
cd D:\
```

## Vollständige Setup-Anleitung für Windows

### Voraussetzungen

- Python 3.11 installiert
- Git installiert
- Windows PowerShell oder CMD

### Setup Schritte

1. **Repository klonen:**

```powershell
git clone <repository-url>
cd dictBench
```

2. **Virtual Environment erstellen:**

```powershell
python -m venv venv-3.11
```

3. **Virtual Environment aktivieren:**

```powershell
# PowerShell
.\venv-3.11\Scripts\Activate.ps1

# CMD
venv-3.11\Scripts\activate.bat
```

4. **Pip upgraden:**

```powershell
python -m pip install --upgrade pip
```

5. **Dependencies installieren:**

```powershell
cd propbench
pip install -r requirements.txt
```

6. **Database Migration:**

```powershell
python manage.py migrate
```

7. **Superuser erstellen:**

```powershell
python manage.py createsuperuser
```

8. **Development Server starten:**

```powershell
python manage.py runserver
```

## Debugging Commands

### Virtual Environment prüfen

```powershell
# Prüfen ob venv aktiv ist
python -c "import sys; print(sys.prefix)"

# Installierte Pakete anzeigen
pip list

# Python Version prüfen
python --version
```

### Django Installation prüfen

```powershell
# Django Version prüfen
python -c "import django; print(django.VERSION)"

# Installierte Django Apps prüfen
python manage.py check
```

## PowerShell spezifische Tipps

1. **Ausführungsrichtlinie setzen (falls nötig):**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

2. **Pfade mit Leerzeichen:**

```powershell
cd "C:\Pfad mit Leerzeichen\dictBench"
```

3. **Tab-Completion nutzen:**
   - Nutzen Sie Tab zum automatischen Vervollständigen von Pfaden

## Häufige Fallen

1. **Virtual Environment nicht aktiviert:** Immer prüfen ob (venv-3.11) im Prompt steht
2. **Falsche Python Version:** `python --version` sollte 3.11.x zeigen
3. **Pfad-Probleme:** Verwenden Sie absolute Pfade wenn relative nicht funktionieren
4. **PowerShell vs CMD:** Bei Problemen in PowerShell, CMD ausprobieren

## Weitere Hilfe

Falls weiterhin Probleme auftreten:

1. **Environment Information sammeln:**

```powershell
python --version
pip --version
python -c "import sys; print(sys.prefix)"
pip list | findstr django
```

2. **Clean Setup versuchen:**

```powershell
# Virtual Environment löschen und neu erstellen
rmdir /s venv-3.11
python -m venv venv-3.11
.\venv-3.11\Scripts\Activate.ps1
pip install -r propbench\requirements.txt
```

3. **Log-Dateien prüfen:** Django Fehler sind meist sehr aussagekräftig - komplette Fehlermeldung lesen!
