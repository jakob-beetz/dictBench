from django.contrib import admin
from .models import (
    PropertyGroup, PropertyGroupMembership, GroupName, GroupDefinition
)


class GroupNameInline(admin.TabularInline):
    model = GroupName
    extra = 1


class GroupDefinitionInline(admin.TabularInline):
    model = GroupDefinition
    extra = 1


class PropertyGroupMembershipInline(admin.TabularInline):
    model = PropertyGroupMembership
    extra = 1
    autocomplete_fields = ['property']


@admin.register(PropertyGroup)
class PropertyGroupAdmin(admin.ModelAdmin):
    """
    Admin for PropertyGroup model.
    """
    list_display = ('name', 'type', 'dictionary', 'parent_group')
    list_filter = ('type', 'dictionary')
    search_fields = ('name', 'description', 'names__name')
    readonly_fields = ('guid', 'created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = [GroupNameInline, GroupDefinitionInline, PropertyGroupMembershipInline]
    
    fieldsets = (
        (None, {
            'fields': ('guid', 'name', 'description', 'type', 'dictionary', 'parent_group')
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
        Override save_model to track the user who created/updated the group.
        """
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PropertyGroupMembership)
class PropertyGroupMembershipAdmin(admin.ModelAdmin):
    """
    Admin for PropertyGroupMembership model.
    """
    list_display = ('property', 'group', 'order', 'is_required')
    list_filter = ('group', 'is_required')
    search_fields = ('property__names__name', 'group__name')
    autocomplete_fields = ['property', 'group']
    
    fieldsets = (
        (None, {
            'fields': ('group', 'property', 'order', 'is_required')
        }),
        ('Additional Information', {
            'fields': ('metadata',),
            'classes': ('collapse',),
        }),
    )
