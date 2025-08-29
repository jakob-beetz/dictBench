from django.contrib import admin
from django.db import transaction
from django.contrib import messages
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import json
import csv
import io
from .models import PropertyGroup, GroupName, GroupDefinition
from dictionaries.models import PropertyDictionary


class GroupNameInline(admin.TabularInline):
    model = GroupName
    extra = 1
    fields = ('name', 'language')


class GroupDefinitionInline(admin.TabularInline):
    model = GroupDefinition
    extra = 1
    fields = ('definition', 'language')


class PropertyGroupAdmin(admin.ModelAdmin):
    """Admin interface for PropertyGroup with import functionality."""
    
    change_list_template = 'admin/groups/propertygroup/change_list.html'
    
    list_display = (
        'name', 'type', 'dictionary', 'parent_group', 
        'created_by', 'created_at', 'updated_by', 'updated_at'
    )
    list_filter = ('type', 'dictionary', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    inlines = [GroupNameInline, GroupDefinitionInline]
    
    fieldsets = (
        ('Core Information', {
            'fields': ('name', 'description', 'type', 'dictionary', 'parent_group')
        }),
        ('Extended Data', {
            'fields': ('extended_attributes', 'metadata'),
            'classes': ('collapse',),
            'description': 'JSON fields for storing ISO 16757 and custom attributes'
        }),
        ('System Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        """Set user tracking on save."""
        if not change:  # Creating new
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_urls(self):
        """Add custom import URLs."""
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv_view), 
                 name='groups_propertygroup_import_csv'),
            path('import-iso16757/', self.admin_site.admin_view(self.import_iso16757_view), 
                 name='groups_propertygroup_import_iso16757'),
            path('export-csv/', self.admin_site.admin_view(self.export_csv_view),
                 name='groups_propertygroup_export_csv'),
        ]
        return custom_urls + urls
    
    def import_csv_view(self, request):
        """Basic CSV import view with transaction management."""
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            dictionary_id = request.POST.get('dictionary_id')
            
            # Debug logging
            print(f"DEBUG: POST data: {dict(request.POST)}")
            print(f"DEBUG: FILES data: {dict(request.FILES)}")
            print(f"DEBUG: csv_file: {csv_file}")
            print(f"DEBUG: dictionary_id: {dictionary_id}")
            
            if not csv_file:
                messages.error(request, 'No CSV file was uploaded. Please select a file.')
                return redirect('admin:groups_propertygroup_import_csv')
                
            if not dictionary_id:
                messages.error(request, 'No dictionary was selected. Please select a dictionary.')
                return redirect('admin:groups_propertygroup_import_csv')
            
            try:
                dictionary = PropertyDictionary.objects.get(id=dictionary_id)
                
                with transaction.atomic():
                    # Read and process CSV
                    try:
                        # Try to read as text file first
                        if hasattr(csv_file, 'read'):
                            file_content = csv_file.read()
                            if isinstance(file_content, bytes):
                                decoded_file = file_content.decode('utf-8')
                            else:
                                decoded_file = file_content
                        else:
                            decoded_file = csv_file.decode('utf-8')
                            
                        io_string = io.StringIO(decoded_file)
                        
                        reader = csv.DictReader(io_string)
                        
                        created_count = 0
                        updated_count = 0
                        
                        for row in reader:
                            # Extract core fields
                            core_data = self._extract_core_fields(row)
                            core_data['dictionary'] = dictionary
                            
                            # Skip empty rows
                            if not core_data.get('name'):
                                continue
                            
                            # Extract extended attributes
                            iso16757_attrs, custom_attrs = self._extract_extended_attributes(row)
                            
                            # Create or update PropertyGroup
                            group, created = PropertyGroup.objects.update_or_create(
                                name=core_data['name'],
                                dictionary=dictionary,
                                defaults={
                                    **core_data,
                                    'extended_attributes': json.dumps(iso16757_attrs) if iso16757_attrs else None,
                                    'metadata': json.dumps(custom_attrs) if custom_attrs else None,
                                    'updated_by': request.user,
                                }
                            )
                            
                            # Set created_by only for new objects
                            if created:
                                group.created_by = request.user
                                group.save(update_fields=['created_by'])
                                created_count += 1
                            else:
                                updated_count += 1
                        
                        messages.success(
                            request, 
                            f'Successfully imported {created_count} new groups and updated {updated_count} existing groups.'
                        )
                        
                    except Exception as csv_error:
                        messages.error(request, f'CSV processing error: {str(csv_error)}')
                        raise csv_error
                    
            except PropertyDictionary.DoesNotExist:
                messages.error(request, f'Dictionary with ID {dictionary_id} not found.')
            except Exception as e:
                messages.error(request, f'Import failed: {str(e)}')
                import traceback
                print(f"DEBUG: Exception traceback: {traceback.format_exc()}")
            
            return redirect('admin:groups_propertygroup_changelist')
        
        # GET request - show import form
        context = {
            'title': 'Import Property Groups from CSV',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': True,
            'dictionaries': PropertyDictionary.objects.all(),
        }
        return render(request, 'admin/groups/import_csv.html', context)
    
    def import_iso16757_view(self, request):
        """ISO 16757 specific import with enhanced attribute mapping."""
        if request.method == 'POST':
            return self._process_iso16757_import(request)
        
        context = {
            'title': 'Import ISO 16757 Property Groups',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': True,
            'dictionaries': PropertyDictionary.objects.all(),
        }
        return render(request, 'admin/groups/import_iso16757.html', context)
    
    def export_csv_view(self, request):
        """Export property groups to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="property_groups.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['name', 'description', 'type', 'dictionary', 'parent_group', 'created_at'])
        
        for group in PropertyGroup.objects.select_related('dictionary', 'parent_group'):
            writer.writerow([
                group.name,
                group.description or '',
                group.type,
                group.dictionary.name,
                group.parent_group.name if group.parent_group else '',
                group.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    
    def _extract_core_fields(self, row):
        """Extract core PropertyGroup fields from CSV row."""
        core_fields = {
            'name': row.get('name', '').strip(),
            'description': row.get('description', '').strip(),
            'type': row.get('type', 'functional').strip().lower(),
        }
        
        # Validate type choice
        valid_types = ['class', 'domain', 'reference_document', 'composed_property', 
                      'alternative_use', 'collection', 'derived_quantity', 'base_quantity', 
                      'template', 'functional', 'classification']
        
        if core_fields['type'] not in valid_types:
            core_fields['type'] = 'functional'
        
        # Handle parent group if specified
        parent_name = row.get('parent_group', '').strip()
        if parent_name:
            try:
                parent = PropertyGroup.objects.get(name=parent_name)
                core_fields['parent_group'] = parent
            except PropertyGroup.DoesNotExist:
                pass  # Skip if parent doesn't exist
        
        return core_fields
    
    def _extract_extended_attributes(self, row):
        """Extract ISO 16757 and custom attributes from CSV row."""
        core_field_names = {
            'name', 'description', 'type', 'parent_group', 'dictionary'
        }
        
        iso16757_attrs = {}
        custom_attrs = {}
        
        for key, value in row.items():
            if key not in core_field_names and value and str(value).strip():
                clean_value = str(value).strip()
                
                # Categorize based on field name patterns
                if any(pattern in key.lower() for pattern in ['iso', '16757', 'standard', 'class']):
                    iso16757_attrs[key] = clean_value
                elif any(pattern in key.lower() for pattern in ['id', 'code', 'ref', 'guid']):
                    custom_attrs[f'identifier_{key}'] = clean_value
                elif any(pattern in key.lower() for pattern in ['calc', 'formula', 'method']):
                    custom_attrs[f'calculation_{key}'] = clean_value
                else:
                    custom_attrs[key] = clean_value
        
        return iso16757_attrs, custom_attrs
    
    def _process_iso16757_import(self, request):
        """Process ISO 16757 specific import with enhanced mapping."""
        csv_file = request.FILES.get('csv_file')
        dictionary_id = request.POST.get('dictionary_id')
        
        if not csv_file or not dictionary_id:
            messages.error(request, 'Please provide both CSV file and dictionary selection.')
            return redirect('admin:groups_propertygroup_import_iso16757')
        
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
        
        return redirect('admin:groups_propertygroup_changelist')
    
    def _process_iso16757_row(self, row, dictionary, user):
        """Process a single row for ISO 16757 import."""
        # Validate required fields
        if not row.get('name', '').strip():
            raise ValueError("Name field is required")
        
        core_data = self._extract_core_fields(row)
        core_data['dictionary'] = dictionary
        
        # Enhanced ISO 16757 attribute extraction
        iso16757_attrs, custom_attrs = self._extract_extended_attributes(row)
        
        # Add import metadata
        import_metadata = {
            'import_source': 'ISO_16757',
            'import_date': str(timezone.now()),
            'import_user': user.username,
            'original_row_data': dict(row)  # Store original for reference
        }
        custom_attrs['import_metadata'] = import_metadata
        
        # Create or update
        group, created = PropertyGroup.objects.update_or_create(
            name=core_data['name'],
            dictionary=dictionary,
            defaults={
                **core_data,
                'extended_attributes': json.dumps(iso16757_attrs) if iso16757_attrs else None,
                'metadata': json.dumps(custom_attrs) if custom_attrs else None,
                'updated_by': user,
            }
        )
        
        # Set created_by only for new objects
        if created:
            group.created_by = user
            group.save(update_fields=['created_by'])
        
        return 'created' if created else 'updated'


# Register the admin classes
admin.site.register(PropertyGroup, PropertyGroupAdmin)
admin.site.register(GroupName)
admin.site.register(GroupDefinition)
