from django.conf import settings
from .models import ExternalLibrary, LibraryItem, LibraryImport
import csv
import io
import json
from django.utils.text import slugify
from django.db.models import Q
from django.urls import reverse


def apply_binding_to_field(form_instance, target_model, target_field):
    """Apply FieldLibraryBinding configuration to a ModelForm field.

    Behavior:
    - Look up active FieldLibraryBinding entries for the given target_model and target_field.
    - If present, configure the form field to use a ModelChoiceField or a Select2 AJAX widget
      pointing to the library_items_autocomplete endpoint for the selected ExternalLibrary.
    - Attach a small helper on the form instance so callers can snapshot selected LibraryItem
      values into model snapshot fields (e.g., unit_code, unit_label).

    This function is permissive: if no binding exists it returns False.
    """
    try:
        from .models import FieldLibraryBinding, FieldLibraryBindingEntry, LibraryItem
        from django import forms
    except Exception:
        return False

    # find bindings that match target_model and target_field
    qs = FieldLibraryBinding.objects.filter(target_model=target_model, target_field=target_field, active=True)
    if not qs.exists():
        return False

    binding = qs.first()
    # collect ordered library entries
    entries = FieldLibraryBindingEntry.objects.filter(binding=binding).order_by('order')
    # if there's a single library, set a static queryset, otherwise use a union queryset
    libs = [e.library for e in entries if e.library and e.library.active]
    if not libs:
        return False

    # If only one library, set queryset directly
    if len(libs) == 1:
        lib = libs[0]
        items_qs = LibraryItem.objects.filter(library=lib, active=True).order_by('order', 'label')
        # replace the target form field with a ModelChoiceField so templates render choices
        try:
            form_instance.fields[target_field] = forms.ModelChoiceField(
                queryset=items_qs,
                required=form_instance.fields.get(target_field, forms.Field()).required if target_field in form_instance.fields else False,
                label=form_instance.fields.get(target_field).label if target_field in form_instance.fields else target_field,
                widget=forms.Select(attrs={'class': 'select2-library', 'data-library-slug': lib.slug})
            )
        except Exception:
            # fallback: set a CharField with hint attrs
            form_instance.fields[target_field] = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Select unit (library)'}))

        # helper to snapshot item on save
        def _snapshot_unit(instance, cleaned_data):
            sel = cleaned_data.get(target_field)
            if sel and hasattr(sel, 'code'):
                # snapshot fields on instance if present
                if hasattr(instance, 'unit_code'):
                    instance.unit_code = sel.code
                if hasattr(instance, 'unit_label'):
                    instance.unit_label = sel.label
                # store reference if model has unit_item FK
                if hasattr(instance, 'unit_item'):
                    instance.unit_item = sel

        setattr(form_instance, '_snapshot_{}_{}'.format(target_model.replace('.', '_'), target_field), _snapshot_unit)
        return True

    # Multiple libraries: configure form to use AJAX autocomplete endpoint and attach libraries list
    lib_slugs = ",".join([lib.slug for lib in libs])
    try:
        # leave form field as CharField but attach data attributes for the JS widget
        if target_field in form_instance.fields:
            w = form_instance.fields[target_field].widget
            w.attrs.setdefault('data-autocomplete-url', reverse('properties:library_items_autocomplete'))
            w.attrs.setdefault('data-library-slugs', lib_slugs)
            w.attrs.setdefault('class', (w.attrs.get('class', '') + ' select2-library-ajax').strip())
        else:
            from django import forms as _forms
            form_instance.fields[target_field] = _forms.CharField(required=False, widget=_forms.TextInput(attrs={
                'data-autocomplete-url': reverse('properties:library_items_autocomplete'),
                'data-library-slugs': lib_slugs,
                'class': 'select2-library-ajax'
            }))
    except Exception:
        return False

    def _snapshot_multiple(instance, cleaned_data):
        val = cleaned_data.get(target_field)
        # if JS returns item code, try to resolve first matching LibraryItem
        if val:
            try:
                item = LibraryItem.objects.filter(Q(code=val) | Q(label=val), library__slug__in=[lib.slug for lib in libs]).first()
                if item:
                    if hasattr(instance, 'unit_code'):
                        instance.unit_code = item.code
                    if hasattr(instance, 'unit_label'):
                        instance.unit_label = item.label
                    if hasattr(instance, 'unit_item'):
                        instance.unit_item = item
            except Exception:
                pass

    setattr(form_instance, '_snapshot_{}_{}'.format(target_model.replace('.', '_'), target_field), _snapshot_multiple)
    return True

def resolve_library_for(request, dictionary=None):
    # 1) user preference (example: profile.default_library_slug)
    user_lib = getattr(request.user, 'profile', None) and getattr(request.user.profile, 'default_library', None)
    if user_lib:
        return user_lib
    # 2) dictionary default
    if dictionary and getattr(dictionary, 'default_library', None):
        return dictionary.default_library
    # 3) global default in settings or first active global
    slug = getattr(settings, 'DEFAULT_LIBRARY_SLUG', None)
    if slug:
        try:
            return ExternalLibrary.objects.get(slug=slug, active=True)
        except ExternalLibrary.DoesNotExist:
            pass
    return ExternalLibrary.objects.filter(scope=ExternalLibrary.SCOPE_GLOBAL, active=True).first()

def parse_library(raw, filename, user=None, library_instance=None, scope=None, dictionary=None, slug=None, name=None):
    """Parse CSV or JSON raw bytes/string and upsert ExternalLibrary and LibraryItem entries.

    Returns the ExternalLibrary instance.
    """
    text = raw.decode('utf-8-sig') if isinstance(raw, (bytes, bytearray)) else str(raw)
    # record raw import for audit
    LibraryImport.objects.create(library=library_instance, uploaded_by=user, filename=filename, raw=raw, content_type='')

    # determine JSON vs CSV
    try:
        if filename.lower().endswith('.json') or text.strip().startswith(('{', '[')):
            payload = json.loads(text)
            lib_slug = payload.get('slug') or slug or slugify(name or filename.rsplit('.', 1)[0])
            library, _ = ExternalLibrary.objects.update_or_create(slug=lib_slug, defaults={
                'name': payload.get('name', name or lib_slug),
                'description': payload.get('description', ''),
                'scope': payload.get('scope', scope or ExternalLibrary.SCOPE_GLOBAL),
                'metadata': payload.get('metadata', {}),
            })
            if dictionary:
                library.dictionary = dictionary
                library.save()
            items = payload.get('items', [])
            for it in items:
                LibraryItem.objects.update_or_create(library=library, code=it.get('code'), defaults={
                    'label': it.get('label') or it.get('code'),
                    'description': it.get('description', ''),
                    'data': it.get('data', {}),
                    'active': it.get('active', True),
                    'order': it.get('order', 0),
                })
            return library
        else:
            reader = csv.DictReader(io.StringIO(text))
            lib_slug = slug or slugify(name or filename.rsplit('.', 1)[0])
            library, _ = ExternalLibrary.objects.update_or_create(slug=lib_slug, defaults={'name': name or lib_slug, 'scope': scope or ExternalLibrary.SCOPE_GLOBAL})
            if dictionary:
                library.dictionary = dictionary
                library.save()
            for row in reader:
                data = {}
                if row.get('data_json'):
                    try:
                        data = json.loads(row.get('data_json'))
                    except Exception:
                        data = {}
                code = row.get('code') or row.get('Code') or row.get('Code'.lower())
                label = row.get('label') or row.get('Label') or row.get('name') or code
                if not code:
                    continue
                LibraryItem.objects.update_or_create(library=library, code=code, defaults={
                    'label': label,
                    'description': row.get('description', ''),
                    'data': data,
                    'active': (str(row.get('active', 'true')).lower() in ('1', 'true', 'yes')),
                    'order': int(row.get('order') or 0),
                })
            return library
    except Exception:
        # bubble up to caller
        raise