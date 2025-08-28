# PropBench Developer Guide

This guide provides a quick overview of the PropBench project structure and development workflow.

## Project Overview

PropBench is a Django-based system that implements ISO 23386:2020 for property management. The system allows for collaborative editing of properties with a structured workflow.

## Project Structure

```
propbench/
├── accounts/         # User management
├── properties/       # Core property models
├── groups/           # Property grouping
├── requests/         # Change request workflow
├── audit/            # Audit trail
├── import_export/    # Import/export functionality
├── dictionaries/     # Property dictionary management
└── propbench/        # Project settings
```

## Getting Started

1. Set up your development environment:
   - Windows: Run `.\setup.ps1`
   - Unix/macOS: Run `bash setup.sh`

2. Access the admin interface at `http://127.0.0.1:8000/admin/`

## Key Components

### Models

- **User**: Custom user model with expert and admin roles
- **Property**: Core model with ISO 23386 attributes
- **PropertyDictionary**: Collection of properties
- **PropertyGroup**: Hierarchical organization
- **ChangeRequest**: Workflow implementation

### Workflow

The system implements a workflow for property changes:

1. Users create change requests
2. Experts review and validate
3. Admins approve and activate
4. Full audit trail is maintained

## Development Guidelines

### Adding Features

1. Create models in the appropriate app
2. Add admin interface registration
3. Create serializers for API access
4. Add views and URL patterns
5. Update tests

### Database Migrations

When changing models:

```
python manage.py makemigrations
python manage.py migrate
```

### Running Tests

```
python manage.py test
```

## API Documentation

The REST API provides endpoints for:

- User management
- Property CRUD operations
- Change request workflow
- Dictionary management

## Contributing

1. Create a feature branch
2. Implement your changes
3. Add tests
4. Submit a pull request

## Troubleshooting

- Check logs in the `logs/` directory
- Ensure database migrations are up to date
- Verify virtual environment is activated
