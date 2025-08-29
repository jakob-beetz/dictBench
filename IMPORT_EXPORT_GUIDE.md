# PropBench Import/Export System Setup Guide

## Overview
This system provides comprehensive import/export capabilities for Properties and Property Groups with:
- ISO 23386 PA code compliance
- ISO 16757 data format support  
- Transaction management and rollback capabilities
- User tracking and audit trails
- Automatic field categorization and JSON storage

## Installation

### 1. Install Required Packages
```bash
pip install -r requirements-import-export.txt
```

### 2. Add to Django Settings
Add to your `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... existing apps
    'import_export',
    'reversion',
    # ... your apps
]

# Add middleware for reversion
MIDDLEWARE = [
    # ... existing middleware
    'reversion.middleware.RevisionMiddleware',
]
```

### 3. Run Migrations
```bash
python manage.py migrate
python manage.py migrate reversion
```

### 4. Create Superuser (if needed)
```bash
python manage.py createsuperuser
```

## Usage

### Admin Interface Import
1. Go to Django Admin → Property Groups
2. Click "Import CSV" or "Import ISO 16757" buttons
3. Select target dictionary
4. Upload CSV file
5. Review results

### Management Command Import
```bash
# Analyze CSV structure only
python manage.py import_iso16757 --analyze

# Import data
python manage.py import_iso16757 --import --dictionary "Heat Pumps" --user admin

# Specify custom data directory
python manage.py import_iso16757 --analyze --data-dir "/path/to/csv/files"
```

### Programmatic Import
```python
from groups.admin_basic import PropertyGroupAdmin
from django.contrib.auth import get_user_model

# Create admin instance
admin = PropertyGroupAdmin(PropertyGroup, admin.site)

# Process import (example)
# This would typically be called from a view or command
```

## Data Mapping

### ISO 23386 PA Code Mapping
- **PA001**: Dictionary assignment
- **PA002**: Version number  
- **PA003**: Revision number
- **PA004**: Data type
- **PA005**: Unit of measurement
- **PA006**: Property groups
- **PA007**: Value domain
- **PA008**: Physical quantity
- **PA011-012**: Classification system/reference
- **PA016-020**: Status and authority info
- **PA021-025**: Geographic and localization

### Field Categorization
The system automatically categorizes CSV columns:

1. **Core Fields** → Direct model fields
2. **ISO 16757 Fields** → `extended_attributes` (JSON)
3. **Identifier Fields** → `metadata.identifiers` (JSON)
4. **Calculation Fields** → `metadata.calculations` (JSON) 
5. **Other Fields** → `metadata.custom_attributes` (JSON)

### Example CSV Structure
```csv
name,description,type,iso_class_id,internal_id,calc_method,custom_note
"Thermal Properties","Heat-related properties","functional","HP001","TH_001","ASHRAE","Custom note"
```

Results in:
- `name`: "Thermal Properties" → Core field
- `description`: "Heat-related properties" → Core field  
- `type`: "functional" → Core field
- `iso_class_id`: "HP001" → `extended_attributes`
- `internal_id`: "TH_001" → `metadata.identifiers`
- `calc_method`: "ASHRAE" → `metadata.calculations`
- `custom_note`: "Custom note" → `metadata.custom_attributes`

## Transaction Management

### Automatic Rollback
- All imports use Django transactions
- Any error during import rolls back all changes
- No partial imports - all or nothing

### Version Control (with django-reversion)
```python
# View change history
from reversion.models import Version
versions = Version.objects.get_for_object(property_group)

# Rollback to previous version
version = versions[1]  # Second most recent
version.revert()
```

### Manual Rollback
```bash
# Database-level rollback (if needed)
# Note: This requires database-specific tools
# PostgreSQL example:
# BEGIN; -- start transaction
# ... run import ...  
# ROLLBACK; -- undo if issues found
```

## Monitoring and Debugging

### Import Logs
Check Django admin messages and logs for:
- Number of records processed
- Success/failure counts  
- Specific error details
- Field mapping information

### Data Validation
- Check `extended_attributes` and `metadata` fields for JSON validity
- Verify PA code compliance in stored data
- Review user tracking fields (`created_by`, `updated_by`)

### Common Issues
1. **CSV Encoding**: Use UTF-8 encoding for international characters
2. **Empty Fields**: Empty strings vs NULL values - system handles both
3. **Large Files**: For files >1000 rows, consider chunked processing
4. **Memory Usage**: Monitor memory for very large imports

## Advanced Features

### Custom Field Processors
Extend the admin classes to add custom field processing:
```python
class CustomPropertyGroupAdmin(PropertyGroupAdmin):
    def _extract_extended_attributes(self, row):
        # Custom logic here
        return super()._extract_extended_attributes(row)
```

### Validation Rules  
Add custom validation before import:
```python
def validate_import_data(self, row):
    if not row.get('name'):
        raise ValueError("Name is required")
    # Add more validation
```

### Export Functionality
The system supports export back to CSV:
```python
# In admin interface
# Select objects → Actions → Export selected items
```

## Security Considerations
- Only staff users can import data
- All imports are tracked by user
- Transactions prevent partial/corrupted imports
- Version control allows rollbacks

## Performance Tips
- Use chunked imports for large files (>10MB)
- Consider background tasks for very large imports
- Monitor database locks during import
- Use database indexes on frequently queried fields

## Support and Troubleshooting
1. Check Django logs for detailed error messages
2. Verify CSV format matches expected structure  
3. Test with small sample files first
4. Use --analyze flag to understand data structure
5. Ensure proper permissions for import user