from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
import pandas as pd
import json
import csv
from pathlib import Path

from groups.models import PropertyGroup
from properties.models import Property, PropertyName, PropertyDefinition
from dictionaries.models import PropertyDictionary


class Command(BaseCommand):
    help = 'Analyze and import ISO 16757 data from the provided CSV files'
    
    def add_arguments(self, parser):
        parser.add_argument('--analyze', action='store_true', help='Only analyze the data, do not import')
        parser.add_argument('--import', action='store_true', help='Import the data after analysis')
        parser.add_argument('--dictionary', type=str, help='Dictionary name to import into')
        parser.add_argument('--user', type=str, help='Username for import tracking')
        parser.add_argument('--data-dir', type=str, default='c:/src/propBench/data/16757_examples',
                          help='Directory containing CSV files')
    
    def handle(self, *args, **options):
        self.data_dir = Path(options['data_dir'])
        
        if not self.data_dir.exists():
            self.stdout.write(
                self.style.ERROR(f'Data directory not found: {self.data_dir}')
            )
            return
        
        # Always analyze first
        self.stdout.write(self.style.SUCCESS('=== ANALYZING CSV DATA ==='))
        analysis = self.analyze_csv_files()
        
        if options['analyze']:
            self.display_analysis(analysis)
            return
        
        if options['import']:
            if not options['dictionary'] or not options['user']:
                self.stdout.write(
                    self.style.ERROR('--dictionary and --user are required for import')
                )
                return
            
            self.stdout.write(self.style.SUCCESS('=== IMPORTING DATA ==='))
            self.import_data(analysis, options['dictionary'], options['user'])
    
    def analyze_csv_files(self):
        """Analyze the structure of CSV files."""
        files = {
            'properties': 'EN_ISO16757_sheet22_HeatPumps-Mono-properties.csv',
            'values': 'EN_ISO16757_sheet22_HeatPumps-Mono-values.csv',
            'classes': 'EN_ISO16757_sheet22_HeatPumps-Mono-class.csv'
        }
        
        analysis = {}
        
        for file_type, filename in files.items():
            filepath = self.data_dir / filename
            if not filepath.exists():
                self.stdout.write(
                    self.style.WARNING(f'File not found: {filename}')
                )
                continue
            
            try:
                # Read with pandas for better analysis
                df = pd.read_csv(filepath, encoding='utf-8', dtype=str, na_filter=False)
                
                analysis[file_type] = {
                    'filename': filename,
                    'shape': df.shape,
                    'columns': df.columns.tolist(),
                    'data': df,
                    'pa_mappings': self.identify_pa_mappings(df, file_type),
                    'iso16757_fields': self.identify_iso16757_fields(df),
                    'custom_identifiers': self.identify_custom_identifiers(df)
                }
                
                self.stdout.write(f'✓ Analyzed {filename}: {df.shape[0]} rows, {df.shape[1]} columns')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error reading {filename}: {e}')
                )
                analysis[file_type] = {'error': str(e)}
        
        return analysis
    
    def identify_pa_mappings(self, df, file_type):
        """Identify ISO 23386 PA code mappings from column names."""
        pa_mappings = {}
        
        # Known PA code mappings
        pa_codes = {
            # Core identification (PA001-PA003)
            'dictionary': 'PA001', 'version': 'PA002', 'revision': 'PA003',
            
            # Technical specification (PA004-PA010)  
            'datatype': 'PA004', 'data_type': 'PA004',
            'unit': 'PA005', 'unit_of_measurement': 'PA005',
            'domain': 'PA007', 'value_domain': 'PA007',
            'physical_quantity': 'PA008',
            
            # Classification (PA011-PA015)
            'classification': 'PA011', 'classification_system': 'PA011',
            'reference': 'PA012', 'classification_reference': 'PA012',
            
            # Status & Authority (PA016-PA020)
            'status': 'PA016', 'authority': 'PA017',
            
            # Geographic & Localization (PA021-PA025)
            'country': 'PA021', 'language': 'PA023'
        }
        
        for column in df.columns:
            column_lower = column.lower().replace('_', '').replace(' ', '')
            
            for field, pa_code in pa_codes.items():
                if field in column_lower:
                    pa_mappings[column] = pa_code
                    break
        
        return pa_mappings
    
    def identify_iso16757_fields(self, df):
        """Identify ISO 16757 specific fields."""
        iso_fields = []
        
        iso_patterns = [
            'iso', '16757', 'class', 'type', 'category',
            'standard', 'reference', 'definition'
        ]
        
        for column in df.columns:
            if any(pattern in column.lower() for pattern in iso_patterns):
                iso_fields.append(column)
        
        return iso_fields
    
    def identify_custom_identifiers(self, df):
        """Identify custom identifier fields."""
        identifier_fields = []
        
        id_patterns = ['id', 'code', 'ref', 'guid', 'key', 'number']
        
        for column in df.columns:
            if any(pattern in column.lower() for pattern in id_patterns):
                identifier_fields.append(column)
        
        return identifier_fields
    
    def display_analysis(self, analysis):
        """Display detailed analysis results."""
        for file_type, data in analysis.items():
            if 'error' in data:
                continue
                
            self.stdout.write(f'\n=== {file_type.upper()} FILE ANALYSIS ===')
            self.stdout.write(f'File: {data["filename"]}')
            self.stdout.write(f'Shape: {data["shape"]}')
            
            self.stdout.write('\nColumns:')
            for i, col in enumerate(data['columns'], 1):
                self.stdout.write(f'  {i:2d}. {col}')
            
            self.stdout.write('\nPA Code Mappings:')
            for column, pa_code in data['pa_mappings'].items():
                self.stdout.write(f'  {column} → {pa_code}')
            
            self.stdout.write('\nISO 16757 Fields:')
            for field in data['iso16757_fields']:
                self.stdout.write(f'  • {field}')
            
            self.stdout.write('\nCustom Identifiers:')
            for field in data['custom_identifiers']:
                self.stdout.write(f'  • {field}')
            
            # Show sample data
            self.stdout.write('\nSample Data (first 3 rows):')
            df = data['data']
            for i in range(min(3, len(df))):
                self.stdout.write(f'\nRow {i+1}:')
                row_data = df.iloc[i].to_dict()
                for key, value in row_data.items():
                    if value:  # Only show non-empty values
                        self.stdout.write(f'  {key}: {value[:100]}{"..." if len(str(value)) > 100 else ""}')
    
    def import_data(self, analysis, dictionary_name, username):
        """Import the analyzed data."""
        # Get or create dictionary
        dictionary, created = PropertyDictionary.objects.get_or_create(
            name=dictionary_name,
            defaults={
                'description': f'Imported from ISO 16757 data on {timezone.now()}',
                'is_default': False
            }
        )
        
        if created:
            self.stdout.write(f'✓ Created dictionary: {dictionary_name}')
        else:
            self.stdout.write(f'✓ Using existing dictionary: {dictionary_name}')
        
        # Get user
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User not found: {username}')
            )
            return
        
        # Import each file type
        with transaction.atomic():
            # Create reversion comment for rollback capability
            try:
                import reversion
                with reversion.create_revision():
                    reversion.set_user(user)
                    reversion.set_comment(f"ISO 16757 import from {dictionary_name}")
                    
                    if 'classes' in analysis and 'error' not in analysis['classes']:
                        self.import_groups(analysis['classes'], dictionary, user)
                    
                    if 'properties' in analysis and 'error' not in analysis['properties']:
                        self.import_properties(analysis['properties'], dictionary, user)
                    
                    # Values are typically linked to properties via separate relationships
                    if 'values' in analysis and 'error' not in analysis['values']:
                        self.stdout.write('ℹ Values data available but not imported (requires property relationships)')
                        
            except ImportError:
                # Reversion not available, use regular transaction
                self.stdout.write(self.style.WARNING('django-reversion not available - using basic transactions'))
                
                if 'classes' in analysis and 'error' not in analysis['classes']:
                    self.import_groups(analysis['classes'], dictionary, user)
                
                if 'properties' in analysis and 'error' not in analysis['properties']:
                    self.import_properties(analysis['properties'], dictionary, user)
    
    def import_groups(self, class_analysis, dictionary, user):
        """Import property groups from class data."""
        df = class_analysis['data']
        pa_mappings = class_analysis['pa_mappings']
        
        self.stdout.write(f'Importing {len(df)} property groups...')
        
        created_count = 0
        updated_count = 0
        
        # Helper: robustly parse a cell value into native Python types
        def _parse_cell_value(raw):
            """Attempt to parse a CSV cell into a Python object.
            Handles values that are already dict/list, plain strings, or nested JSON-encoded strings
            (e.g. '"{\"key\": \"value\"}"'). Returns the native type or the stripped string.
            """
            if raw is None:
                return None
            if isinstance(raw, (dict, list)):
                return raw
            s = str(raw).strip()
            # strip surrounding quotes if present
            if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
                s = s[1:-1].strip()

            # try to JSON-decode repeatedly to unwrap nested encodings
            try:
                parsed = json.loads(s)
                # unwrap repeatedly if result is a JSON string
                unwrap_count = 0
                while isinstance(parsed, str) and unwrap_count < 5:
                    candidate = parsed.strip()
                    if (candidate.startswith('{') or candidate.startswith('[') or candidate.startswith('"') or candidate.startswith("'")):
                        try:
                            parsed = json.loads(parsed)
                        except Exception:
                            break
                    else:
                        break
                    unwrap_count += 1
                return parsed
            except Exception:
                return s

        for index, row in df.iterrows():
            try:
                # Extract core data
                name = row.get('name', row.get('Name', f'Group_{index}'))
                if not name or name.strip() == '':
                    continue
                
                description = row.get('description', row.get('Description', ''))
                group_type = row.get('type', row.get('Type', 'collection')).lower()
                
                # Map to valid choices
                type_mapping = {
                    'class': 'class',
                    'domain': 'domain', 
                    'functional': 'functional',
                    'collection': 'collection',
                    'template': 'template'
                }
                group_type = type_mapping.get(group_type, 'collection')
                
                # Extract extended attributes
                iso16757_attrs = {}
                custom_attrs = {}
                identifiers = {}

                for column, value in row.items():
                    # normalize empty cells
                    if value is None or str(value).strip() == '':
                        continue

                    # skip core fields
                    if column in ['name', 'Name', 'description', 'Description', 'type', 'Type']:
                        continue  # Skip core fields

                    parsed_value = _parse_cell_value(value)

                    if column in class_analysis['iso16757_fields']:
                        iso16757_attrs[column] = parsed_value
                    elif column in class_analysis['custom_identifiers']:
                        identifiers[f'original_{column}'] = parsed_value
                    else:
                        custom_attrs[column] = parsed_value

                # Add import metadata
                import_metadata = {
                    'import_source': 'ISO_16757_classes',
                    'import_date': str(timezone.now()),
                    'import_user': user.username,
                    'original_row_index': index,
                    'pa_mappings': pa_mappings,
                    'identifiers': identifiers
                }

                # Combine metadata
                metadata = {
                    'import_metadata': import_metadata,
                    'custom_attributes': custom_attrs,
                    'identifiers': identifiers
                }

                # Create or update group
                group, created = PropertyGroup.objects.update_or_create(
                    name=name.strip(),
                    dictionary=dictionary,
                    defaults={
                        'description': description.strip() if description else '',
                        'type': group_type,
                        # store native types (dict/None) not JSON strings
                        'extended_attributes': iso16757_attrs or None,
                        'metadata': metadata or None,
                        'updated_by': user,
                    }
                )
                
                if created:
                    group.created_by = user
                    group.save(update_fields=['created_by'])
                    created_count += 1
                else:
                    updated_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error importing group at row {index}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Groups: {created_count} created, {updated_count} updated')
        )
    
    def import_properties(self, prop_analysis, dictionary, user):
        """Import properties from properties data."""
        df = prop_analysis['data']
        pa_mappings = prop_analysis['pa_mappings']
        
        self.stdout.write(f'Importing {len(df)} properties...')
        
        created_count = 0
        updated_count = 0
        
        # Helper: robustly parse a cell value into native Python types
        def _parse_cell_value(raw):
            """Attempt to parse a CSV cell into a Python object.
            Handles values that are already dict/list, plain strings, or nested JSON-encoded strings
            (e.g. '"{\"key\": \"value\"}"'). Returns the native type or the stripped string.
            """
            if raw is None:
                return None
            if isinstance(raw, (dict, list)):
                return raw
            s = str(raw).strip()
            # strip surrounding quotes if present
            if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
                s = s[1:-1].strip()

            # try to JSON-decode repeatedly to unwrap nested encodings
            try:
                parsed = json.loads(s)
                # unwrap repeatedly if result is a JSON string
                unwrap_count = 0
                while isinstance(parsed, str) and unwrap_count < 5:
                    candidate = parsed.strip()
                    if (candidate.startswith('{') or candidate.startswith('[') or candidate.startswith('"') or candidate.startswith("'")):
                        try:
                            parsed = json.loads(parsed)
                        except Exception:
                            break
                    else:
                        break
                    unwrap_count += 1
                return parsed
            except Exception:
                return s

        for index, row in df.iterrows():
            try:
                # Extract core PA code fields
                data_type = row.get('DataType', row.get('datatype', 'String'))
                unit = row.get('Unit', row.get('unit', ''))
                
                # Map data types to model choices
                data_type_mapping = {
                    'string': 'string',
                    'text': 'string', 
                    'integer': 'integer',
                    'real': 'real',
                    'boolean': 'boolean',
                    'complex': 'complex'
                }
                data_type = data_type_mapping.get(data_type.lower(), 'string')
                
                # Extract extended attributes
                iso16757_attrs = {}
                custom_attrs = {}
                identifiers = {}
                pa_code_data = {}

                for column, value in row.items():
                    # normalize empty cells
                    if value is None or str(value).strip() == '':
                        continue

                    # Skip if core field
                    if column.lower() in ['datatype', 'unit']:
                        continue

                    parsed_value = _parse_cell_value(value)

                    if column in prop_analysis['iso16757_fields']:
                        iso16757_attrs[column] = parsed_value
                    elif column in prop_analysis['custom_identifiers']:
                        identifiers[f'original_{column}'] = parsed_value
                    elif column in pa_mappings:
                        pa_code_data[pa_mappings[column]] = parsed_value
                    else:
                        custom_attrs[column] = parsed_value

                # Create unique identifier for property
                property_key = f"{data_type}_{unit}_{index}"

                # Add import metadata
                import_metadata = {
                    'import_source': 'ISO_16757_properties',
                    'import_date': str(timezone.now()),
                    'import_user': user.username,
                    'original_row_index': index,
                    'pa_mappings': pa_mappings,
                    'pa_code_data': pa_code_data
                }

                # Combine metadata
                metadata = {
                    'import_metadata': import_metadata,
                    'custom_attributes': custom_attrs,
                    'identifiers': identifiers,
                    'pa_code_data': pa_code_data
                }

                # Create or update property
                property_obj, created = Property.objects.update_or_create(
                    dictionary=dictionary,
                    data_type=data_type,
                    unit_of_measurement=unit,
                    defaults={
                        'status': 'active',
                        # store native dicts/lists instead of JSON strings
                        'extended_attributes': iso16757_attrs or None,
                        'metadata': metadata or None,
                        'updated_by': user,
                    }
                )
                
                if created:
                    property_obj.created_by = user
                    property_obj.save(update_fields=['created_by'])
                    created_count += 1
                    
                    # Create property name if we have one
                    name_field = None
                    for col in ['Name', 'name', 'PropertyName', 'Label']:
                        if col in row and row[col]:
                            name_field = row[col]
                            break
                    
                    if name_field:
                        PropertyName.objects.create(
                            property=property_obj,
                            name=str(name_field).strip(),
                            language='en'
                        )
                    
                    # Create property definition if we have one
                    def_field = None
                    for col in ['Definition', 'definition', 'Description', 'description']:
                        if col in row and row[col]:
                            def_field = row[col]
                            break
                    
                    if def_field:
                        PropertyDefinition.objects.create(
                            property=property_obj,
                            definition=str(def_field).strip(),
                            language='en'
                        )
                else:
                    updated_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error importing property at row {index}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Properties: {created_count} created, {updated_count} updated')
        )