# Schnellhilfe für Migration-Fehler

## Problem: ModuleNotFoundError bei Migration

Falls beim Ausführen von `python manage.py migrate` folgende Fehler auftreten:

- `ModuleNotFoundError: No module named 'debug_toolbar'`
- `ModuleNotFoundError: No module named 'django_json_widget'`

## Sofortige Lösung:

1. **Fehlende Pakete installieren:**

   ```cmd
   pip install django-debug-toolbar django-json-widget
   ```

2. **Migration erneut versuchen:**
   ```cmd
   python manage.py migrate
   ```

## Langfristige Lösung:

Die `requirements.txt` wurde aktualisiert. Bei einem Clean Setup werden diese Pakete automatisch installiert.

## Für neue Benutzer:

```cmd
git pull origin Erich
# Dann clean setup:
rmdir /s venv-3.11
python -m venv venv-3.11
venv-3.11\Scripts\activate.bat
cd propbench
pip install -r requirements.txt
python manage.py migrate
```
