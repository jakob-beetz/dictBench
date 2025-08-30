# Property Grid Manager

A comprehensive Tabulator-based grid interface for managing properties with advanced features including versioning, fuzzy search, and bulk operations.

## 🚀 Features

### Core Functionality
- **Advanced Grid View**: Interactive Tabulator-based grid with sorting, filtering, and pagination
- **CRUD Operations**: Create, read, update, delete properties with instant feedback
- **Bulk Operations**: Select multiple properties and perform batch operations
- **Fuzzy Search**: Intelligent search across all fields with partial matching
- **Real-time Updates**: Changes are saved automatically and reflected immediately

### Versioning & History
- **Complete Version Tracking**: Every change is tracked with timestamps and user info
- **Version History View**: Browse through all changes with detailed diff information
- **Undo/Redo**: Built-in undo/redo stack for reverting changes
- **Version Restoration**: Restore any previous version of a property

### Search & Filtering
- **Global Fuzzy Search**: Search across all fields with intelligent matching
- **Column-specific Filters**: Filter by specific columns with autocomplete
- **Field-specific Search**: Fuzzy search for units, quantities, and classifications
- **Smart Suggestions**: Auto-complete for frequently used values

### Import/Export
- **Multiple Export Formats**: CSV, Excel, JSON, PDF export options
- **ISO 16757 Import**: Specialized import for ISO 16757 standard files
- **Bulk Import**: Import hundreds of properties with validation and error handling

## 📋 Prerequisites

```bash
# Required Python packages
pip install fuzzywuzzy[speedup]
pip install python-levenshtein
```

## 🛠 Installation & Setup

### 1. Run Setup Command
```bash
python manage.py setup_property_grid --install-deps
```

This will:
- Install required dependencies
- Create demo data for testing
- Set up sample physical quantities
- Verify all components are working

### 2. Access the Grid Manager

Navigate to your Django admin:
1. Go to `/admin/properties/property/`
2. Click the **"Grid Manager"** button
3. Start managing your properties!

## 📖 Usage Guide

### Basic Operations

#### Adding Properties
1. Click **"Add Property"** button
2. Fill in property details:
   - Property names (multiple languages supported)
   - Data type (string, real, integer, boolean)
   - Unit of measurement (with autocomplete)
   - Status, dictionary, and other metadata
3. Click **"Save Changes"**

#### Editing Properties
- **Single Edit**: Click on any property name or use the edit button
- **Inline Edit**: Some fields support direct editing in the grid
- **Bulk Edit**: Select multiple properties and use bulk operations

#### Searching & Filtering
- **Global Search**: Use the search box at the top for fuzzy search across all fields
- **Column Filters**: Use the filter inputs in column headers
- **Field-specific Search**: Search units, quantities, and classifications with autocomplete

### Advanced Features

#### Version Management
1. Select a property and click **"Version History"**
2. Browse through all changes with timestamps and user info
3. Click **"Restore Version"** to revert to any previous state
4. Use **Undo/Redo** buttons for quick reversals

#### Bulk Operations
1. Select multiple properties using checkboxes
2. Click **"Bulk Edit"** button
3. Choose operation:
   - **Status Changes**: Activate, deprecate, or mark as draft
   - **Dictionary Changes**: Move properties to different dictionaries
   - **Classification**: Set classification references
   - **Delete**: Remove multiple properties

#### Export Data
1. Select properties (or leave empty for all)
2. Click **"Export"** button
3. Choose format: CSV, Excel, JSON, or PDF
4. Download starts automatically

### Fuzzy Search Examples

The grid includes intelligent fuzzy search that works even with typos:

```
Search: "temprature" → Finds: "Temperature"
Search: "presr" → Finds: "Pressure"
Search: "kwhr" → Finds: "kWh"
Search: "manufact" → Finds: "Manufacturer"
```

### Keyboard Shortcuts

- **Ctrl+A**: Select all visible properties
- **Delete**: Delete selected properties (with confirmation)
- **Ctrl+Z**: Undo last action
- **Ctrl+Y**: Redo last action
- **Escape**: Close current modal/dialog

## 🔧 Configuration

### Customizing Columns

Edit `property_grid.html` to modify columns:

```javascript
columns: [
    {
        title: "Your Custom Column",
        field: "your_field",
        formatter: function(cell) {
            // Custom formatting
            return `<span>${cell.getValue()}</span>`;
        },
        headerFilter: "input",
        width: 150
    }
]
```

### Adding Custom Bulk Operations

Add to `bulk_edit_properties` view in `grid_views.py`:

```python
elif action == 'your-custom-action':
    custom_value = data.get('custom_value')
    modified_count = properties.update(
        your_field=custom_value,
        updated_by=request.user,
        updated_at=timezone.now()
    )
```

### Extending Fuzzy Search

Add new search endpoints in `grid_views.py`:

```python
@staff_member_required
def search_custom_field(request):
    query = request.GET.get('q', '').strip()
    # Your custom search logic
    return JsonResponse({'results': matches})
```

## 🐛 Troubleshooting

### Common Issues

1. **Grid Not Loading**
   - Check browser console for JavaScript errors
   - Verify Tabulator CDN is accessible
   - Ensure CSRF token is properly set

2. **Fuzzy Search Not Working**
   - Install: `pip install fuzzywuzzy[speedup]`
   - Install: `pip install python-levenshtein`
   - Restart Django server

3. **Bulk Operations Failing**
   - Check Django logs for detailed error messages
   - Verify user has proper permissions
   - Ensure database constraints are met

### Performance Tips

1. **Large Datasets**: Use pagination and server-side filtering
2. **Memory Usage**: Limit version history to last 50 changes
3. **Search Speed**: Install `python-levenshtein` for faster fuzzy matching

## 📊 API Endpoints

### Grid Data
```
GET /admin/properties/property/api/grid-data/
```
Parameters: `search`, `page`, `size`, `sort`, `dir`

### CRUD Operations
```
POST /admin/properties/property/api/create/
PUT /admin/properties/property/api/<id>/update/
DELETE /admin/properties/property/api/<id>/delete/
```

### Bulk Operations
```
POST /admin/properties/property/api/bulk-edit/
```
Body: `{"action": "activate", "property_ids": [...]}`

### Search Endpoints
```
GET /admin/properties/property/api/search/units/?q=search_term
GET /admin/properties/property/api/search/quantities/?q=search_term
GET /admin/properties/property/api/search/classifications/?q=search_term
```

### Version Management
```
GET /admin/properties/property/api/<id>/versions/
POST /admin/properties/property/api/restore-version/<version_id>/
```

## 🎨 Customization

The grid is highly customizable. Key files to modify:

- **Templates**: `templates/admin/properties/property_grid.html`
- **Styles**: CSS within the template or separate file
- **JavaScript**: `property_grid_script.js` for behavior
- **Backend**: `grid_views.py` for API endpoints
- **Models**: Extend Property model for additional fields

## 📈 Performance Metrics

The grid is optimized for:
- **Loading**: < 2 seconds for 1000+ properties
- **Search**: < 500ms for fuzzy search across all fields
- **Updates**: Real-time updates with optimistic UI
- **Memory**: Efficient pagination and lazy loading

## 🔒 Security

- **CSRF Protection**: All API calls include CSRF tokens
- **Permission Checks**: Staff member required for all operations
- **Input Validation**: Server-side validation for all inputs
- **Audit Trail**: Complete version history for compliance

## 📞 Support

For issues or feature requests:
1. Check the troubleshooting section above
2. Review Django admin logs
3. Check browser console for JavaScript errors
4. Verify all dependencies are installed

---

**Happy Property Management!** 🎉