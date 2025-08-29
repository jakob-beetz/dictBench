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

2. Create and activate a virtual environment
   ```
   python -m venv venv-3.11
   # On Windows:
   .\venv-3.11\Scripts\activate.ps1
   # On Unix/macOS:
   source venv-3.11/bin/activate
   ```

3. Install dependencies
   ```
   pip install -r propbench/requirements.txt
   ```

4. Apply migrations
   ```
   cd propbench
   python manage.py migrate
   ```

5. Create a superuser
   ```
   python manage.py createsuperuser
   ```

6. Run the development server
   ```
   python manage.py runserver
   ```

7. Access the admin interface at `http://127.0.0.1:8000/admin/`

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