from django.contrib import admin
from django.db import models, transaction
from django.contrib import messages
from django.urls import path
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
import json
import csv
import io
from .models import (
    Property, PropertyName, PropertyDefinition, PhysicalQuantity, PropertyRelationship
)
from dictionaries.models import PropertyDictionary
from .widgets import JSONEditorWidget


class PropertyNameInline(admin.TabularInline):
    model = PropertyName
    extra = 1
    fields = ('name', 'language')


class PropertyDefinitionInline(admin.TabularInline):
    model = PropertyDefinition
    extra = 1
    fields = ('definition', 'language')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """Admin interface for Property with comprehensive import/export functionality."""
    
    change_list_template = 'admin/properties/property/change_list.html'
    
    # apply JSONEditorWidget to all JSONField fields
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    list_display = (
        'get_first_name', 'data_type', 'status', 'dictionary', 
        'unit_of_measurement', 'created_by', 'created_at'
    )
    list_filter = (
        'data_type', 'status', 'dictionary', 'created_at', 'updated_at',
        'country_of_origin', 'classification_system'
    )
    search_fields = ('names__name', 'classification_reference', 'unit_of_measurement')
    ordering = ('-created_at',)
    inlines = [PropertyNameInline, PropertyDefinitionInline]
    
    fieldsets = (
        ('Core Information (PA001-003)', {
            'fields': ('dictionary', 'version_number', 'revision_number')
        }),
        ('Technical Specifications (PA004-010)', {
            'fields': ('data_type', 'unit_of_measurement', 'value_domain', 'physical_quantity')
        }),
        ('Classification (PA011-015)', {
            'fields': ('classification_system', 'classification_reference')
        }),
        ('Lifecycle & Authority (PA016-020)', {
            'fields': ('status', 'registration_authority', 'registration_date', 'deprecation_explanation')
        }),
        ('Geographic & Localization (PA021-025)', {
            'fields': ('country_of_origin', 'countries_of_use', 'creators_language')
        }),
        ('Extended Data', {
            'fields': ('extended_attributes', 'metadata'),
            'classes': ('collapse',),
            'description': 'JSON fields for storing ISO 16757 and PA code compliant data'
        }),
        ('System Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
    
    def get_first_name(self, obj):
        """Get first available property name for display."""
        first_name = obj.names.first()
        return first_name.name if first_name else f"Property {obj.guid}"
    get_first_name.short_description = "Name"
    
    def save_model(self, request, obj, form, change):
        """Set user tracking on save."""
        if not change:  # Creating new
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_urls(self):
        """Add custom import/export URLs."""
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv_view), 
                 name='properties_property_import_csv'),
            path('import-iso16757/', self.admin_site.admin_view(self.import_iso16757_view), 
                 name='properties_property_import_iso16757'),
            path('export-csv/', self.admin_site.admin_view(self.export_csv_view),
                 name='properties_property_export_csv'),
            path('grid-manager/', self.admin_site.admin_view(self.grid_manager_view),
                 name='properties_property_grid_manager'),
        ]
        return custom_urls + urls
    
    def grid_manager_view(self, request):
        """Advanced grid manager view."""
        from .grid_views import PropertyGridView
        view = PropertyGridView.as_view()
        return view(request)
    
    def import_csv_view(self, request):
        """Basic CSV import view with transaction management."""
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            dictionary_id = request.POST.get('dictionary_id')
            
            if not csv_file or not dictionary_id:
                messages.error(request, 'Please provide both CSV file and dictionary selection.')
                return redirect('admin:properties_property_import_csv')
            
            try:
                dictionary = PropertyDictionary.objects.get(id=dictionary_id)
                
                with transaction.atomic():
                    # Read and process CSV
                    decoded_file = csv_file.read().decode('utf-8')
                    io_string = io.StringIO(decoded_file)
                    
                    reader = csv.DictReader(io_string)
                    
                    created_count = 0
                    updated_count = 0
                    
                    for row in reader:
                        # Extract core fields
                        core_data = self._extract_core_fields(row)
                        core_data['dictionary'] = dictionary
                        
                        # Extract PA code and extended attributes
                        pa_code_data, iso16757_attrs, custom_attrs = self._extract_extended_attributes(row)
                        
                        # Create or update Property
                        property_obj, created = Property.objects.update_or_create(
                            dictionary=dictionary,
                            data_type=core_data.get('data_type', 'string'),
                            unit_of_measurement=core_data.get('unit_of_measurement', ''),
                            defaults={
                                **core_data,
                                'extended_attributes': json.dumps(iso16757_attrs) if iso16757_attrs else None,
                                'metadata': json.dumps({
                                    'pa_code_data': pa_code_data,
                                    'custom_attributes': custom_attrs
                                }),
                                'updated_by': request.user,
                            }
                        )
                        
                        # Set created_by only for new objects
                        if created:
                            property_obj.created_by = request.user
                            property_obj.save(update_fields=['created_by'])
                            created_count += 1
                            
                            # Create property name if available
                            name_value = row.get('name', row.get('Name', row.get('property_name', '')))
                            if name_value:
                                PropertyName.objects.create(
                                    property=property_obj,
                                    name=str(name_value).strip(),
                                    language='en'
                                )
                            
                            # Create property definition if available
                            def_value = row.get('definition', row.get('Definition', row.get('description', '')))
                            if def_value:
                                PropertyDefinition.objects.create(
                                    property=property_obj,
                                    definition=str(def_value).strip(),
                                    language='en'
                                )
                        else:
                            updated_count += 1
                    
                    messages.success(
                        request, 
                        f'Successfully imported {created_count} new properties and updated {updated_count} existing properties.'
                    )
                    
            except Exception as e:
                messages.error(request, f'Import failed: {str(e)}')
            
            return redirect('admin:properties_property_changelist')
        
        # GET request - show import form
        context = {
            'title': 'Import Properties from CSV',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': True,
            'dictionaries': PropertyDictionary.objects.all(),
        }
        return render(request, 'admin/properties/import_csv.html', context)
    
    def import_iso16757_view(self, request):
        """ISO 16757 specific import with PA code compliance."""
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            dictionary_id = request.POST.get('dictionary_id')
            
            # Enhanced debug logging
            print("=" * 50)
            print("DEBUG: ISO 16757 Import Form Submission")
            print(f"DEBUG: Request method: {request.method}")
            print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
            print(f"DEBUG: POST data values: {dict(request.POST)}")
            print(f"DEBUG: FILES data keys: {list(request.FILES.keys())}")
            print(f"DEBUG: FILES data: {dict(request.FILES)}")
            print(f"DEBUG: csv_file object: {repr(csv_file)}")
            print(f"DEBUG: csv_file name: {getattr(csv_file, 'name', 'N/A')}")
            print(f"DEBUG: csv_file size: {getattr(csv_file, 'size', 'N/A')}")
            print(f"DEBUG: dictionary_id raw: {repr(dictionary_id)}")
            print(f"DEBUG: dictionary_id stripped: {repr(dictionary_id.strip() if dictionary_id else None)}")
            print("=" * 50)
            
            # Check if we have any dictionaries at all
            available_dicts = PropertyDictionary.objects.all()
            print(f"DEBUG: Available dictionaries count: {available_dicts.count()}")
            for d in available_dicts:
                print(f"DEBUG: Dictionary {d.pk}: {d.name}")
            
            if not csv_file:
                print("DEBUG: CSV file validation failed")
                messages.error(request, 'No CSV file was uploaded. Please select a file.')
                return redirect('admin:properties_property_import_iso16757')
                
            if not dictionary_id or dictionary_id.strip() == '':
                print("DEBUG: Dictionary validation failed")
                print(f"DEBUG: dictionary_id type: {type(dictionary_id)}")
                print(f"DEBUG: dictionary_id repr: {repr(dictionary_id)}")
                print(f"DEBUG: dictionary_id bool: {bool(dictionary_id)}")
                print(f"DEBUG: Available dictionary PKs: {[d.pk for d in available_dicts]}")
                messages.error(request, f'No dictionary was selected. Please select a dictionary from the dropdown. Received: "{dictionary_id}"')
                return redirect('admin:properties_property_import_iso16757')
            
            print("DEBUG: Both validations passed, proceeding to process import...")
            return self._process_iso16757_import(request)
        
        # GET request - show import form
        dictionaries = PropertyDictionary.objects.all()
        print(f"DEBUG: GET request - Available dictionaries: {dictionaries.count()}")
        for d in dictionaries:
            print(f"DEBUG: Dictionary '{d.name}' - PK: {d.pk} (type: {type(d.pk)})")
        
        context = {
            'title': 'Import ISO 16757 Properties',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': True,
            'dictionaries': dictionaries,
        }
        return render(request, 'admin/properties/import_iso16757.html', context)
    
    def export_csv_view(self, request):
        """Export properties to CSV with ISO 16757 and PA code compliance."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="properties_iso16757_export.csv"'
        
        writer = csv.writer(response)
        
        # ISO 16757 compliant headers matching import format
        headers = [
            # Core identification (PA001-PA003)
            'Property ID', 'dictionary', 'version_number', 'revision_number',
            
            # Technical specifications (PA004-PA010)  
            'Property type', 'data_type', 'unit_of_measurement', 'UnitNo', 
            'value_domain', 'List of Possible Values', 'QuantityID', 'physical_quantity',
            
            # Classification (PA011-PA015)
            'classification_system', 'Classification system', 'classification_reference', 
            'Reference to standard or document',
            
            # Lifecycle & Authority (PA016-PA020)
            'Status', 'status', 'registration_authority', 'Reference to VDI 3805 record no',
            'registration_date', 'Date of creation', 'deprecation_explanation',
            
            # Geographic & Localization (PA021-PA025)
            'country_of_origin', 'Country of origin', 'countries_of_use', 'Country of use',
            'creators_language', 'Creators language',
            
            # Multilingual names and definitions
            'Names in language de-DE', 'Names in language EN',
            'Definitions in language de-DE', 'Definitions in language EN',
            'Descriptions in language de-DE', 'Descriptions in language EN',
            
            # Extended attributes
            'extended_attributes', 'metadata', 
            
            # System fields
            'created_at', 'created_by', 'updated_at', 'updated_by'
        ]
        writer.writerow(headers)
        
        for prop in Property.objects.select_related('dictionary', 'physical_quantity', 'created_by', 'updated_by').prefetch_related('names', 'definitions'):
            
            # Get multilingual names
            names_de = [n.name for n in prop.names.filter(language='de')]
            names_en = [n.name for n in prop.names.filter(language='en')]
            names_de_str = '; '.join(names_de) if names_de else ''
            names_en_str = '; '.join(names_en) if names_en else ''
            
            # Get multilingual definitions  
            defs_de = [d.definition for d in prop.definitions.filter(language='de')]
            defs_en = [d.definition for d in prop.definitions.filter(language='en')]
            defs_de_str = '; '.join(defs_de) if defs_de else ''
            defs_en_str = '; '.join(defs_en) if defs_en else ''
            
            # Generate Property ID from GUID or create one
            property_id = str(prop.guid) if hasattr(prop, 'guid') else f"PROP_{prop.pk}"
            
            # Map property type back to ISO 16757 format
            property_type_mapping = {
                'string': '1',
                'real': '2', 
                'integer': '3',
                'boolean': '4'
            }
            property_type = property_type_mapping.get(prop.data_type, '1')
            
            writer.writerow([
                # Core identification
                property_id,
                prop.dictionary.name,
                prop.version_number or '',
                prop.revision_number or '',
                
                # Technical specifications
                property_type,
                prop.data_type,
                prop.unit_of_measurement or '',
                prop.unit_of_measurement or '',  # Duplicate for UnitNo
                prop.value_domain or '',
                prop.value_domain or '',  # Duplicate for List of Possible Values
                prop.physical_quantity.name if prop.physical_quantity else '',
                prop.physical_quantity.name if prop.physical_quantity else '',
                
                # Classification
                prop.classification_system or '',
                prop.classification_system or '',  # Duplicate
                prop.classification_reference or '',
                prop.classification_reference or '',  # Duplicate
                
                # Lifecycle & Authority
                prop.status,
                prop.status,  # Duplicate
                prop.registration_authority or '',
                prop.registration_authority or '',  # Duplicate
                prop.registration_date.strftime('%Y-%m-%d') if prop.registration_date else '',
                prop.registration_date.strftime('%Y-%m-%d') if prop.registration_date else '',
                prop.deprecation_explanation or '',
                
                # Geographic & Localization
                prop.country_of_origin or '',
                prop.country_of_origin or '',  # Duplicate
                prop.countries_of_use or '',
                prop.countries_of_use or '',  # Duplicate
                prop.creators_language or '',
                prop.creators_language or '',  # Duplicate
                
                # Multilingual content
                names_de_str,
                names_en_str, 
                defs_de_str,
                defs_en_str,
                '',  # Descriptions de-DE (could be same as definitions)
                '',  # Descriptions en-EN
                
                # Extended attributes
                prop.extended_attributes or '',
                prop.metadata or '',
                
                # System fields
                prop.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                prop.created_by.username if prop.created_by else '',
                prop.updated_at.strftime('%Y-%m-%d %H:%M:%S') if prop.updated_at else '',
                prop.updated_by.username if prop.updated_by else ''
            ])
        
        return response
    
    def _extract_core_fields(self, row):
        """Extract core Property fields from CSV row with ISO 16757 and PA code mapping."""
        
        # Map ISO 16757 CSV headers to our model fields
        field_mappings = {
            # Note: 'Property ID' and 'PA001.1' are NOT mapped to model fields 
            # as the Property model doesn't have a property_id field
            # These will be stored in extended_attributes instead
            
            # Data type mapping - handle both German and English
            'Property type': 'data_type',
            'Data Type': 'data_type',
            
            # Unit mapping
            'UnitNo': 'unit_of_measurement',
            'Unit': 'unit_of_measurement',
            
            # Status mapping
            'Status': 'status',
            
            # Version and revision
            'Version number': 'version_number',
            'Revision number': 'revision_number',
            
            # Language and localization
            'Creators language': 'creators_language',
            'Country of use': 'countries_of_use',
            'Country of origin': 'country_of_origin',
            
            # Classification
            'Classification system': 'classification_system',
            'Reference to standard or document': 'classification_reference',
            
            # Dates
            'Date of creation': 'registration_date',
            'Date of activation': 'registration_date',
            
            # Authority
            'Reference to VDI 3805 record no': 'registration_authority',
        }
        
        # Data type mapping for ISO 16757 property types
        data_type_mapping = {
            '1': 'string',     # ISO type 1
            '2': 'real',       # ISO type 2  
            '3': 'integer',    # ISO type 3
            '4': 'boolean',    # ISO type 4
            'string': 'string',
            'float': 'real',
            'integer': 'integer', 
            'int': 'integer',
            'real': 'real',
            'boolean': 'boolean',
            'bool': 'boolean',
            'string enum': 'string',
        }
        
        # Status mapping
        status_mapping = {
            'active': 'active',
            'deprecated': 'deprecated',
            'draft': 'draft',
            'withdrawn': 'withdrawn',
            '': 'active',  # Default to active if empty
        }
        
        core_fields = {}
        
        # Extract and map fields
        for csv_field, model_field in field_mappings.items():
            if csv_field in row and row[csv_field]:
                value = str(row[csv_field]).strip()
                if value:
                    core_fields[model_field] = value
        
        # Handle data type specifically
        data_type_raw = (
            row.get('Property type', '') or 
            row.get('Data Type', '') or 
            row.get('data_type', '') or
            '1'  # Default to string type
        )
        data_type = data_type_mapping.get(str(data_type_raw).strip(), 'string')
        core_fields['data_type'] = data_type
        
        # Handle unit of measurement
        unit_raw = (
            row.get('UnitNo', '') or
            row.get('Unit', '') or
            row.get('unit_of_measurement', '') or
            ''
        )
        core_fields['unit_of_measurement'] = str(unit_raw).strip()
        
        # Handle status
        status_raw = row.get('Status', 'active')
        status = status_mapping.get(str(status_raw).strip().lower(), 'active')
        core_fields['status'] = status
        
        # Handle value domain from List of Possible Values
        value_domain = row.get('List of Possible Values', '')
        if value_domain:
            core_fields['value_domain'] = str(value_domain).strip()
        
        # Handle registration date
        date_fields = ['Date of creation', 'Date of activation', 'registration_date']
        for date_field in date_fields:
            if date_field in row and row[date_field]:
                try:
                    from datetime import datetime
                    date_str = str(row[date_field]).strip()
                    if date_str and date_str != '':
                        # Try different date formats
                        for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y']:
                            try:
                                core_fields['registration_date'] = datetime.strptime(date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                        break
                except Exception:
                    pass  # Skip invalid dates
        
        # Handle physical quantity
        quantity_id = row.get('QuantityID', '')
        if quantity_id:
            try:
                # Try to find existing physical quantity or create a basic one
                from .models import PhysicalQuantity
                pq, created = PhysicalQuantity.objects.get_or_create(
                    name=str(quantity_id).strip(),
                    defaults={'description': f'Physical quantity from ISO 16757: {quantity_id}'}
                )
                core_fields['physical_quantity'] = pq
            except Exception:
                pass  # Skip if physical quantity creation fails
        
        return core_fields
    
    def _extract_extended_attributes(self, row):
        """Extract ISO 16757, PA code data, and custom attributes from CSV row."""
        
        # Core PA fields that go into the model directly
        core_model_fields = {
            # Removed 'property_id' as it's not a valid model field
            'data_type', 'unit_of_measurement', 'status',
            'version_number', 'revision_number', 'creators_language', 
            'countries_of_use', 'country_of_origin', 'classification_system',
            'classification_reference', 'registration_date', 'registration_authority',
            'value_domain', 'physical_quantity', 'deprecation_explanation'
        }
        
        # ISO 16757 specific fields that should go into extended_attributes
        iso16757_fields = {
            'Part', 'Property ID', 'IsSpecialisedOf', 'Property type',
            'Names in language de-DE', 'Definitions in language de-DE', 
            'Descriptions in language de-DE', 'Examples in language de-DE',
            'Names in language EN', 'Definitions in language EN', 
            'Descriptions in language EN', 'Examples in language EN',
            'Symbols of the property in a given property group', 'Visual representation',
            'Method of measurement', 'List of Possible Values', 
            'abstract_property with superset of values', 'Class assignment',
            'Parameters of the dependent property', 'Type of enumeration',
            'Identifier ETIM', 'ETIM Mapping Quality', 'Definition ETIM',
            'Identifier IFC 2_3', 'IFC 2_3 Mapping Quality', 'Definition IFC 2_3',
            'Identifier IFC 4x', 'IFC 4x Mapping Quality', 'Definition IFC 4x',
            'Identifier CIBSE', 'CISBE Mapping Quality', 'Definition CIBSE',
            'Identifier prodBIM', 'prodBIM Mapping Quality', 'Definition prodBIM',
            'Identifier ECLASS', 'ECLASS Mapping Quality', 'Definition ECLASS',
            'Identifier UniversalType', 'UniversalType Mapping Quality', 'Definition UniversalType'
        }
        
        # PA code fields for reference
        pa_code_fields = {
            'PA001.1', 'PA002', 'PA003', 'PA004', 'PA005', 'PA006', 'PA007', 
            'PA008', 'PA009', 'PA010', 'PA011', 'PA012', 'PA013', 'PA014',
            'PA015', 'PA016', 'PA017', 'PA018', 'PA019', 'PA020', 'PA021',
            'PA022', 'PA023', 'PA024', 'PA025', 'PA026', 'PA027', 'PA028',
            'PA029', 'PA030', 'PA031', 'PA032', 'PA033', 'PA034', 'PA035',
            'PA036', 'PA037', 'PA038', 'PA039', 'PA040', 'PA041', 'PA042',
            'PA043', 'PA044', 'PA045', 'PA046', 'PA047', 'PA048', 'PA049'
        }
        
        pa_code_data = {}
        iso16757_attrs = {}
        custom_attrs = {}
        
        for key, value in row.items():
            if not value or str(value).strip() == '':
                continue
                
            clean_value = str(value).strip()
            
            # Skip fields that are mapped to model fields directly
            if key.lower().replace(' ', '_').replace('-', '_') in core_model_fields:
                continue
                
            # ISO 16757 specific fields
            if key in iso16757_fields:
                iso16757_attrs[key] = clean_value
            
            # PA code fields
            elif key in pa_code_fields or key.startswith('PA') or key.startswith('P00'):
                pa_code_data[key] = clean_value
                
            # Multi-language names and definitions
            elif 'names in language' in key.lower() or 'definitions in language' in key.lower():
                iso16757_attrs[key] = clean_value
                
            # Classification and mapping fields
            elif any(pattern in key.lower() for pattern in ['etim', 'ifc', 'cibse', 'prodbim', 'eclass', 'universal']):
                iso16757_attrs[key] = clean_value
                
            # Identifier and reference fields
            elif any(pattern in key.lower() for pattern in ['identifier', 'id', 'guid', 'reference']):
                custom_attrs[f'identifier_{key}'] = clean_value
                
            # Technical specification fields
            elif any(pattern in key.lower() for pattern in ['quantity', 'method', 'measurement', 'visual']):
                custom_attrs[f'technical_{key}'] = clean_value
                
            # Date fields not in core model
            elif any(pattern in key.lower() for pattern in ['date of', 'created', 'updated', 'modified']):
                custom_attrs[f'date_{key}'] = clean_value
                
            # All other custom fields
            else:
                custom_attrs[key] = clean_value
        
        return pa_code_data, iso16757_attrs, custom_attrs
    
    def _process_iso16757_import(self, request):
        """Process ISO 16757 specific import with PA code compliance."""
        csv_file = request.FILES.get('csv_file')
        dictionary_id = request.POST.get('dictionary_id')
        
        if not csv_file or not dictionary_id:
            messages.error(request, 'Please provide both CSV file and dictionary selection.')
            return redirect('admin:properties_property_import_iso16757')
        
        try:
            dictionary = PropertyDictionary.objects.get(pk=dictionary_id)
            
            with transaction.atomic():
                # Handle file reading more robustly for ISO 16757 format
                try:
                    if hasattr(csv_file, 'read'):
                        file_content = csv_file.read()
                        if isinstance(file_content, bytes):
                            decoded_file = file_content.decode('utf-8-sig')  # Handle BOM
                        else:
                            decoded_file = file_content
                    else:
                        decoded_file = str(csv_file)
                        
                    io_string = io.StringIO(decoded_file)
                    
                    # ISO 16757 typically uses semicolon as delimiter
                    # Try to detect delimiter automatically
                    sample = decoded_file[:1024]
                    delimiter = ';' if sample.count(';') > sample.count(',') else ','
                    
                    print(f"DEBUG: Using delimiter: '{delimiter}'")
                    print(f"DEBUG: First 200 chars: {decoded_file[:200]}")
                    
                    io_string.seek(0)  # Reset to beginning
                    reader = csv.DictReader(io_string, delimiter=delimiter)
                    
                    print(f"DEBUG: CSV Headers: {reader.fieldnames}")
                    
                except Exception as e:
                    messages.error(request, f'Error reading CSV file: {str(e)}')
                    return redirect('admin:properties_property_import_iso16757')
                
                import_stats = {
                    'created': 0,
                    'updated': 0,
                    'skipped': 0,
                    'errors': []
                }
                
                # Process each row individually with savepoints to avoid transaction rollback
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        # Use savepoint for each row to isolate errors
                        with transaction.atomic():
                            # Skip completely empty rows
                            if not any(value.strip() for value in row.values() if value):
                                continue
                            
                            # Add debug info for the first few rows
                            if row_num <= 5:
                                print(f"DEBUG: Processing row {row_num}")
                                print(f"DEBUG: Row data: {dict(row)}")
                                
                            result = self._process_iso16757_row(row, dictionary, request.user)
                            import_stats[result] += 1
                            
                            # Log progress for large files
                            if row_num % 100 == 0:
                                print(f"DEBUG: Processed {row_num} rows...")
                        
                    except Exception as e:
                        import_stats['errors'].append(f'Row {row_num}: {str(e)}')
                        import_stats['skipped'] += 1
                        print(f"DEBUG: Error in row {row_num}: {e}")
                        # Continue processing other rows even if this one failed
                
                # Report results
                if import_stats['errors']:
                    messages.warning(
                        request,
                        f"Import completed with {len(import_stats['errors'])} errors. "
                        f"Created: {import_stats['created']}, Updated: {import_stats['updated']}, "
                        f"Skipped: {import_stats['skipped']}"
                    )
                    # Log detailed errors (first 5)
                    for error in import_stats['errors'][:5]:
                        messages.error(request, error)
                        
                    if len(import_stats['errors']) > 5:
                        messages.warning(request, f"... and {len(import_stats['errors']) - 5} more errors.")
                else:
                    messages.success(
                        request,
                        f"ISO 16757 import successful! Created: {import_stats['created']}, "
                        f"Updated: {import_stats['updated']}"
                    )
                
        except PropertyDictionary.DoesNotExist:
            messages.error(request, f'Dictionary with ID {dictionary_id} not found.')
        except Exception as e:
            messages.error(request, f'Import failed: {str(e)}')
            import traceback
            print(f"DEBUG: Exception traceback: {traceback.format_exc()}")
        
        return redirect('admin:properties_property_changelist')
    
    def _process_iso16757_row(self, row, dictionary, user):
        """Process a single row for ISO 16757 import with comprehensive field mapping."""
        
        # Import json at the beginning of the method
        import json
        import time
        
        # Validate required fields for ISO 16757
        property_id = row.get('Property ID', row.get('PA001.1', ''))
        property_type = row.get('Property type', row.get('Data Type', '1'))
        
        if not property_id:
            # Generate a fallback ID if none provided
            property_id = f"PROP_{hash(str(row))}"[:16]
        
        # Extract core model fields (excluding property_id which doesn't exist in model)
        core_data = self._extract_core_fields(row)
        core_data['dictionary'] = dictionary
        
        # Ensure required fields have defaults
        if 'data_type' not in core_data:
            core_data['data_type'] = 'string'
        if 'unit_of_measurement' not in core_data:
            core_data['unit_of_measurement'] = ''
        if 'status' not in core_data:
            core_data['status'] = 'active'
        if 'version_number' not in core_data:
            core_data['version_number'] = '1'
        
        # Enhanced attribute extraction
        pa_code_data, iso16757_attrs, custom_attrs = self._extract_extended_attributes(row)
        
        # Add the property_id to extended_attributes since it's not a model field
        iso16757_attrs['original_property_id'] = property_id
        
        # Add import metadata
        import_metadata = {
            'import_source': 'ISO_16757',
            'import_date': str(timezone.now()),
            'import_user': user.username,
            'original_property_id': property_id,
            'iso16757_property_type': property_type,
        }
        
        # Combine metadata with enhanced structure
        metadata = {
            'import_metadata': import_metadata,
            'pa_code_data': pa_code_data,
            'custom_attributes': custom_attrs,
            'iso16757_mappings': {
                'etim': {k: v for k, v in iso16757_attrs.items() if 'etim' in k.lower()},
                'ifc': {k: v for k, v in iso16757_attrs.items() if 'ifc' in k.lower()},
                'cibse': {k: v for k, v in iso16757_attrs.items() if 'cibse' in k.lower()},
                'prodbim': {k: v for k, v in iso16757_attrs.items() if 'prodbim' in k.lower()},
                'eclass': {k: v for k, v in iso16757_attrs.items() if 'eclass' in k.lower()},
                'universal': {k: v for k, v in iso16757_attrs.items() if 'universal' in k.lower()},
            }
        }
        
        # Create unique lookup to avoid duplicates - use more specific fields
        lookup_fields = {
            'dictionary': dictionary,
            'data_type': core_data.get('data_type', 'string'),
            'unit_of_measurement': core_data.get('unit_of_measurement', ''),
        }
        
        # Add additional unique identifiers to avoid duplicates
        if core_data.get('version_number'):
            lookup_fields['version_number'] = core_data.get('version_number')
        
        # Try to find existing property - if multiple found, make it unique
        existing_properties = Property.objects.filter(**lookup_fields)
        
        if existing_properties.exists():
            # Check if any existing property has the same original_property_id
            property_obj = None
            for prop in existing_properties[:5]:  # Limit to first 5 to avoid performance issues
                if prop.extended_attributes:
                    try:
                        attrs = json.loads(prop.extended_attributes)
                        if attrs.get('original_property_id') == property_id:
                            property_obj = prop
                            created = False
                            break
                    except Exception:
                        continue
            
            if not property_obj:
                # No exact match by property_id, create a new unique one
                unique_suffix = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
                property_obj = Property.objects.create(
                    dictionary=dictionary,
                    data_type=core_data.get('data_type', 'string'),
                    unit_of_measurement=core_data.get('unit_of_measurement', ''),
                    version_number=f"{core_data.get('version_number', '1')}-{unique_suffix}",
                    status=core_data.get('status', 'active'),
                    extended_attributes=json.dumps(iso16757_attrs) if iso16757_attrs else None,
                    metadata=json.dumps(metadata),
                    created_by=user,
                    updated_by=user,
                )
                created = True
            else:
                # Update existing property
                property_obj.status = core_data.get('status', property_obj.status)
                property_obj.extended_attributes = json.dumps(iso16757_attrs) if iso16757_attrs else None
                property_obj.metadata = json.dumps(metadata)
                property_obj.updated_by = user
                property_obj.save()
                created = False
                
        else:
            # No existing property, create new one
            property_obj = Property.objects.create(
                dictionary=dictionary,
                data_type=core_data.get('data_type', 'string'),
                unit_of_measurement=core_data.get('unit_of_measurement', ''),
                status=core_data.get('status', 'active'),
                version_number=core_data.get('version_number', '1'),
                extended_attributes=json.dumps(iso16757_attrs) if iso16757_attrs else None,
                metadata=json.dumps(metadata),
                created_by=user,
                updated_by=user,
            )
            created = True
        
        # Create property names and definitions for new properties only
        if created:
            # Create property names from ISO 16757 multilingual fields
            self._create_property_names_iso16757(property_obj, row)
            # Create property definitions from ISO 16757 multilingual fields
            self._create_property_definitions_iso16757(property_obj, row)
        
        return 'created' if created else 'updated'
    
    def _create_property_names_iso16757(self, property_obj, row):
        """Create PropertyName instances from ISO 16757 multilingual data."""
        # Mapping of CSV columns to language codes
        name_mappings = {
            'Names in language de-DE': 'de',
            'Names in language EN': 'en',
            'name': 'en',
            'Name': 'en',
            'property_name': 'en',
            'PropertyName': 'en'
        }
        
        created_names = set()  # Track created names to avoid duplicates
        
        for field, language in name_mappings.items():
            if field in row and row[field]:
                name_value = str(row[field]).strip()
                if name_value and name_value not in created_names:
                    PropertyName.objects.get_or_create(
                        property=property_obj,
                        name=name_value,
                        language=language
                    )
                    created_names.add(name_value)
    
    def _create_property_definitions_iso16757(self, property_obj, row):
        """Create PropertyDefinition instances from ISO 16757 multilingual data."""
        # Mapping of CSV columns to language codes
        definition_mappings = {
            'Definitions in language de-DE': 'de',
            'Definitions in language EN': 'en',
            'Descriptions in language de-DE': 'de',
            'Descriptions in language EN': 'en',
            'Examples in language de-DE': 'de',
            'Examples in language EN': 'en',
            'definition': 'en',
            'Definition': 'en',
            'description': 'en',
            'Description': 'en'
        }
        
        created_definitions = set()  # Track created definitions to avoid duplicates
        
        for field, language in definition_mappings.items():
            if field in row and row[field]:
                def_value = str(row[field]).strip()
                if def_value and def_value not in created_definitions:
                    PropertyDefinition.objects.get_or_create(
                        property=property_obj,
                        definition=def_value,
                        language=language
                    )
                    created_definitions.add(def_value)
    
    def grid_data_view(self, request):
        """Return JSON list of properties for the grid."""
        from django.http import JsonResponse
        from django.core.serializers.json import DjangoJSONEncoder

        qs = Property.objects.select_related('dictionary', 'physical_quantity', 'created_by', 'updated_by').prefetch_related('names')
        data = []
        for p in qs:
            names = []
            try:
                for n in p.names.all():
                    names.append({"language": getattr(n, 'language', 'en'), "name": getattr(n, 'name', '')})
            except Exception:
                names = []

            data.append({
                'id': p.pk,
                'guid': getattr(p, 'guid', None),
                'names': names,
                'data_type': getattr(p, 'data_type', None),
                'unit_of_measurement': getattr(p, 'unit_of_measurement', None),
                'status': getattr(p, 'status', None),
                'dictionary_name': p.dictionary.name if getattr(p, 'dictionary', None) else None,
                'physical_quantity_name': p.physical_quantity.name if getattr(p, 'physical_quantity', None) else None,
                'version_number': getattr(p, 'version_number', None),
                'updated_at': p.updated_at.isoformat() if getattr(p, 'updated_at', None) else None,
                'extended_attributes': p.extended_attributes if getattr(p, 'extended_attributes', None) else None,
            })

        return JsonResponse({'properties': data}, encoder=DjangoJSONEncoder, safe=True)

    def dictionaries_view(self, request):
        """Return JSON list of dictionaries for dropdowns."""
        from django.http import JsonResponse
        dicts = PropertyDictionary.objects.all().order_by('name')
        result = []
        for d in dicts:
            result.append({
                'pk': d.pk,
                'name': d.name,
                'guid': getattr(d, 'guid', None),
                'is_default': getattr(d, 'is_default', False),
            })
        return JsonResponse(result, safe=False)


# Register the admin classes
# admin.site.register(Property, PropertyAdmin)
admin.site.register(PropertyName)
admin.site.register(PropertyDefinition)
admin.site.register(PhysicalQuantity)
