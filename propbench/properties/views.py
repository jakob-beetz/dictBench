from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView, DetailView
from django.db import transaction
from .models import Property
from .forms import PropertyForm, PropertyFormCrisp, PropertyNameFormSet, PropertyDefinitionFormSet, LANGUAGE_CHOICES
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from dictionaries.models import PropertyDictionary
from reversion.models import Revision, Version
from pprint import pprint;
from .iso16757_import import parse_and_import
from django.urls import reverse_lazy
import json
from collections import defaultdict
import math

@login_required
def property_list(request):
    """List all properties."""
    properties = Property.objects.all()
    return render(request, 'properties/property_list.html', {'properties': properties})

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
def property_create(request):
    """Create a new property."""
    if request.method == 'POST':
        form = PropertyForm(request.POST, user=request.user)
        name_formset = PropertyNameFormSet(request.POST, prefix='names')
        definition_formset = PropertyDefinitionFormSet(request.POST, prefix='definitions')
        
        if form.is_valid() and name_formset.is_valid() and definition_formset.is_valid():
            property_instance = form.save(commit=False)
            
            # Ensure user fields are set
            property_instance.created_by = request.user
            property_instance.updated_by = request.user
            property_instance.save()
            
            # Save formsets
            name_formset.instance = property_instance
            name_formset.save()
            
            definition_formset.instance = property_instance
            definition_formset.save()
            
            # Save many-to-many relationships
            form.save_m2m()
            
            messages.success(request, 'Property created successfully!')
            return redirect('properties:property_detail', pk=property_instance.pk)
    else:
        form = PropertyForm(user=request.user)
        name_formset = PropertyNameFormSet(prefix='names')
        definition_formset = PropertyDefinitionFormSet(prefix='definitions')
    
    context = {
        'form': form,
        'name_formset': name_formset,
        'definition_formset': definition_formset,
        'is_new': True,
        'language_choices': LANGUAGE_CHOICES,
    }
    return render(request, 'properties/property_form.html', context)




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
        name_formset = PropertyNameFormSet(request.POST, instance=prop)
        definition_formset = PropertyDefinitionFormSet(request.POST, instance=prop)
        
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
                # Save form but delay committing so we can ensure JSON fields are Python objects
                property_instance = form.save(commit=False)

                # list of model JSON fields that use the JSONEditor/CrispyJSONField
                json_fields = [
                    "countries_of_use", "subdivisions_of_use", "permissible_units",
                    "value_domain", "external_identifiers", "dimension",
                    "defining_names", "defining_values", "tolerance",
                    "digital_format", "boundary_values", "property_media",
                    "extended_attributes", "metadata",
                ]

                for fname in json_fields:
                    if fname not in form.cleaned_data:
                        continue
                    val = form.cleaned_data.get(fname)
                    # If widget returned a JSON string, parse it to Python objects
                    if isinstance(val, str):
                        v = val.strip()
                        if v == "" or v.lower() == "null":
                            parsed = None
                        else:
                            try:
                                parsed = json.loads(v)
                            except Exception:
                                # fallback: keep raw string (avoid crash) or set None
                                parsed = None
                        setattr(property_instance, fname, parsed)
                    else:
                        # already a Python object (e.g. widget/set by form), assign directly
                        setattr(property_instance, fname, val)

                # ensure updater is recorded
                property_instance.updated_by = request.user
                property_instance.save()

                # save m2m & formsets after instance exists
                form.save_m2m()
                name_formset.instance = property_instance
                name_formset.save()
                definition_formset.instance = property_instance
                definition_formset.save()
                
                # Get primary name for success message
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
def property_delete(request, pk):
    """Delete a property."""
    prop = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        name = prop.names.first().name if prop.names.exists() else str(prop)
        prop.delete()
        messages.success(request, f'Property "{name}" deleted successfully')
        return redirect('properties:property_list')
    
    return render(request, 'properties/property_delete.html', {'property': prop})

@staff_member_required
def get_dictionaries_api(request):
    """API endpoint to get all dictionaries for dropdowns."""
    try:
        dictionaries = PropertyDictionary.objects.all().values('guid', 'name', 'description')
        dictionaries_list = list(dictionaries)
        
        # Convert UUID to string if needed
        for d in dictionaries_list:
            d['guid'] = str(d['guid'])
        
        return JsonResponse(dictionaries_list, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
            fld.widget.attrs["class"] = (cls + " form-control form-control-sm").strip()
            if hasattr(fld.widget, "attrs"):
                if fld.widget.__class__.__name__.lower().find("select") != -1:
                    fld.widget.attrs["class"] = (fld.widget.attrs.get("class", "") + " form-select form-select-sm").strip()

        # ensure helper is not trying to render a form tag and labels are shown
        if hasattr(form, "helper"):
            form.helper.form_tag = False
            form.helper.form_class = "row g-2"
            form.helper.label_class = "form-label small"
            form.helper.field_class = "form-control form-control-sm"
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
