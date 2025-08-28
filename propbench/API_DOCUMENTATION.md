# PropBench API Documentation

## Authentication

All API endpoints require authentication. You can authenticate using:

1. Session-based authentication (for browser access)
2. Token-based authentication (for programmatic access)

## API Endpoints

### Dictionary Endpoints

- `GET /api/dictionaries/` - List all dictionaries
- `POST /api/dictionaries/` - Create a new dictionary
- `GET /api/dictionaries/{guid}/` - Retrieve a specific dictionary
- `PUT /api/dictionaries/{guid}/` - Update a dictionary
- `DELETE /api/dictionaries/{guid}/` - Delete a dictionary
- `POST /api/dictionaries/{guid}/set_default/` - Set a dictionary as default

### Property Group Endpoints

- `GET /api/groups/` - List all property groups
- `GET /api/groups/?dictionary_id={guid}` - List property groups for a specific dictionary
- `POST /api/groups/` - Create a new property group (requires dictionary_id)
- `GET /api/groups/{guid}/` - Retrieve a specific property group
- `PUT /api/groups/{guid}/` - Update a property group
- `DELETE /api/groups/{guid}/` - Delete a property group

### Property Endpoints

- `GET /api/properties/` - List all properties
- `GET /api/properties/?dictionary_id={guid}` - List properties for a specific dictionary
- `POST /api/properties/` - Create a new property (requires dictionary_id)
- `GET /api/properties/{guid}/` - Retrieve a specific property
- `PUT /api/properties/{guid}/` - Update a property
- `DELETE /api/properties/{guid}/` - Delete a property

## Examples

### Creating a Dictionary

```json
POST /api/dictionaries/
{
    "name": "Building Components Dictionary",
    "description": "Standard property dictionary for building components",
    "registration_authority": "PropBench Organization",
    "version": "1.0",
    "status": "draft",
    "is_default": true
}
```

### Creating a Property Group

```json
POST /api/groups/
{
    "name": "Wall Components",
    "description": "Properties related to wall components and materials",
    "type": "classification",
    "dictionary_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

### Creating a Property

```json
POST /api/properties/
{
    "data_type": "real",
    "unit_of_measurement": "mm",
    "status": "draft",
    "dictionary_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "names": [
        {
            "name": "Wall Thickness",
            "language": "en"
        },
        {
            "name": "Wanddicke",
            "language": "de"
        }
    ],
    "definitions": [
        {
            "definition": "The measured thickness of a wall element",
            "language": "en"
        }
    ]
}
```