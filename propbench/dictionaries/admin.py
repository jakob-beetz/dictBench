from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import PropertyDictionary
from properties.models import ExternalLibrary

class DictionaryDefaultLibraryForm(forms.ModelForm):
    class Meta:
        model = PropertyDictionary
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        # admin.get_form will inject `request` into the form via get_form below
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_default_library(self):
        lib = self.cleaned_data.get('default_library')
        if not lib:
            return lib

        # Global libraries are always ok
        if lib.scope == ExternalLibrary.SCOPE_GLOBAL:
            return lib

        # Dictionary-scoped library must belong to this dictionary
        if lib.scope == ExternalLibrary.SCOPE_DICTIONARY:
            # If instance has a PK, require match
            if self.instance and self.instance.pk:
                if lib.dictionary_id != self.instance.pk:
                    raise ValidationError("Selected library is scoped to another dictionary.")
            else:
                # Creating a new dictionary: disallow picking an existing dictionary-scoped library
                # because it belongs to some other dictionary already.
                if lib.dictionary_id is not None:
                    raise ValidationError("Cannot select a library that is already scoped to another dictionary while creating a new dictionary.")
            return lib

        # User-scoped libraries: allow only the owner or superuser
        if lib.scope == ExternalLibrary.SCOPE_USER:
            req_user = getattr(self, 'request', None) and getattr(self.request, 'user', None)
            if not req_user:
                raise ValidationError("Insufficient context to validate a user-scoped library.")
            if lib.owner_id != req_user.id and not req_user.is_superuser:
                raise ValidationError("User-scoped libraries can only be used by their owner or by a superuser.")
            # It's unusual to set a user-scoped library as a dictionary default; warn or allow per policy.
            # Here we allow it only if owner matches request.user or user is superuser.
            return lib

        return lib


@admin.register(PropertyDictionary)
class PropertyDictionaryAdmin(admin.ModelAdmin):
    form = DictionaryDefaultLibraryForm
    """
    Admin for PropertyDictionary model.
    """
    list_display = ('name', 'version', 'registration_authority', 'status', 'is_default')
    list_filter = ('status', 'is_default', 'registration_authority')
    search_fields = ('name', 'description', 'registration_authority')
    readonly_fields = ('guid', 'created_at', 'updated_at', 'created_by', 'updated_by')
    fieldsets = (
        (None, {
            'fields': ('guid', 'name', 'description', 'version', 'registration_authority')
        }),
        ('Status Information', {
            'fields': ('status', 'is_default', 'date_of_activation', 'date_of_deprecation', 'date_of_deactivation')
        }),
        ('Extended Attributes', {
            'fields': ('extended_attributes', 'metadata'),
            'classes': ('collapse',),
        }),
        ('System Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to track the user who created/updated the dictionary.
        """
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """
        Inject request into the ModelForm so it can validate user-scoped libraries.
        Also wrap the form class to ensure __init__ receives request.
        """
        Form = super().get_form(request, obj, **kwargs)
        class AdminForm(Form):
            def __init__(self_inner, *args, **fkwargs):
                fkwargs['request'] = request
                super().__init__(*args, **fkwargs)
        return AdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Narrow the queryset shown for default_library in the admin.
        Show active global libraries and dictionary-scoped libraries.
        (User-scoped libraries are hidden unless the user is superuser.)
        """
        if db_field.name == 'default_library':
            qs = ExternalLibrary.objects.filter(active=True).filter(
                Q(scope=ExternalLibrary.SCOPE_GLOBAL) |
                Q(scope=ExternalLibrary.SCOPE_DICTIONARY)
            )
            # superusers may also see user-scoped libraries
            if request.user.is_superuser:
                qs = ExternalLibrary.objects.filter(active=True)
            kwargs['queryset'] = qs.order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
