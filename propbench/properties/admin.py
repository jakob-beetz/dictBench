from django.contrib import admin
from django.db import transaction
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


class PropertyNameInline(admin.TabularInline):
    model = PropertyName
    extra = 1
    fields = ('name', 'language')


class PropertyDefinitionInline(admin.TabularInline):
    model = PropertyDefinition
    extra = 1
    fields = ('definition', 'language')


class PropertyAdmin(admin.ModelAdmin):
    """Admin interface for Property with comprehensive import/export functionality."""
    
    change_list_template = 'admin/properties/property/change_list.html'
    
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
        ]
        return custom_urls + urls
    
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
            return self._process_iso16757_import(request)
        
        context = {
            'title': 'Import ISO 16757 Properties',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': True,
            'dictionaries': PropertyDictionary.objects.all(),
        }
        return render(request, 'admin/properties/import_iso16757.html', context)
    
    def export_csv_view(self, request):
        """Export properties to CSV with PA code compliance."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="properties.csv"'
        
        writer = csv.writer(response)
        
        # PA code compliant headers
        headers = [
            'dictionary', 'version_number', 'revision_number',  # PA001-PA003
            'data_type', 'unit_of_measurement', 'value_domain',  # PA004-PA007
            'physical_quantity', 'classification_system', 'classification_reference',  # PA008-PA012
            'status', 'registration_authority', 'registration_date',  # PA016-PA018
            'country_of_origin', 'countries_of_use', 'creators_language',  # PA021-PA023
            'deprecation_explanation', 'first_name', 'first_definition',  # Additional fields
            'extended_attributes', 'metadata', 'created_at', 'created_by'
        ]
        writer.writerow(headers)
        
        for prop in Property.objects.select_related('dictionary', 'physical_quantity').prefetch_related('names', 'definitions'):
            first_name = prop.names.first()
            first_definition = prop.definitions.first()
            
            writer.writerow([
                prop.dictionary.name,
                prop.version_number or '',
                prop.revision_number or '',
                prop.data_type,
                prop.unit_of_measurement or '',
                prop.value_domain or '',
                prop.physical_quantity.name if prop.physical_quantity else '',
                prop.classification_system or '',
                prop.classification_reference or '',
                prop.status,
                prop.registration_authority or '',
                prop.registration_date.strftime('%Y-%m-%d') if prop.registration_date else '',
                prop.country_of_origin or '',
                prop.countries_of_use or '',
                prop.creators_language or '',
                prop.deprecation_explanation or '',
                first_name.name if first_name else '',
                first_definition.definition if first_definition else '',
                prop.extended_attributes or '',
                prop.metadata or '',
                prop.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                prop.created_by.username if prop.created_by else ''
            ])
        
        return response
    
    def _extract_core_fields(self, row):
        """Extract core Property fields from CSV row with PA code mapping."""
        # Data type mapping
        data_type_mapping = {
            'string': 'string', 'text': 'string', 'char': 'string',
            'integer': 'integer', 'int': 'integer', 'number': 'integer',
            'real': 'real', 'float': 'real', 'decimal': 'real', 'double': 'real',
            'boolean': 'boolean', 'bool': 'boolean',
            'complex': 'complex', 'compound': 'complex'
        }
        
        data_type_raw = row.get('data_type', row.get('DataType', row.get('type', 'string')))
        data_type = data_type_mapping.get(str(data_type_raw).lower().strip(), 'string')
        
        # Status mapping
        status_mapping = {
            'active': 'active', 'current': 'active', 'valid': 'active',
            'deprecated': 'deprecated', 'obsolete': 'deprecated',
            'draft': 'draft', 'proposed': 'draft',
            'withdrawn': 'withdrawn', 'invalid': 'withdrawn'
        }
        
        status_raw = row.get('status', row.get('Status', 'active'))
        status = status_mapping.get(str(status_raw).lower().strip(), 'active')
        
        core_fields = {
            # PA001-PA003: Core identification
            'version_number': row.get('version_number', row.get('version', '')),
            'revision_number': row.get('revision_number', row.get('revision', '')),
            
            # PA004-PA010: Technical specification
            'data_type': data_type,
            'unit_of_measurement': row.get('unit_of_measurement', row.get('unit', row.get('Unit', ''))),
            'value_domain': row.get('value_domain', row.get('domain', '')),
            
            # PA011-PA015: Classification
            'classification_system': row.get('classification_system', row.get('class_system', '')),
            'classification_reference': row.get('classification_reference', row.get('class_ref', '')),
            
            # PA016-PA020: Lifecycle & Authority
            'status': status,
            'registration_authority': row.get('registration_authority', row.get('authority', '')),
            'deprecation_explanation': row.get('deprecation_explanation', row.get('deprecation', '')),
            
            # PA021-PA025: Geographic & Localization
            'country_of_origin': row.get('country_of_origin', row.get('country', '')),
            'countries_of_use': row.get('countries_of_use', row.get('countries', '')),
            'creators_language': row.get('creators_language', row.get('language', ''))
        }
        
        # Handle registration date
        reg_date = row.get('registration_date', row.get('reg_date', ''))
        if reg_date:
            try:
                from datetime import datetime
                core_fields['registration_date'] = datetime.strptime(str(reg_date), '%Y-%m-%d').date()
            except:
                pass  # Skip invalid dates
        
        # Handle physical quantity
        phys_quantity = row.get('physical_quantity', row.get('quantity', ''))
        if phys_quantity:
            try:
                pq = PhysicalQuantity.objects.get(name=str(phys_quantity).strip())
                core_fields['physical_quantity'] = pq
            except PhysicalQuantity.DoesNotExist:
                pass  # Skip if not found
        
        return core_fields
    
    def _extract_extended_attributes(self, row):
        """Extract PA code data, ISO 16757, and custom attributes from CSV row."""
        # PA code compliant fields
        pa_fields = {
            'dictionary', 'version_number', 'revision_number',  # PA001-003
            'data_type', 'datatype', 'type',  # PA004
            'unit_of_measurement', 'unit',  # PA005
            'value_domain', 'domain',  # PA007
            'physical_quantity', 'quantity',  # PA008
            'classification_system', 'class_system',  # PA011
            'classification_reference', 'class_ref',  # PA012
            'status',  # PA016
            'registration_authority', 'authority',  # PA017
            'registration_date', 'reg_date',  # PA018
            'country_of_origin', 'country',  # PA021
            'countries_of_use', 'countries',  # PA022
            'creators_language', 'language',  # PA023
            'deprecation_explanation', 'deprecation',  # PA024
            # Additional core fields
            'name', 'property_name', 'definition', 'description'
        }
        
        pa_code_data = {}
        iso16757_attrs = {}
        custom_attrs = {}
        
        for key, value in row.items():
            if not value or str(value).strip() == '':
                continue
                
            clean_value = str(value).strip()
            key_lower = key.lower()
            
            if key_lower in pa_fields:
                # Store PA code data for reference
                pa_code_data[key] = clean_value
            elif any(pattern in key_lower for pattern in ['iso', '16757', 'standard', 'class']):
                # ISO 16757 specific fields
                iso16757_attrs[key] = clean_value
            elif any(pattern in key_lower for pattern in ['id', 'code', 'ref', 'guid']):
                # Identifier fields
                custom_attrs[f'identifier_{key}'] = clean_value
            elif any(pattern in key_lower for pattern in ['calc', 'formula', 'method', 'algorithm']):
                # Calculation fields
                custom_attrs[f'calculation_{key}'] = clean_value
            else:
                # Other custom fields
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
            dictionary = PropertyDictionary.objects.get(id=dictionary_id)
            
            with transaction.atomic():
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                
                reader = csv.DictReader(io_string)
                
                import_stats = {
                    'created': 0,
                    'updated': 0,
                    'skipped': 0,
                    'errors': []
                }
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        result = self._process_iso16757_row(row, dictionary, request.user)
                        import_stats[result] += 1
                        
                    except Exception as e:
                        import_stats['errors'].append(f'Row {row_num}: {str(e)}')
                        import_stats['skipped'] += 1
                
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
                else:
                    messages.success(
                        request,
                        f"ISO 16757 import successful! Created: {import_stats['created']}, "
                        f"Updated: {import_stats['updated']}"
                    )
                
        except Exception as e:
            messages.error(request, f'Import failed: {str(e)}')
        
        return redirect('admin:properties_property_changelist')
    
    def _process_iso16757_row(self, row, dictionary, user):
        """Process a single row for ISO 16757 import with PA code compliance."""
        # Validate required fields
        data_type = row.get('data_type', row.get('DataType', row.get('type', 'string')))
        unit = row.get('unit_of_measurement', row.get('unit', row.get('Unit', '')))
        
        if not data_type:
            raise ValueError("Data type field is required")
        
        core_data = self._extract_core_fields(row)
        core_data['dictionary'] = dictionary
        
        # Enhanced attribute extraction
        pa_code_data, iso16757_attrs, custom_attrs = self._extract_extended_attributes(row)
        
        # Add import metadata
        import_metadata = {
            'import_source': 'ISO_16757',
            'import_date': str(timezone.now()),
            'import_user': user.username,
            'original_row_data': dict(row)  # Store original for reference
        }
        
        # Combine metadata
        metadata = {
            'import_metadata': import_metadata,
            'pa_code_data': pa_code_data,
            'custom_attributes': custom_attrs
        }
        
        # Create or update property
        property_obj, created = Property.objects.update_or_create(
            dictionary=dictionary,
            data_type=core_data['data_type'],
            unit_of_measurement=core_data.get('unit_of_measurement', ''),
            defaults={
                **core_data,
                'extended_attributes': json.dumps(iso16757_attrs) if iso16757_attrs else None,
                'metadata': json.dumps(metadata),
                'updated_by': user,
            }
        )
        
        # Set created_by only for new objects
        if created:
            property_obj.created_by = user
            property_obj.save(update_fields=['created_by'])
            
            # Create property names and definitions
            self._create_property_names(property_obj, row)
            self._create_property_definitions(property_obj, row)
        
        return 'created' if created else 'updated'
    
    def _create_property_names(self, property_obj, row):
        """Create PropertyName instances from row data."""
        name_fields = ['name', 'Name', 'property_name', 'PropertyName']
        
        for field in name_fields:
            if field in row and row[field]:
                PropertyName.objects.get_or_create(
                    property=property_obj,
                    name=str(row[field]).strip(),
                    language='en'
                )
                break  # Only create one name per row
    
    def _create_property_definitions(self, property_obj, row):
        """Create PropertyDefinition instances from row data."""
        def_fields = ['definition', 'Definition', 'description', 'Description']
        
        for field in def_fields:
            if field in row and row[field]:
                PropertyDefinition.objects.get_or_create(
                    property=property_obj,
                    definition=str(row[field]).strip(),
                    language='en'
                )
                break  # Only create one definition per row


# Register the admin classes
admin.site.register(Property, PropertyAdmin)
admin.site.register(PropertyName)
admin.site.register(PropertyDefinition)
admin.site.register(PhysicalQuantity)
