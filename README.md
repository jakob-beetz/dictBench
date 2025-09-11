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

1. Clone the repository

   ```
   git clone https://github.com/yourusername/propbench.git
   cd propbench
   ```

2. Install Python 3.11 and make sure that the path to `python.exe` (e.g. `C:\Users\<username>\AppData\Local\Programs\Python\Python311`) is at the top of your PATH environment variable.

3. Create the virtual environment explicitly with Python 3.11:

   ```
   "C:\Users\<username>\AppData\Local\Programs\Python\Python311\python.exe" -m venv venv-3.11
   ```

4. Activate the venv (Windows CMD):

   ```
   venv-3.11\Scripts\activate.bat
   ```

   (For PowerShell: `venv-3.11\Scripts\Activate.ps1`)

5. Install the dependencies:

   ```
   pip install -r propbench/requirements.txt
   ```

6. If you get errors about missing packages when running `python manage.py migrate`, install them manually, e.g.:

   ```
   pip install django-debug-toolbar django-json-widget
   ```

   Repeat this for any other missing packages reported.

7. Apply migrations

   ```
   cd propbench
   python manage.py migrate
   ```

8. Create a superuser

   ```
   python manage.py createsuperuser
   ```

9. Run the development server

   ```
   python manage.py runserver
   ```

10. Access the admin interface at `http://127.0.0.1:8000/admin/`

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

- If after activating the venv you still see the wrong Python version, check your PATH variable and use the full path to Python 3.11.
- For any error about missing modules, simply install the named package with `pip install <packagename>`.
