from collections import defaultdict
import math
import csv, io, json, uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.http import JsonResponse, HttpResponseBadRequest
from dictionaries.models import PropertyDictionary
from .models import Property, PropertyName, ExternalLibrary, LibraryItem, LibraryImport
from .forms import PropertyForm, PropertyFormCrisp, PropertyNameFormSet, PropertyDefinitionFormSet, LANGUAGE_CHOICES
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.urls import reverse_lazy
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST, require_GET

from django.db import transaction
from django.contrib import messages
from django.db.models import OuterRef, Subquery, CharField, Q
from django.views.generic import CreateView, TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from .iso16757_import import parse_and_import
from reversion.models import Revision, Version
from django.template.loader import render_to_string

def import_iso16757_view(request):
    """
    POST multipart/form-data:
      - csv_file: uploaded CSV
      - mapping_file: optional uploaded JSON mapping
      - dictionary: dictionary id or object (adjust as needed)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    csv_file = request.FILES.get('csv_file')
    mapping_file = request.FILES.get('mapping_file')  # optional
    if not csv_file:
        return JsonResponse({'error': 'csv_file required'}, status=400)
    # resolve dictionary object according to your app (placeholder)
    dictionary = request.POST.get('dictionary')
    stats = parse_and_import(csv_file, dictionary, request.user, mapping_file=mapping_file)
    return JsonResponse({'stats': stats})

@login_required
def property_list(request):
    """List all properties with filtering, sorting and pagination."""
    # base queryset + annotate primary name
    # PropertyName model has no `is_primary` field (see FieldError). Order deterministically by PK.
    # If your model uses a different flag (e.g. `is_preferred`), replace 'pk' ordering with that field.
    primary_name_qs = PropertyName.objects.filter(property=OuterRef('pk')).order_by('pk')
    qs = Property.objects.select_related('dictionary').annotate(
        primary_name=Subquery(primary_name_qs.values('name')[:1], output_field=CharField())
    )

    # --- filters ---
    dictionary_id = request.GET.get('dictionary_id')
    if dictionary_id:
        qs = qs.filter(dictionary_id=dictionary_id)

    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)

    # optional text search (on primary name or pa_code) - small convenience
    q = request.GET.get('q')
    if q:
        qs = qs.filter(Q(primary_name__icontains=q) | Q(pa_code__icontains=q))

    # --- sorting ---
    sort = request.GET.get('sort', 'pk')  # allowed: name,status,pa_code,data_type,created
    sort_dir = request.GET.get('dir', 'asc')
    sort_map = {
        'name': 'primary_name',
        'status': 'status',
        'pa_code': 'pa_code',
        'data_type': 'data_type',
        'created': 'created_at',
        'pk': 'pk'
    }
    sort_field = sort_map.get(sort, 'pk')
    if sort_dir == 'desc':
        sort_field = '-' + sort_field
    qs = qs.order_by(sort_field)

    # --- pagination ---
    try:
        per_page = int(request.GET.get('per_page', 25))
        if per_page <= 0:
            per_page = 25
    except Exception:
        per_page = 25
    page_number = request.GET.get('page', 1)
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # helper lists for filter widgets
    dictionaries = PropertyDictionary.objects.all()
    statuses = list(Property.objects.values_list('status', flat=True).distinct())

    # build compact page links (handles ellipsis)
    def build_page_links(paginator, current_page, window=3):
        num_pages = paginator.num_pages
        cur = int(current_page)
        links = []
        if num_pages <= 10:
            for i in range(1, num_pages + 1):
                links.append({'num': i, 'ellipsis': False, 'current': (i == cur)})
            return links

        links.append({'num': 1, 'ellipsis': False, 'current': (1 == cur)})
        left = max(2, cur - window)
        right = min(num_pages - 1, cur + window)

        if left > 2:
            links.append({'ellipsis': True})
        for i in range(left, right + 1):
            links.append({'num': i, 'ellipsis': False, 'current': (i == cur)})
        if right < num_pages - 1:
            links.append({'ellipsis': True})

        links.append({'num': num_pages, 'ellipsis': False, 'current': (num_pages == cur)})
        return links

    page_links = build_page_links(paginator, page_obj.number)

    context = {
        'properties': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'dictionaries': dictionaries,
        'statuses': statuses,
        # echo back current filter/sort params for template
        'current': {
            'dictionary_id': dictionary_id,
            'status': status,
            'q': q or '',
            'sort': sort,
            'dir': sort_dir,
            'per_page': per_page,
        },
        'page_links': page_links,
    }
    return render(request, 'properties/property_list.html', context)

@login_required
def property_detail(request, pk):
    """Show property details."""
    prop = get_object_or_404(Property, pk=pk)
    # Bind a form to the instance for display (read-only fields are disabled in form)
    form = PropertyForm(instance=prop)

    # DEBUG: JSON dump of prop printed previously
    try:
        import json
        from django.forms.models import model_to_dict
        data = model_to_dict(prop, fields=[f.name for f in prop._meta.fields])
        print(json.dumps(data, default=str, indent=2))
    except Exception:
        pass

    return render(request, 'properties/property_detail.html', {'property': prop, 'form': form})

@login_required
def property_create(request, dictionary_slug=None):
    """Create a new property with dictionary context if provided."""
    print (f"DEBUG: Entered property_create view : {dictionary_slug=}")
    dictionary = None
    if dictionary_slug:
        dictionary = get_object_or_404(PropertyDictionary, slug=dictionary_slug)
    

    if request.method == 'POST':
        print("DEBUG: Processing POST data for property creation")
        form = PropertyForm(request.POST, user=request.user, request=request, library_slug=dictionary_slug)
        name_formset = PropertyNameFormSet(request.POST, prefix='names')
        definition_formset = PropertyDefinitionFormSet(request.POST, prefix='definitions')
        
        if form.is_valid() and name_formset.is_valid() and definition_formset.is_valid():
            # Save logic
            property = form.save(commit=False)
            property.created_by = request.user
            property.updated_by = request.user
            property.save()
            
            # Process name formset
            for name_form in name_formset:
                if name_form.cleaned_data and not name_form.cleaned_data.get('DELETE', False):
                    name = name_form.save(commit=False)
                    name.property = property
                    name.save()
                    
            # Process definition formset
            for def_form in definition_formset:
                if def_form.cleaned_data and not def_form.cleaned_data.get('DELETE', False):
                    definition = def_form.save(commit=False)
                    definition.property = property
                    definition.save()
                    
            messages.success(request, "Property created successfully!")
            return redirect('properties:property_detail', pk=property.pk)
    else:
        initial = {}
        if dictionary:
            initial['dictionary'] = dictionary
            
        form = PropertyForm(user=request.user, request=request, initial=initial, library_slug=dictionary_slug)
        name_formset = PropertyNameFormSet(prefix='names')
        definition_formset = PropertyDefinitionFormSet(prefix='definitions')
    
    return render(request, 'properties/property_form.html', {
        'form': form,
        'name_formset': name_formset,
        'definition_formset': definition_formset,
        'language_choices': LANGUAGE_CHOICES,
        'is_new': True
    })

@login_required
def property_edit(request, pk):
    """Edit an existing property."""
    prop = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        # DEBUG: dump POST and incoming form data for troubleshooting
        try:
            print('\n===== DEBUG property edit POST =====')
            print('DEBUG: request.path ->', request.path)
            # print a short sample of POST keys and values
            post_sample = {k: (v if len(str(v)) < 200 else str(v)[:200] + '...') for k, v in request.POST.items()}
            print('DEBUG: request.POST keys/values ->', post_sample)
        except Exception:
            print('DEBUG: failed to print request.POST')

        form = PropertyForm(request.POST, instance=prop, user=request.user)
        name_formset = PropertyNameFormSet(request.POST, prefix='names', instance=prop)
        definition_formset = PropertyDefinitionFormSet(request.POST, prefix='definitions', instance=prop)
        
        # Debug the formsets
        print(f"Names formset is bound: {name_formset.is_bound}")
        print(f"Names TOTAL_FORMS: {request.POST.get('names-TOTAL_FORMS')}")
        print(f"Names is valid: {name_formset.is_valid()}")
        if not name_formset.is_valid():
            print(f"Names errors: {name_formset.errors}")
            print(f"Names non-form errors: {name_formset.non_form_errors()}")
            
        # Continue with your existing view logic...

        # After forms are created, print their validation errors if any
        try:
            print('DEBUG: form.is_valid ->', getattr(form, 'is_valid', lambda: '<no form>')())
        except Exception:
            pass
        try:
            print('DEBUG: form.errors ->', getattr(form, 'errors', '<no form errors>'))
        except Exception:
            print('DEBUG: could not read form.errors')
        try:
            print('DEBUG: name_formset.is_valid ->', getattr(name_formset, 'is_valid', lambda: '<no formset>')())
        except Exception:
            pass
        try:
            print('DEBUG: name_formset.errors ->', getattr(name_formset, 'errors', '<no name_formset errors>'))
        except Exception:
            print('DEBUG: could not read name_formset.errors')
        try:
            print('DEBUG: definition_formset.is_valid ->', getattr(definition_formset, 'is_valid', lambda: '<no formset>')())
        except Exception:
            pass
        try:
            print('DEBUG: definition_formset.errors ->', getattr(definition_formset, 'errors', '<no definition_formset errors>'))
        except Exception:
            print('DEBUG: could not read definition_formset.errors')
        print('===== END DEBUG =====\n')

        if form.is_valid() and name_formset.is_valid() and definition_formset.is_valid():
            with transaction.atomic():
                property_instance = form.save(commit=False)
                # Removed manual json_fields parsing (default form handles JSONField)
                property_instance.updated_by = request.user
                property_instance.save()
                form.save_m2m()
                name_formset.instance = property_instance
                name_formset.save()
                definition_formset.instance = property_instance
                definition_formset.save()
                primary_name = property_instance.names.first()
                name_display = primary_name.name if primary_name else "Property"
                messages.success(request, f'Property "{name_display}" updated successfully')
                return redirect('properties:property_detail', pk=property_instance.guid)
    else:
        form = PropertyForm(instance=prop, user=request.user)
        name_formset = PropertyNameFormSet(instance=prop)
        definition_formset = PropertyDefinitionFormSet(instance=prop)
    
    return render(request, 'properties/property_form.html', {
        'form': form,
        'name_formset': name_formset,
        'definition_formset': definition_formset,
        'language_choices': LANGUAGE_CHOICES,
        'property': prop, 
        'is_new': False
    })

@login_required
def property_edit2(request, pk):
    """Minimal property edit view using crispy forms with Select2."""
    prop = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=prop, user=request.user)
        if form.is_valid():
            property = form.save()
            messages.success(request, f"Property updated successfully!")
            return redirect('property_detail', pk=property.pk)
    else:
        form = PropertyForm(instance=prop, user=request.user)
    
    return render(request, 'properties/property_edit2.html', {
        'form': form,
        'property': prop,
    })

@login_required
def property_delete(request, pk):
    """Delete a property."""
    prop = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        name = prop.names.first().name if prop.names.exists() else str(prop)
        prop.delete()
        messages.success(request, f'Property "{name}" deleted successfully')
        return redirect('properties:property_list')
    
    return render(request, 'properties/property_delete.html', {'property': prop})

def property_versions(request, pk):
    """Show a list of versions recorded by django-reversion for a Property (by guid)."""
    prop = get_object_or_404(Property, guid=pk)
    # Get all versions for this object (newest first)
    versions = Version.objects.get_for_object(prop)

    # Build simple list of entries for template
    entries = []
    for v in versions:
        entries.append({
            'date': getattr(v.revision, 'date_created', None),
            'user': getattr(v.revision, 'user', None),
            'comment': getattr(v.revision, 'comment', ''),
            'field_dict': getattr(v, 'field_dict', {}),
            'version_id': v.pk,
        })

    context = {
        'property': prop,
        'versions': entries,
    }
    return render(request, 'properties/property_versions.html', context)

def recent_changes(request):
    """Show recent revisions recorded by django-reversion across the site.

    Lists the latest revisions and the models/objects changed. For Property objects
    we try to read the GUID from the saved field snapshot to provide links.
    """
    revisions = Revision.objects.order_by('-date_created')[:100]
    entries = []
    for rev in revisions:
        changed = []
        for v in rev.version_set.select_related('content_type'):
            model_cls = v.content_type.model_class()
            model_name = model_cls.__name__ if model_cls else v.content_type.model
            guid = None
            try:
                fd = v.field_dict
                # Try common identifiers
                guid = fd.get('guid') or fd.get('pk') or fd.get('id')
            except Exception:
                guid = None
            changed.append({
                'model': model_name,
                'object_id': v.object_id,
                'version_id': v.pk,
                'guid': guid,
            })
        entries.append({
            'date': rev.date_created,
            'user': getattr(rev.user, 'username', None),
            'comment': rev.comment,
            'changed': changed,
        })

    return render(request, 'properties/recent_changes.html', {'revisions': entries})

@login_required
def index_view(request):
    """Render the index page."""
    return render(request, 'properties/index.html')

@login_required
def iso16757_import_view(request):
    """Handle the ISO 16757 import."""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        dictionary_id = request.POST.get('dictionary_id')
        if not csv_file or not dictionary_id:
            messages.error(request, 'Please provide both CSV and dictionary')
            return redirect('properties:iso16757_import')
        try:
            dictionary = PropertyDictionary.objects.get(pk=dictionary_id)
        except PropertyDictionary.DoesNotExist:
            messages.error(request, 'Dictionary not found')
            return redirect('properties:iso16757_import')
        try:
            stats = parse_and_import(csv_file, dictionary, request.user)
            if stats.get('errors'):
                messages.warning(request, f"Import completed with errors: {len(stats.get('errors'))} errors. Created: {stats.get('created')}, Updated: {stats.get('updated')}")
                for err in stats.get('errors')[:5]:
                    messages.error(request, err)
            else:
                messages.success(request, f"Import successful. Created: {stats.get('created')}, Updated: {stats.get('updated')}")
        except Exception as e:
            messages.error(request, f'Import failed: {e}')
        return redirect('properties:iso16757_import')

    dictionaries = PropertyDictionary.objects.all()
    return render(request, 'properties/iso16757_import.html', {'dictionaries': dictionaries})



class PropertyCreateView(CreateView):
    model = Property
    form_class = PropertyFormCrisp
    template_name = "properties/property_form_crisp.html"
    success_url = reverse_lazy("property_list")

class LoadReplacedPropertiesView(TemplateView):
    template_name = "partials/replaced_properties_dropdown.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["properties"] = Property.objects.all()
        return context

class LoadParameterPropertiesView(TemplateView):

    template_name = "partials/parameter_properties_dropdown.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["properties"] = Property.objects.all()
        return context

class PropertyCompactDetailView(LoginRequiredMixin, DetailView):
    """
    Render a compact, read-only multi-column view of a Property using
    PropertyFormCrisp (fields disabled). Template groups fields into cards.
    """
    model = Property
    template_name = "properties/property_compact_detail.html"
    context_object_name = "property"

    def _chunk_fields(self, fields, cols):
        """Distribute a flat list of fields into `cols` lists, balanced vertically."""
        if not fields:
            return [[] for _ in range(cols)]
        n = len(fields)
        per_col = math.ceil(n / cols)
        return [fields[i * per_col:(i + 1) * per_col] for i in range(cols)]

    def _build_groups(self):
        # same groups as before, but don't compute columns here
        return [
            {"title": "Identification", "cols": 2, "fields": [
                "pa_code", "status", "version_number", "revision_number", "data_type"
            ]},
            {"title": "Lifecycle / Dates", "cols": 4, "fields": [
                "date_of_activation", "date_of_version", "date_of_revision", "date_of_deactivation",
                "registration_authority", "registration_date"
            ]},
            {"title": "Origin & Classification", "cols": 2, "fields": [
                "country_of_origin", "creators_language", "dictionary", "classification_system", "classification_reference"
            ]},
            {"title": "Units & Value", "cols": 3, "fields": [
                "physical_quantity", "unit_of_measurement", "permissible_units", "value_domain", "dimension"
            ]},
            {"title": "Defining / Tolerance", "cols": 2, "fields": [
                "defining_names", "defining_values", "tolerance", "digital_format", "text_format", "boundary_values"
            ]},
            {"title": "Media & Metadata (JSON)", "cols": 2, "fields": [
                "property_media", "extended_attributes", "metadata", "external_identifiers"
            ]},
            {"title": "Relations & Flags", "cols": 2, "fields": [
                "replaced_properties", "parameter_properties", "dynamic_property", "method_of_measurement", "deprecation_explanation"
            ]},
            {"title": "System", "cols": 2, "fields": [
                "created_by", "updated_by", "created_at", "updated_at"
            ]},
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        prop = self.object
        form = PropertyFormCrisp(instance=prop)

        # make all fields read-only / compact
        for fld in form.fields.values():
            fld.disabled = True
            cls = fld.widget.attrs.get("class", "")
            fld.widget.attrs["class"] = (cls + " form-control form-control").strip()
            if hasattr(fld.widget, "attrs"):
                if fld.widget.__class__.__name__.lower().find("select") != -1:
                    fld.widget.attrs["class"] = (fld.widget.attrs.get("class", "") + " form-select form-select").strip()

        # ensure helper is not trying to render a form tag and labels are shown
        if hasattr(form, "helper"):
            form.helper.form_tag = False
            form.helper.form_class = "row g-2"
            form.helper.label_class = "form-label small"
            form.helper.field_class = "form-control form-control"
            form.helper.form_show_labels = True     # <-- ensure labels are enabled

        # --- multilingual names mapping ---
        names_by_lang = defaultdict(list)
        # assume related_name 'names' on Property -> PropertyName
        for n in prop.names.all():
            # n.language and n.name assumed; adjust if fields differ
            lang = getattr(n, "language", "") or "und"
            names_by_lang[lang].append({
                "name": getattr(n, "name", str(n)),
                "is_primary": getattr(n, "is_primary", False),
                "pk": getattr(n, "pk", None),
            })
        ctx["names_by_lang"] = dict(names_by_lang)

        # --- split group fields into columns for the template ---
        groups = self._build_groups()
        for g in groups:
            cols = g.get("cols", 1) or 1
            g["columns"] = self._chunk_fields(g.get("fields", []), cols)

        ctx["form"] = form
        ctx["groups"] = groups
        return ctx

@login_required
@require_POST
def upload_library(request):
    """
    POST multipart:
      - file: CSV or JSON
      - slug, name (optional), scope (global|dictionary|user), dictionary_id (optional)
    """
    f = request.FILES.get('file')
    if not f:
        return HttpResponseBadRequest("file required")

    slug = request.POST.get('slug') or None
    name = request.POST.get('name') or (slug or f.name)
    scope = request.POST.get('scope', ExternalLibrary.SCOPE_GLOBAL)
    dictionary_id = request.POST.get('dictionary_id')
    library = None
    # create or update library by slug if provided
    if slug:
        library, _ = ExternalLibrary.objects.get_or_create(slug=slug, defaults={
            'name': name, 'scope': scope, 'owner': request.user if scope==ExternalLibrary.SCOPE_USER else None
        })
    # record import
    raw = f.read()
    li = LibraryImport.objects.create(library=library, uploaded_by=request.user, filename=f.name, raw=raw, content_type=f.content_type or '')
    # parse file
    text = raw.decode('utf-8-sig') if isinstance(raw, (bytes,bytearray)) else str(raw)
    try:
        if f.name.lower().endswith('.json') or (text.strip().startswith('{') or text.strip().startswith('[')):
            payload = json.loads(text)
            # expected structure: { "slug":..., "name":..., "items":[{code,label,description,data,active,order}] }
            lib_slug = payload.get('slug') or slug or f.name
            library, _ = ExternalLibrary.objects.update_or_create(slug=lib_slug, defaults={
                'name': payload.get('name', name),
                'description': payload.get('description',''),
                'scope': payload.get('scope', scope),
                'metadata': payload.get('metadata',{})
            })
            items = payload.get('items', [])
            for it in items:
                LibraryItem.objects.update_or_create(library=library, code=it.get('code'), defaults={
                    'label': it.get('label', it.get('code')),
                    'description': it.get('description',''),
                    'data': it.get('data', {}),
                    'active': it.get('active', True),
                    'order': it.get('order', 0),
                })
        else:
            # assume CSV; columns: code,label,description,data_json,active,order
            reader = csv.DictReader(io.StringIO(text))
            lib_slug = slug or f.name.rsplit('.',1)[0]
            library, _ = ExternalLibrary.objects.update_or_create(slug=lib_slug, defaults={'name': name, 'scope': scope})
            for row in reader:
                data = {}
                if row.get('data_json'):
                    try:
                        data = json.loads(row.get('data_json'))
                    except Exception:
                        data = {}
                LibraryItem.objects.update_or_create(library=library, code=row.get('code') or row.get('Code') or row.get('Code'.lower()), defaults={
                    'label': row.get('label') or row.get('Name') or row.get('Label') or row.get('code'),
                    'description': row.get('description',''),
                    'data': data,
                    'active': (row.get('active','true').lower() in ('1','true','yes')),
                    'order': int(row.get('order') or 0),
                })
    except Exception as e:
        return HttpResponseBadRequest(str(e))

    return JsonResponse({'status':'ok','library': library.slug})


def library_items_autocomplete(request):
    """JSON endpoint: ?q=&libraries=slug1,slug2&mode=union|priority&page=&per_page="""
    q = request.GET.get('q', '').strip()
    libs = request.GET.get('libraries', '')
    mode = request.GET.get('mode', 'union')
    per_page = int(request.GET.get('per_page', 25))
    page = int(request.GET.get('page', 1))

    qs = LibraryItem.objects.filter(active=True)
    if libs:
        slugs = [s for s in libs.split(',') if s]
        qs = qs.filter(library__slug__in=slugs)
    if q:
        qs = qs.filter(Q(label__icontains=q) | Q(code__icontains=q))

    if mode == 'priority' and libs:
        # Walk libraries in order and collect unique codes
        results = []
        seen = set()
        for slug in slugs:
            lib_qs = LibraryItem.objects.filter(library__slug=slug, active=True)
            if q:
                lib_qs = lib_qs.filter(Q(label__icontains=q) | Q(code__icontains=q))
            for it in lib_qs.order_by('order','label')[:per_page]:
                if it.code in seen:
                    continue
                seen.add(it.code)
                results.append({'id': str(it.guid), 'text': f"{it.label} ({it.code})", 'code': it.code, 'library': it.library.slug})
                if len(results) >= 200:
                    break
        return JsonResponse({'results': results})

    paginator = Paginator(qs.order_by('library__name','order','label'), per_page)
    try:
        p = paginator.page(page)
    except Exception:
        p = paginator.page(1)

    results = [{'id': str(i.guid), 'text': f"{i.label} ({i.code})", 'code': i.code, 'library': i.library.slug} for i in p.object_list]
    return JsonResponse({'results': results, 'count': paginator.count, 'page': page, 'pages': paginator.num_pages})


def library_items_options(request):
    """Return HTML <option> elements for HTMX widgets."""
    lib = request.GET.get('library')
    q = request.GET.get('q', '')
    qs = LibraryItem.objects.filter(active=True)
    if lib:
        qs = qs.filter(library__slug=lib)
    if q:
        qs = qs.filter(Q(label__icontains=q) | Q(code__icontains=q))
    items = qs.order_by('order','label')[:200]
    html = render_to_string('properties/_library_options.html', {'items': items})
    return HttpResponse(html, content_type='text/html')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from dictionaries.models import PropertyDictionary

@login_required
def upload_library_view(request):
    """
    GET: render the user upload form.
    POST: delegate to the existing upload_library() API handler.
    """
    if request.method == "POST":
        return upload_library(request)  # assumes upload_library(request) exists and returns an HttpResponse/JsonResponse

    dictionaries = PropertyDictionary.objects.all().order_by("name")
    return render(request, "properties/upload_library.html", {"dictionaries": dictionaries})
