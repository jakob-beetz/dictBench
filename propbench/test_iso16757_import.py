#!/usr/bin/env python
"""
Test script for ISO 16757 property import functionality
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'propbench.settings')
django.setup()

from django.contrib.auth import get_user_model
from dictionaries.models import PropertyDictionary
from properties.models import Property, PropertyName, PropertyDefinition
import csv
import json

User = get_user_model()

def test_iso16757_import():
    """Test ISO 16757 import functionality with the heat pump CSV"""
    print("🧪 Testing ISO 16757 Property Import")
    print("=" * 50)
    
    # Create test user and dictionary if needed
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@test.com',
            'is_superuser': True,
            'is_staff': True
        }
    )
    if created:
        user.set_password('admin123')
        user.save()
        print(f"✓ Created admin user")
    
    dictionary, created = PropertyDictionary.objects.get_or_create(
        name='Heat Pumps ISO 16757',
        defaults={
            'description': 'ISO 16757 Heat Pump Properties Dictionary',
            'created_by': user,
            'updated_by': user
        }
    )
    if created:
        print(f"✓ Created dictionary: {dictionary.name}")
    
    # Test file path
    csv_file_path = Path(__file__).parent.parent / 'data' / '16757_examples' / 'EN_ISO16757_sheet22_HeatPumps-Mono-properties2.csv'
    
    if not csv_file_path.exists():
        print(f"❌ Test file not found: {csv_file_path}")
        return
    
    print(f"📁 Reading CSV file: {csv_file_path.name}")
    
    # Import the CSV
    imported_count = 0
    updated_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')  # ISO 16757 uses semicolon
            
            print(f"📊 CSV Headers: {len(reader.fieldnames)} columns")
            print(f"🔍 First few headers: {reader.fieldnames[:5]}")
            
            for row_num, row in enumerate(reader, 1):
                if row_num > 5:  # Limit to first 5 rows for testing
                    break
                    
                try:
                    # Get property ID
                    prop_id = row.get('Property ID', f'TEST_{row_num}')
                    prop_type = row.get('Property type', '1')
                    
                    # Skip header/empty rows
                    if not prop_id or prop_id in ['Property ID', '']:
                        continue
                    
                    print(f"\n📝 Processing Row {row_num}: {prop_id}")
                    
                    # Map basic fields
                    data_type_map = {'1': 'string', '2': 'real', '3': 'integer', '4': 'boolean'}
                    data_type = data_type_map.get(prop_type, 'string')
                    
                    unit = row.get('UnitNo', '')
                    status = row.get('Status', 'active')
                    
                    # Create property
                    property_obj, created = Property.objects.update_or_create(
                        dictionary=dictionary,
                        data_type=data_type,
                        unit_of_measurement=unit,
                        defaults={
                            'status': status,
                            'creators_language': row.get('Creators language', ''),
                            'country_of_origin': row.get('Country of origin', ''),
                            'classification_system': row.get('Classification system', ''),
                            'extended_attributes': json.dumps({
                                'property_id': prop_id,
                                'iso16757_type': prop_type,
                                'names_de': row.get('Names in language de-DE', ''),
                                'names_en': row.get('Names in language EN', ''),
                                'definitions_de': row.get('Definitions in language de-DE', ''),
                                'definitions_en': row.get('Definitions in language EN', ''),
                            }),
                            'metadata': json.dumps({
                                'import_source': 'ISO_16757_TEST',
                                'original_row': dict(row),
                                'row_number': row_num
                            }),
                            'created_by': user,
                            'updated_by': user
                        }
                    )
                    
                    # Create names
                    names_de = row.get('Names in language de-DE', '')
                    names_en = row.get('Names in language EN', '')
                    
                    if names_de:
                        PropertyName.objects.get_or_create(
                            property=property_obj,
                            name=names_de[:255],  # Truncate if too long
                            language='de'
                        )
                    
                    if names_en:
                        PropertyName.objects.get_or_create(
                            property=property_obj,
                            name=names_en[:255],
                            language='en'
                        )
                    
                    # Create definitions
                    defs_de = row.get('Definitions in language de-DE', '')
                    defs_en = row.get('Definitions in language EN', '')
                    
                    if defs_de:
                        PropertyDefinition.objects.get_or_create(
                            property=property_obj,
                            definition=defs_de,
                            language='de'
                        )
                    
                    if defs_en:
                        PropertyDefinition.objects.get_or_create(
                            property=property_obj,
                            definition=defs_en,
                            language='en'
                        )
                    
                    if created:
                        imported_count += 1
                        print(f"   ✓ Created: {data_type} property")
                    else:
                        updated_count += 1
                        print(f"   ↻ Updated existing property")
                    
                except Exception as e:
                    print(f"   ❌ Error processing row {row_num}: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return
    
    print(f"\n🎉 Import Summary:")
    print(f"   📊 Total processed: {imported_count + updated_count}")
    print(f"   ✅ Created: {imported_count}")
    print(f"   ↻ Updated: {updated_count}")
    
    # Show some results
    total_props = Property.objects.filter(dictionary=dictionary).count()
    total_names = PropertyName.objects.filter(property__dictionary=dictionary).count()
    total_defs = PropertyDefinition.objects.filter(property__dictionary=dictionary).count()
    
    print(f"\n📈 Database Status:")
    print(f"   🏷️ Properties: {total_props}")
    print(f"   📝 Names: {total_names}")
    print(f"   📖 Definitions: {total_defs}")
    
    # Show sample property
    sample = Property.objects.filter(dictionary=dictionary).first()
    if sample:
        print(f"\n🔍 Sample Property:")
        print(f"   ID: {sample.id}")
        print(f"   Type: {sample.data_type}")
        print(f"   Unit: {sample.unit_of_measurement}")
        print(f"   Status: {sample.status}")
        print(f"   Names: {[n.name for n in sample.names.all()]}")
        print(f"   Extended Attrs: {sample.extended_attributes[:100] if sample.extended_attributes else 'None'}...")

if __name__ == '__main__':
    test_iso16757_import()