from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
import json
import logging
try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    # Fallback simple fuzzy matching
    def simple_fuzzy_ratio(a, b):
        a, b = a.lower(), b.lower()
        if a in b or b in a:
            return 80
        return 0
from .models import Property, PropertyName, PropertyDefinition, PhysicalQuantity
from dictionaries.models import PropertyDictionary

logger = logging.getLogger(__name__)

@method_decorator(staff_member_required, name='dispatch')
class PropertyGridView(TemplateView):
    """Main property grid management view."""
    template_name = 'admin/properties/property_grid.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Property Grid Manager',
            'app_label': 'properties',
        })
        
        # Add debug information
        from .models import Property
        from dictionaries.models import PropertyDictionary
        
        property_count = Property.objects.count()
        dictionary_count = PropertyDictionary.objects.count()
        
        print(f"DEBUG: Property Grid - Properties: {property_count}, Dictionaries: {dictionary_count}")
        
        context['debug_info'] = {
            'property_count': property_count,
            'dictionary_count': dictionary_count,
        }
        
        return context

@staff_member_required
def property_grid_data(request):
    """API endpoint to fetch property data for the grid."""
    try:
        # DEBUG: print incoming request details for diagnosis
        try:
            print(f"DEBUG property_grid_data: method={request.method}")
            print("DEBUG property_grid_data: GET ->", dict(request.GET))
            print("DEBUG property_grid_data: QUERY_STRING ->", request.META.get('QUERY_STRING', ''))
            print("DEBUG property_grid_data: CONTENT_TYPE ->", request.META.get('CONTENT_TYPE', ''))
            body_sample = None
            try:
                body_sample = request.body[:500] if getattr(request, 'body', None) else b''
                print("DEBUG property_grid_data: body (sample)->", body_sample)
            except Exception:
                print("DEBUG property_grid_data: could not read request.body")
        except Exception:
            print("DEBUG property_grid_data: failed to print request info")

        # Get query parameters
        search = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        size = int(request.GET.get('size', 50))
        sort_field = request.GET.get('sort', 'updated_at')
        sort_dir = request.GET.get('dir', 'desc')
        
        # If Tabulator sent a JSON payload via GET (e.g. payload={...}), prefer it
        payload_param = None
        try:
            if 'payload' in request.GET:
                # request.GET may expose list values; get first
                raw = request.GET.get('payload')
                if raw:
                    try:
                        # raw is expected to be a JSON string
                        parsed = json.loads(raw)
                        if isinstance(parsed, dict):
                            payload_param = parsed
                    except Exception:
                        # Try URL-unquoted then parse
                        try:
                            from urllib.parse import unquote_plus
                            parsed = json.loads(unquote_plus(raw))
                            if isinstance(parsed, dict):
                                payload_param = parsed
                        except Exception:
                            payload_param = None
        except Exception:
            payload_param = None

        # Prefer values from payload if present; else fall back to GET params
        if payload_param:
            search = (payload_param.get('search') or '').strip()
            try:
                page = int(payload_param.get('page', page))
            except Exception:
                page = int(request.GET.get('page', page))
            try:
                size = int(payload_param.get('size', size))
            except Exception:
                size = int(request.GET.get('size', size))
            # handle simple sorter extraction if provided
            sorters = payload_param.get('sorters') or payload_param.get('sort')
            if isinstance(sorters, list) and len(sorters) > 0 and isinstance(sorters[0], dict):
                sf = sorters[0].get('field')
                sd = sorters[0].get('dir', 'desc')
                if sf:
                    sort_field = sf
                    sort_dir = sd
            elif isinstance(sorters, dict):
                sort_field = sorters.get('field', sort_field)
                sort_dir = sorters.get('dir', sort_dir)
        
        # Build base queryset with optimized joins
        queryset = Property.objects.select_related(
            'dictionary', 
            'physical_quantity',
            'created_by',
            'updated_by'
        ).prefetch_related(
            Prefetch('names', queryset=PropertyName.objects.order_by('language')),
            Prefetch('definitions', queryset=PropertyDefinition.objects.order_by('language'))
        )
        
        # Apply search filter
        if search:
            search_q = (
                Q(names__name__icontains=search) |
                Q(unit_of_measurement__icontains=search) |
                Q(data_type__icontains=search) |
                Q(status__icontains=search) |
                Q(dictionary__name__icontains=search) |
                Q(physical_quantity__name__icontains=search) |
                Q(classification_reference__icontains=search)
            )
            queryset = queryset.filter(search_q).distinct()
        
        # Apply sorting
        if sort_field and sort_field in ['updated_at', 'created_at', 'data_type', 'status', 'unit_of_measurement']:
            if sort_dir == 'desc':
                sort_field = f'-{sort_field}'
            queryset = queryset.order_by(sort_field)
        else:
            queryset = queryset.order_by('-updated_at')
        
        # Count total before pagination
        total_count = queryset.count()
        
        # If no properties exist, return empty data structure
        if total_count == 0:
            return JsonResponse({
                'properties': [],
                'pagination': {
                    'page': 1,
                    'size': size,
                    'total': 0,
                    'pages': 0,
                    'has_next': False,
                    'has_prev': False,
                }
            })
        
        # Apply pagination
        paginator = Paginator(queryset, size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        properties_data = []
        for prop in page_obj:
            # Get version count (if versioning is implemented)
            version_count = getattr(prop, 'version_count', 1)
            
            # Serialize property names
            names_data = []
            for name in prop.names.all():
                names_data.append({
                    'name': name.name,
                    'language': name.language
                })
            
            # Serialize property definitions
            definitions_data = []
            for definition in prop.definitions.all():
                definitions_data.append({
                    'definition': definition.definition,
                    'language': definition.language
                })
            
            # Parse extended attributes and metadata
            extended_attributes = {}
            metadata = {}

            if prop.extended_attributes:
                try:
                    if isinstance(prop.extended_attributes, (dict, list)):
                        extended_attributes = prop.extended_attributes
                    else:
                        extended_attributes = json.loads(prop.extended_attributes)
                except Exception as ex:
                    logger.warning(f"Invalid JSON in extended_attributes for property {prop.pk}: {ex}")
                    extended_attributes = {}

            if prop.metadata:
                try:
                    if isinstance(prop.metadata, (dict, list)):
                        metadata = prop.metadata
                    else:
                        metadata = json.loads(prop.metadata)
                except Exception as ex:
                    logger.warning(f"Invalid JSON in metadata for property {prop.pk}: {ex}")
                    metadata = {}
            
            property_data = {
                'id': str(prop.pk),  # Convert UUID to string if needed
                'names': names_data,
                'definitions': definitions_data,
                'data_type': prop.data_type,
                'unit_of_measurement': prop.unit_of_measurement or '',
                'status': prop.status,
                'dictionary': str(prop.dictionary.pk) if prop.dictionary else None,
                'dictionary_name': prop.dictionary.name if prop.dictionary else None,
                'physical_quantity': str(prop.physical_quantity.pk) if prop.physical_quantity else None,
                'physical_quantity_name': prop.physical_quantity.name if prop.physical_quantity else None,
                'value_domain': prop.value_domain or '',
                'classification_reference': prop.classification_reference or '',
                'version_number': prop.version_number or '1',
                'version_count': version_count,
                'created_at': prop.created_at.isoformat() if prop.created_at else None,
                'updated_at': prop.updated_at.isoformat() if prop.updated_at else None,
                'created_by': prop.created_by.username if prop.created_by else None,
                'updated_by': prop.updated_by.username if prop.updated_by else None,
                'extended_attributes': extended_attributes,
                'metadata': metadata,
            }
            
            properties_data.append(property_data)
        
        response_data = {
            'properties': properties_data,
            'pagination': {
                'page': page,
                'size': size,
                'total': total_count,
                'pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_prev': page_obj.has_previous(),
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in property_grid_data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def create_property(request):
    """Create a new property via API."""
    try:
        data = json.loads(request.body)
        
        with transaction.atomic():
            # Get dictionary
            dictionary = get_object_or_404(PropertyDictionary, pk=data['dictionary'])
            
            # Create property
            property_obj = Property.objects.create(
                dictionary=dictionary,
                data_type=data.get('data_type', 'string'),
                unit_of_measurement=data.get('unit_of_measurement', ''),
                status=data.get('status', 'active'),
                value_domain=data.get('value_domain', ''),
                classification_reference=data.get('classification_reference', ''),
                version_number=data.get('version_number', '1'),
                created_by=request.user,
                updated_by=request.user,
            )
            
            # Handle physical quantity
            if data.get('physical_quantity_name'):
                physical_quantity, created = PhysicalQuantity.objects.get_or_create(
                    name=data['physical_quantity_name'],
                    defaults={
                        'description': f'Auto-created: {data["physical_quantity_name"]}',
                        'created_by': request.user,
                        'updated_by': request.user,
                    }
                )
                property_obj.physical_quantity = physical_quantity
                property_obj.save()
            
            # Create property names
            for name_data in data.get('names', []):
                if name_data.get('name'):
                    PropertyName.objects.create(
                        property=property_obj,
                        name=name_data['name'],
                        language=name_data.get('language', 'en'),
                        created_by=request.user,
                        updated_by=request.user,
                    )
            
            # Create property definitions if provided
            for def_data in data.get('definitions', []):
                if def_data.get('definition'):
                    PropertyDefinition.objects.create(
                        property=property_obj,
                        definition=def_data['definition'],
                        language=def_data.get('language', 'en'),
                        created_by=request.user,
                        updated_by=request.user,
                    )
            
            # Create version record for tracking
            create_property_version(property_obj, request.user, 'Created')
            
            # Return created property data
            return JsonResponse({
                'id': str(property_obj.pk),
                'message': 'Property created successfully'
            })
            
    except Exception as e:
        logger.error(f"Error creating property: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@staff_member_required
@require_http_methods(["PUT"])
@csrf_exempt
def update_property(request, property_id):
    """Update an existing property via API."""
    try:
        property_obj = get_object_or_404(Property, pk=property_id)
        data = json.loads(request.body)
        
        # Store old data for versioning
        old_data = {
            'data_type': property_obj.data_type,
            'unit_of_measurement': property_obj.unit_of_measurement,
            'status': property_obj.status,
            'value_domain': property_obj.value_domain,
            'classification_reference': property_obj.classification_reference,
        }
        
        with transaction.atomic():
            # Update basic fields
            property_obj.data_type = data.get('data_type', property_obj.data_type)
            property_obj.unit_of_measurement = data.get('unit_of_measurement', property_obj.unit_of_measurement)
            property_obj.status = data.get('status', property_obj.status)
            property_obj.value_domain = data.get('value_domain', property_obj.value_domain)
            property_obj.classification_reference = data.get('classification_reference', property_obj.classification_reference)
            property_obj.updated_by = request.user
            
            # Update dictionary if provided
            if data.get('dictionary'):
                dictionary = get_object_or_404(PropertyDictionary, pk=data['dictionary'])
                property_obj.dictionary = dictionary
            
            # Handle physical quantity
            if data.get('physical_quantity_name'):
                physical_quantity, created = PhysicalQuantity.objects.get_or_create(
                    name=data['physical_quantity_name'],
                    defaults={
                        'description': f'Auto-created: {data["physical_quantity_name"]}',
                        'created_by': request.user,
                        'updated_by': request.user,
                    }
                )
                property_obj.physical_quantity = physical_quantity
            elif 'physical_quantity_name' in data and not data['physical_quantity_name']:
                property_obj.physical_quantity = None
            
            property_obj.save()
            
            # Update property names
            if 'names' in data:
                # Remove existing names
                property_obj.names.all().delete()
                
                # Create new names
                for name_data in data['names']:
                    if name_data.get('name'):
                        PropertyName.objects.create(
                            property=property_obj,
                            name=name_data['name'],
                            language=name_data.get('language', 'en'),
                            created_by=request.user,
                            updated_by=request.user,
                        )
            
            # Calculate changes for versioning
            changes = {}
            for field, old_value in old_data.items():
                new_value = getattr(property_obj, field)
                if old_value != new_value:
                    changes[field] = {'old': old_value, 'new': new_value}
            
            # Create version record if there were changes
            if changes:
                create_property_version(property_obj, request.user, 'Updated', changes)
            
            return JsonResponse({
                'id': str(property_obj.pk),
                'message': 'Property updated successfully',
                'changes': changes
            })
            
    except Exception as e:
        logger.error(f"Error updating property {property_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@staff_member_required
@require_http_methods(["DELETE"])
@csrf_exempt
def delete_property(request, property_id):
    """Delete a property via API."""
    try:
        property_obj = get_object_or_404(Property, pk=property_id)
        
        # Store data for potential undo
        property_data = {
            'id': str(property_obj.pk),
            'data_type': property_obj.data_type,
            'unit_of_measurement': property_obj.unit_of_measurement,
            'status': property_obj.status,
            # Add more fields as needed
        }
        
        # Create version record before deletion
        create_property_version(property_obj, request.user, 'Deleted')
        
        # Soft delete or hard delete based on your preference
        property_obj.status = 'withdrawn'
        property_obj.updated_by = request.user
        property_obj.save()
        
        # Or for hard delete:
        # property_obj.delete()
        
        return JsonResponse({
            'message': 'Property deleted successfully',
            'deleted_data': property_data
        })
        
    except Exception as e:
        logger.error(f"Error deleting property {property_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def bulk_edit_properties(request):
    """Bulk edit multiple properties."""
    try:
        data = json.loads(request.body)
        action = data.get('action')
        property_ids = data.get('property_ids', [])
        
        if not property_ids:
            return JsonResponse({'error': 'No properties selected'}, status=400)
        
        # Get properties to modify
        properties = Property.objects.filter(pk__in=property_ids)
        
        if not properties.exists():
            return JsonResponse({'error': 'No valid properties found'}, status=404)
        
        modified_count = 0
        
        with transaction.atomic():
            if action == 'activate':
                modified_count = properties.update(
                    status='active',
                    updated_by=request.user,
                    updated_at=timezone.now()
                )
                
            elif action == 'deprecate':
                modified_count = properties.update(
                    status='deprecated',
                    updated_by=request.user,
                    updated_at=timezone.now()
                )
                
            elif action == 'draft':
                modified_count = properties.update(
                    status='draft',
                    updated_by=request.user,
                    updated_at=timezone.now()
                )
                
            elif action == 'move-dictionary':
                dictionary_id = data.get('dictionary_id')
                if not dictionary_id:
                    return JsonResponse({'error': 'Dictionary ID required'}, status=400)
                
                dictionary = get_object_or_404(PropertyDictionary, pk=dictionary_id)
                modified_count = properties.update(
                    dictionary=dictionary,
                    updated_by=request.user,
                    updated_at=timezone.now()
                )
                
            elif action == 'set-classification':
                classification_ref = data.get('classification_reference', '')
                modified_count = properties.update(
                    classification_reference=classification_ref,
                    updated_by=request.user,
                    updated_at=timezone.now()
                )
                
            elif action == 'delete':
                # Soft delete
                modified_count = properties.update(
                    status='withdrawn',
                    updated_by=request.user,
                    updated_at=timezone.now()
                )
                
            else:
                return JsonResponse({'error': f'Unknown action: {action}'}, status=400)
            
            # Create version records for bulk changes
            for prop in properties:
                create_property_version(prop, request.user, f'Bulk {action}')
        
        return JsonResponse({
            'message': f'Bulk {action} completed successfully',
            'modified': modified_count,
            'action': action
        })
        
    except Exception as e:
        logger.error(f"Error in bulk edit: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# Fuzzy search endpoints
@staff_member_required
def search_units(request):
    """Fuzzy search for units of measurement."""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Get unique units from existing properties
    units = Property.objects.values_list('unit_of_measurement', flat=True).distinct()
    units = [unit for unit in units if unit]  # Filter out empty units
    
    # Perform fuzzy matching
    matches = []
    for unit in units:
        if unit:
            if FUZZYWUZZY_AVAILABLE:
                score = fuzz.partial_ratio(query.lower(), unit.lower())
            else:
                score = simple_fuzzy_ratio(query.lower(), unit.lower())
            
            if score > 60:
                matches.append({
                    'value': unit,
                    'score': score
                })
    
    # Sort by score and return top matches
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    return JsonResponse({'results': matches[:10]})

@staff_member_required
def search_physical_quantities(request):
    """Fuzzy search for physical quantities."""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    quantities = PhysicalQuantity.objects.all()
    
    matches = []
    for qty in quantities:
        if FUZZYWUZZY_AVAILABLE:
            score = fuzz.partial_ratio(query.lower(), qty.name.lower())
        else:
            score = simple_fuzzy_ratio(query.lower(), qty.name.lower())
        
        if score > 60:
            matches.append({
                'value': qty.name,
                'id': str(qty.pk),
                'score': score
            })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    return JsonResponse({'results': matches[:10]})

@staff_member_required
def search_classifications(request):
    """Fuzzy search for classification references."""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Get unique classification references
    classifications = Property.objects.values_list('classification_reference', flat=True).distinct()
    classifications = [cls for cls in classifications if cls]
    
    matches = []
    for cls in classifications:
        if cls:
            if FUZZYWUZZY_AVAILABLE:
                score = fuzz.partial_ratio(query.lower(), cls.lower())
            else:
                score = simple_fuzzy_ratio(query.lower(), cls.lower())
            
            if score > 60:
                matches.append({
                    'value': cls,
                    'score': score
                })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    return JsonResponse({'results': matches[:10]})

# Helper function for versioning
def create_property_version(property_obj, user, action, changes=None):
    """Create a version record for property changes."""
    # This is a placeholder - implement according to your versioning strategy
    version_data = {
        'property_id': str(property_obj.pk),
        'action': action,
        'changes': changes or {},
        'user': user.username,
        'timestamp': timezone.now().isoformat(),
    }
    
    # Store in property metadata or separate versioning table
    try:
        if property_obj.metadata:
            metadata = json.loads(property_obj.metadata)
        else:
            metadata = {}
        
        if 'versions' not in metadata:
            metadata['versions'] = []
        
        metadata['versions'].append(version_data)
        
        # Keep only last 50 versions
        if len(metadata['versions']) > 50:
            metadata['versions'] = metadata['versions'][-50:]
        
        property_obj.metadata = json.dumps(metadata)
        property_obj.save()
        
    except Exception as e:
        logger.error(f"Error creating version record: {str(e)}")

@staff_member_required
def get_property_versions(request, property_id):
    """Get version history for a property."""
    try:
        property_obj = get_object_or_404(Property, pk=property_id)
        
        versions = []
        if property_obj.metadata:
            try:
                metadata = json.loads(property_obj.metadata)
                versions = metadata.get('versions', [])
            except json.JSONDecodeError:
                pass
        
        return JsonResponse({'versions': versions})
        
    except Exception as e:
        logger.error(f"Error getting versions for property {property_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)