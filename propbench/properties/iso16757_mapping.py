import json
import os
from django.conf import settings

DEFAULT_FIELD_MAPPINGS = {
    # CSV header (human) -> model field
    'Property type': 'data_type',
    'Data Type': 'data_type',
    'UnitNo': 'unit_of_measurement',
    'Unit': 'unit_of_measurement',
    'Status': 'status',
    'Version number': 'version_number',
    'Revision number': 'revision_number',
    'Creators language': 'creators_language',
    'Country of use': 'countries_of_use',
    'Country of origin': 'country_of_origin',
    'Classification system': 'classification_system',
    'Reference to standard or document': 'classification_reference',
    'Date of creation': 'registration_date',
    'Date of activation': 'registration_date',
    'Reference to VDI 3805 record no': 'registration_authority',
}

# mapping for ISO property-type codes (ISO16757->internal)
DEFAULT_TYPE_MAPPING = {
    '1': 'string',
    '2': 'real',
    '3': 'integer',
    '4': 'boolean',
}


def load_mapping():
    """Return a mapping dict, optionally loaded from a JSON file configured in settings.ISO16757_MAPPING_FILE."""
    mapping = {
        'field_mappings': DEFAULT_FIELD_MAPPINGS,
        'type_mapping': DEFAULT_TYPE_MAPPING,
    }

    path = getattr(settings, 'ISO16757_MAPPING_FILE', None)
    if path:
        try:
            if os.path.isabs(path):
                fp = path
            else:
                # relative to project root
                fp = os.path.join(settings.BASE_DIR, path)
            with open(fp, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                # merge
                mapping['field_mappings'].update(data.get('field_mappings', {}))
                mapping['type_mapping'].update(data.get('type_mapping', {}))
        except Exception:
            # ignore and fall back to defaults
            pass
    return mapping
