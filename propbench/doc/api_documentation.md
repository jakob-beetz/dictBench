# PropBench REST API Documentation

This document provides information about the REST API endpoints for PropBench, focusing on Groups and Properties with active dictionary requirements.

## Authentication

All API endpoints require authentication. Use the built-in Django session authentication or provide authentication credentials in the headers.

## Common Parameters

- `dictionary`: UUID of the dictionary to filter by. If not provided, the default dictionary will be used.

## Properties API

### List Properties

```
GET /api/properties/
```

Query Parameters:
- `dictionary`: Filter properties by dictionary UUID
- `status`: Filter by property status (draft, active, deprecated, etc.)
- `data_type`: Filter by data type (string, integer, real, boolean, complex)
- `search`: Search in property names, definitions, and unit of measurement

### Get Property Details

```
GET /api/properties/{guid}/
```

### Create Property

```
POST /api/properties/
```

Required fields:
- `data_type`: Type of the property data

Optional fields:
- `dictionary`: UUID of the dictionary to assign the property to. If not provided, the default dictionary will be used.
- `names`: List of property names in different languages
- `definitions`: List of property definitions in different languages
- And any other property fields from the model

### Update Property

```
PUT/PATCH /api/properties/{guid}/
```

### Delete Property

```
DELETE /api/properties/{guid}/
```

### Property History

```
GET /api/properties/{guid}/history/
```

View the audit history for a property.

## Groups API

### List Groups

```
GET /api/groups/
```

Query Parameters:
- `dictionary`: Filter groups by dictionary UUID
- `type`: Filter by group type (class, domain, reference_document, etc.)
- `parent_group`: Filter by parent group UUID
- `search`: Search in group names and descriptions

### Get Group Details

```
GET /api/groups/{guid}/
```

### Create Group

```
POST /api/groups/
```

Required fields:
- `name`: Name of the group
- `type`: Type of the group

Optional fields:
- `dictionary`: UUID of the dictionary to assign the group to. If not provided, the default dictionary will be used.
- `description`: Description of the group
- `parent_group`: UUID of the parent group
- `names`: List of group names in different languages
- And any other group fields from the model

### Update Group

```
PUT/PATCH /api/groups/{guid}/
```

### Delete Group

```
DELETE /api/groups/{guid}/
```

### Group History

```
GET /api/groups/{guid}/history/
```

View the audit history for a group.

### Add Properties to Group

```
POST /api/groups/{guid}/add_properties/
```

Required fields:
- `property_ids`: List of property UUIDs to add to the group

Optional fields:
- `is_required`: Boolean indicating if the properties are required in the group

Note: Properties must be from the same dictionary as the group.

### Remove Properties from Group

```
POST /api/groups/{guid}/remove_properties/
```

Required fields:
- `property_ids`: List of property UUIDs to remove from the group

## Dictionaries API

### List Dictionaries

```
GET /api/dictionaries/
```

### Get Dictionary Details

```
GET /api/dictionaries/{guid}/
```

### Create Dictionary

```
POST /api/dictionaries/
```

### Update Dictionary

```
PUT/PATCH /api/dictionaries/{guid}/
```

### Delete Dictionary

```
DELETE /api/dictionaries/{guid}/
```

## Important Notes

1. All create and update operations require authentication.
2. For both Groups and Properties, an active dictionary must be specified in the request or the system will use the default dictionary.
3. Properties can only be added to groups within the same dictionary.
4. All operations are audited and history can be viewed through the history endpoints.
