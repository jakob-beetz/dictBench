import csv
import io
import time
import json
from django.utils import timezone
from django.db import transaction
from .iso16757_mapping import load_mapping
from .models import Property, PropertyName, PropertyDefinition, PhysicalQuantity, PropertyExample, PropertyDescription
import reversion


mapping = load_mapping()


def _detect_delimiter(sample):
    return ';' if sample.count(';') > sample.count(',') else ','


def parse_and_import(fileobj, dictionary, user, delimiter=None, dry_run=False):
    """Parse ISO16757 CSV file-like and import rows using process_row.
    Returns stats dict.
    """
    if hasattr(fileobj, 'read'):
        raw = fileobj.read()
        if isinstance(raw, bytes):
            decoded = raw.decode('utf-8-sig')
        else:
            decoded = raw
    else:
        decoded = str(fileobj)

    sample = decoded[:2048]
    if not delimiter:
        delimiter = _detect_delimiter(sample)

    sio = io.StringIO(decoded)
    reader = csv.reader(sio, delimiter=delimiter)

    # read header and optional pa-tag second row
    try:
        header = next(reader)
    except StopIteration:
        return {'created': 0, 'updated': 0, 'skipped': 0, 'errors': ['empty file']}

    # attempt to read second row - if it looks like PA tags (contains 'PA' tokens) assume it's the tag row
    pa_tags = None
    try:
        second_row = next(reader)
        if any((cell or '').strip().upper().startswith('PA') for cell in second_row if cell):
            pa_tags = {h: t for h, t in zip(header, second_row)}
        else:
            # not a tag row: rewind
            sio.seek(0)
            reader = csv.DictReader(sio, delimiter=delimiter)
            pa_tags = {}
    except StopIteration:
        sio.seek(0)
        reader = csv.DictReader(sio, delimiter=delimiter)
        pa_tags = {}

    # If we have pa_tags, rebuild DictReader using header row
    if pa_tags:
        # position stream after first two rows
        sio.seek(0)
        _ = sio.readline()
        _ = sio.readline()
        reader = csv.DictReader(sio, fieldnames=header, delimiter=delimiter)

    stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': []}

    # process rows
    rownum = 2 if pa_tags else 1
    for row in reader:
        rownum += 1
        # skip empty rows
        if not any((v or '').strip() for v in row.values()):
            continue
        try:
            with transaction.atomic():
                result = process_row(row, dictionary, user, pa_tags=pa_tags)
                stats[result] += 1
        except Exception as e:
            stats['errors'].append(f'Row {rownum}: {e}')
            stats['skipped'] += 1
    return stats


def process_row(row, dictionary, user, pa_tags=None):
    """Process a single CSV Dict row and create/update Property.
    pa_tags: optional mapping header->PA tag
    """
    # helper mapping
    field_mappings = mapping.get('field_mappings', {})
    type_mapping = mapping.get('type_mapping', {})

    # get property id / PA code
    property_id = (row.get('Property ID') or row.get('PA001.1') or '').strip()
    property_type_raw = (row.get('Property type') or row.get('Data Type') or '').strip()

    core = {}
    # map fields using mapping
    for hdr, model_field in field_mappings.items():
        if hdr in row and row[hdr] and str(row[hdr]).strip() != '':
            core[model_field] = row[hdr].strip()

    # data_type mapping
    if property_type_raw:
        core['data_type'] = type_mapping.get(property_type_raw, property_type_raw)
    else:
        core['data_type'] = core.get('data_type', 'string')

    # unit
    if 'unit_of_measurement' in core:
        core['unit_of_measurement'] = core['unit_of_measurement']

    # physical quantity handling
    quantity_id = row.get('QuantityID') or row.get('physical_quantity')
    if quantity_id:
        qid = str(quantity_id).strip()
        if qid:
            pq, _ = PhysicalQuantity.objects.get_or_create(name=qid, defaults={'description': f'Imported PQ {qid}'})
            core['physical_quantity'] = pq

    # build extended / iso attrs
    iso_attrs = {}
    custom_attrs = {}
    pa_code_data = {}

    for k, v in row.items():
        if not v or str(v).strip() == '':
            continue
        val = str(v).strip()
        # use pa tag when present
        pa_tag = (pa_tags.get(k) if pa_tags and k in pa_tags else None)
        # key_for_meta = pa_tag or k

        # multilingual names/definitions
        lk = k.lower()
        if lk.startswith('names in language'):
            lang = k.split()[-1]
            # do not create PropertyName before Property exists; collect into metadata instead
            iso_attrs.setdefault('names', {})[lang] = val
        elif lk.startswith('definitions in language') or lk.startswith('descriptions in language'):
            lang = k.split()[-1]
            iso_attrs.setdefault('definitions', {})[lang] = val
        elif any(token in k.lower() for token in ('method of measurement', 'method', 'measurement')):
            custom_attrs['method_of_measurement'] = val
        elif k in ('Replaces', 'Replaced by'):
            pa_code_data[k] = val
        else:
            # place into iso_attrs by pa_tag if available
            if pa_tag:
                pa_code_data[pa_tag] = val
            else:
                custom_attrs[k] = val

    # add original_property_id
    if property_id:
        iso_attrs['original_property_id'] = property_id

    # build metadata structure
    import_metadata = {
        'import_source': 'ISO_16757',
        'import_date': str(timezone.now()),
        'import_user': user.username,
        'original_property_id': property_id,
    }

    metadata = {
        'import_metadata': import_metadata,
        'pa_code_data': pa_code_data,
        'custom_attributes': custom_attrs,
    }

    # Find existing property
    prop = None
    created = False
    # Perform DB writes and related creations inside a reversion revision
    with reversion.create_revision():
        if property_id:
            prop = Property.objects.filter(pa_code=property_id).first()

        if prop:
            # update
            for f, val in core.items():
                if f == 'physical_quantity' and val:
                    setattr(prop, f, val)
                elif f != 'dictionary':
                    setattr(prop, f, val)
            prop.extended_attributes = iso_attrs or None
            prop.metadata = metadata
            prop.updated_by = user
            prop.save()
        else:
            # try lookup by dictionary + data_type + unit
            lookup = {'dictionary': dictionary, 'data_type': core.get('data_type', 'string'), 'unit_of_measurement': core.get('unit_of_measurement', '')}
            if core.get('version_number'):
                lookup['version_number'] = core.get('version_number')
            existing = Property.objects.filter(**lookup)
            if existing.exists():
                # pick one and update if original_property_id matches
                found = None
                for p in existing[:5]:
                    attrs = p.extended_attributes or {}
                    if attrs.get('original_property_id') == property_id:
                        found = p
                        break
                if found:
                    prop = found
                    created = False
                    prop.extended_attributes = iso_attrs or None
                    prop.metadata = metadata
                    prop.updated_by = user
                    prop.save()
                else:
                    unique_suffix = str(int(time.time()))[-6:]
                    prop = Property.objects.create(
                        dictionary=dictionary,
                        data_type=core.get('data_type', 'string'),
                        unit_of_measurement=core.get('unit_of_measurement', ''),
                        version_number=f"{core.get('version_number', '1')}-{unique_suffix}",
                        status=core.get('status', 'active'),
                        pa_code=property_id or None,
                        extended_attributes=iso_attrs or None,
                        metadata=metadata,
                        created_by=user,
                        updated_by=user,
                    )
                    created = True
            else:
                prop = Property.objects.create(
                    dictionary=dictionary,
                    data_type=core.get('data_type', 'string'),
                    unit_of_measurement=core.get('unit_of_measurement', ''),
                    status=core.get('status', 'active'),
                    version_number=core.get('version_number', '1'),
                    pa_code=property_id or None,
                    extended_attributes=iso_attrs or None,
                    metadata=metadata,
                    created_by=user,
                    updated_by=user,
                )
                created = True

        # Attach multilingual names and definitions after property exists
        # create from iso_attrs collected earlier
        try:
            for lang, text in (iso_attrs.get('names') or {}).items():
                PropertyName.objects.get_or_create(property=prop, name=text, language=lang)
        except Exception:
            pass

        try:
            for lang, text in (iso_attrs.get('definitions') or {}).items():
                PropertyDefinition.objects.get_or_create(property=prop, definition=text, language=lang)
        except Exception:
            pass

        # Also create from explicit columns if present
        for k, v in row.items():
            if not v or str(v).strip() == '':
                continue
            lk = k.lower()
            if lk.startswith('names in language'):
                lang = k.split()[-1]
                PropertyName.objects.get_or_create(property=prop, name=v.strip(), language=lang)
            if lk.startswith('definitions in language') or lk.startswith('descriptions in language'):
                lang = k.split()[-1]
                PropertyDefinition.objects.get_or_create(property=prop, definition=v.strip(), language=lang)
            if lk.startswith('examples in language'):
                lang = k.split()[-1]
                PropertyExample.objects.get_or_create(property=prop, example=v.strip(), language=lang)
            if lk.startswith('descriptions in language'):
                lang = k.split()[-1]
                PropertyDescription.objects.get_or_create(property=prop, description=v.strip(), language=lang)

        # Handle Replaces / Replaced by
        if 'Replaces' in row and row['Replaces']:
            for token in str(row['Replaces']).split(','):
                t = token.strip()
                if t:
                    p2 = Property.objects.filter(pa_code=t).first()
                    if p2:
                        prop.replaced_properties.add(p2)
        if 'Replaced by' in row and row['Replaced by']:
            for token in str(row['Replaced by']).split(','):
                t = token.strip()
                if t:
                    p2 = Property.objects.filter(pa_code=t).first()
                    if p2:
                        prop.replacing_properties.add(p2)

        # annotate revision
        try:
            reversion.set_user(user)
            reversion.set_comment(f"ISO16757 import property {property_id or '<no-id>'}")
        except Exception:
            pass

    return 'created' if created else 'updated'
