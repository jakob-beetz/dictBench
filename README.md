# PropBench

PropBench is a Django-based collaborative editor system for managing properties according to ISO 23386:2020 standards.

## Features

- ISO 23386 compliant property management
- Multiple property dictionaries support
- Collaborative editing with change request workflow
- Comprehensive audit trail
- Multi-language support
- Import/Export functionality
- RESTful API

## Setup

### Automatisches Setup (Windows)

Für eine einfache Installation unter Windows:

1. **Repository klonen:**

   ```
   git clone https://github.com/yourusername/propbench.git
   cd dictBench
   ```

2. **Setup-Skript ausführen:**

   **PowerShell:**

   ```powershell
   .\setup_windows.ps1
   ```

   **CMD:**

   ```cmd
   setup_windows.bat
   ```

3. **Superuser erstellen:**

   ```
   python manage.py createsuperuser
   ```

4. **Development Server starten:**
   ```
   python manage.py runserver
   ```

### Manuelles Setup

1. **Repository klonen:**

   ```
   git clone https://github.com/yourusername/propbench.git
   cd dictBench
   ```

2. **Python 3.11 installieren** und sicherstellen, dass `python.exe` im PATH ist.

3. **Virtual Environment erstellen:**

   ```
   python -m venv venv-3.11
   ```

4. **Virtual Environment aktivieren:**

   **CMD:**

   ```cmd
   venv-3.11\Scripts\activate.bat
   ```

   **PowerShell:**

   ```powershell
   .\venv-3.11\Scripts\Activate.ps1
   ```

   Bei PowerShell-Problemen siehe [Setup Troubleshooting](SETUP_TROUBLESHOOTING.md).

5. **Dependencies installieren:**

   ```
   cd propbench
   pip install -r requirements.txt
   ```

6. **Database Migration:**

   ```
   python manage.py migrate
   ```

7. **Superuser erstellen:**

   ```
   python manage.py createsuperuser
   ```

8. **Development Server starten:**

   ```
   python manage.py runserver
   ```

9. **Admin Interface öffnen:** `http://127.0.0.1:8000/admin/`

## Project Structure

- **accounts**: User management and authentication
- **properties**: Core property models and logic
- **groups**: Group models and hierarchical organization
- **requests**: Change request workflow
- **audit**: Comprehensive audit trail
- **import_export**: Bulk import/export functionality
- **dictionaries**: Property dictionary management

## License

MIT

## Contributors

RWTH Aachen University - Chair of Design Comptuation

---

### Troubleshooting

Bei Setup-Problemen siehe die detaillierte [Setup Troubleshooting Anleitung](SETUP_TROUBLESHOOTING.md).

**Häufige Probleme:**

- **PowerShell Aktivierung fehlgeschlagen:** Nutzen Sie CMD oder ändern Sie die Ausführungsrichtlinie
- **Module nicht gefunden:** Virtual Environment nicht aktiviert oder Dependencies nicht installiert
- **Django Import Fehler:** `pip install -r requirements.txt` im aktivierten venv ausführen

**Quick Fixes:**

- Virtual Environment prüfen: `python -c "import sys; print(sys.prefix)"`
- Dependencies neu installieren: `pip install -r propbench\requirements.txt`
- Clean Setup: venv-3.11 Ordner löschen und neu erstellen
