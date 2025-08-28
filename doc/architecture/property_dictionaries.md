# ISO 23386 Property Dictionaries Architecture

This document outlines the architecture for supporting multiple property dictionaries in PropBench according to ISO 23386 requirements.

## Overview

ISO 23386 specifies that properties should be organized within property dictionaries. Organizations may need to maintain multiple property dictionaries for different purposes:

- Industry standard dictionaries (e.g., buildingSMART Data Dictionary)
- Regional or national dictionaries
- Company-specific dictionaries
- Project-specific dictionaries
- Domain-specific dictionaries (e.g., HVAC, electrical, structural)

The PropBench system implements a flexible architecture that allows users to:

1. Create multiple property dictionaries
2. Associate properties with specific dictionaries
3. Switch between different dictionaries
4. Apply dictionary-specific validation rules
5. Import/export dictionaries for interchange

## Database Schema

### PropertyDictionary Model

The central model is the `PropertyDictionary` which represents a collection of properties:

```python
class PropertyDictionary(models.Model):
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    registration_authority = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('deprecated', 'Deprecated'),
        ('inactive', 'Inactive')
    ], default='draft')
    is_default = models.BooleanField(default=False)
    
    # Extended attributes
    extended_attributes = models.JSONField(blank=True, null=True)
    
    # System fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_of_activation = models.DateTimeField(blank=True, null=True)
    date_of_deprecation = models.DateTimeField(blank=True, null=True)
    date_of_deactivation = models.DateTimeField(blank=True, null=True)
```

Each property in the system is associated with a specific dictionary through a foreign key relationship:

```python
class Property(models.Model):
    # Other fields...
    dictionary = models.ForeignKey(PropertyDictionary, on_delete=models.CASCADE, 
                                related_name='properties')
```

## Dictionary Management

### Default Dictionary

The system supports marking one dictionary as the default. This is controlled by the `is_default` field and enforced by the model's `save()` method:

```python
def save(self, *args, **kwargs):
    # If this is set as default, unset default flag on all other dictionaries
    if self.is_default:
        PropertyDictionary.objects.filter(is_default=True).update(is_default=False)
    
    # If no dictionaries exist, make this one default
    if not PropertyDictionary.objects.exists():
        self.is_default = True
        
    super().save(*args, **kwargs)
```

### Dictionary Lifecycle

Each dictionary has its own lifecycle with states:

1. **Draft**: Initial state for newly created dictionaries
2. **Active**: Dictionary is approved and available for use
3. **Deprecated**: Dictionary is marked for future removal but still available
4. **Inactive**: Dictionary is no longer available for new properties

The lifecycle is tracked with timestamps:
- `date_of_activation`: When the dictionary became active
- `date_of_deprecation`: When the dictionary was deprecated
- `date_of_deactivation`: When the dictionary became inactive

## User Interface Considerations

The UI should provide:

1. **Dictionary Selector**: A dropdown or similar control to switch between dictionaries
2. **Dictionary Management Interface**: For creating and managing dictionaries
3. **Filter by Dictionary**: Ability to filter properties by their dictionary
4. **Dictionary Status Indicators**: Visual cues for dictionary status (active, deprecated, etc.)

## API Support

The API should include endpoints for:

1. **Dictionary CRUD operations**: Create, read, update, delete dictionaries
2. **Dictionary switching**: Change the default/active dictionary
3. **Dictionary-scoped property queries**: Get properties from a specific dictionary
4. **Dictionary import/export**: Exchange dictionaries with other systems

## Implementation Strategy

When implementing the dictionary architecture:

1. Create the dictionary model first
2. Ensure all property-related models reference the dictionary
3. Add dictionary switching logic in the service layer
4. Implement dictionary selection in the UI
5. Add dictionary import/export functionality