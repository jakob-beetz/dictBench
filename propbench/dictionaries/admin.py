from django.contrib import admin
from .models import PropertyDictionary


@admin.register(PropertyDictionary)
class PropertyDictionaryAdmin(admin.ModelAdmin):
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
