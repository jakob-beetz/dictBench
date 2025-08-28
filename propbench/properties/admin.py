from django.contrib import admin
from .models import (
    Property, PropertyName, PropertyDefinition, 
    PhysicalQuantity, PropertyRelationship
)


class PropertyNameInline(admin.TabularInline):
    model = PropertyName
    extra = 1


class PropertyDefinitionInline(admin.TabularInline):
    model = PropertyDefinition
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """
    Admin for Property model.
    """
    list_display = ('get_name', 'data_type', 'status', 'registration_authority', 'dictionary')
    list_filter = ('status', 'data_type', 'dictionary', 'registration_authority')
    search_fields = ('names__name', 'guid', 'registration_authority')
    readonly_fields = (
        'guid', 'created_at', 'updated_at', 'date_of_last_change',
        'created_by', 'updated_by'
    )
    inlines = [PropertyNameInline, PropertyDefinitionInline]
    
    fieldsets = (
        (None, {
            'fields': ('guid', 'dictionary', 'data_type', 'physical_quantity', 'unit_of_measurement')
        }),
        ('Status Information', {
            'fields': (
                'status', 'version_number', 'revision_number', 
                'date_of_activation', 'date_of_version', 'date_of_revision',
                'date_of_last_change', 'date_of_deactivation', 'date_of_deprecation',
                'deprecation_explanation'
            )
        }),
        ('Registration Information', {
            'fields': (
                'registration_authority', 'registration_date', 'country_of_origin',
                'countries_of_use', 'creators_language'
            )
        }),
        ('Data Constraints', {
            'fields': ('value_domain',)
        }),
        ('Classification', {
            'fields': ('classification_system', 'classification_reference')
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
    
    def get_name(self, obj):
        """
        Get the English name of the property or the first available name.
        """
        name = obj.names.filter(language='en-EN').first()
        if not name:
            name = obj.names.first()
        return name.name if name else f"Property {obj.guid}"
    get_name.short_description = 'Name'
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to track the user who created/updated the property.
        """
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PhysicalQuantity)
class PhysicalQuantityAdmin(admin.ModelAdmin):
    """
    Admin for PhysicalQuantity model.
    """
    list_display = ('name', 'symbol', 'type')
    list_filter = ('type',)
    search_fields = ('name', 'symbol', 'description')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'symbol', 'description', 'type')
        }),
        ('Formula (for derived quantities)', {
            'fields': ('formula',),
            'classes': ('collapse',),
        }),
    )


@admin.register(PropertyRelationship)
class PropertyRelationshipAdmin(admin.ModelAdmin):
    """
    Admin for PropertyRelationship model.
    """
    list_display = ('source_property', 'relationship_type', 'target_property')
    list_filter = ('relationship_type',)
    search_fields = ('source_property__names__name', 'target_property__names__name', 'description')
    
    fieldsets = (
        (None, {
            'fields': ('source_property', 'relationship_type', 'target_property', 'description')
        }),
    )
