from django.contrib import admin
from .models import Audit


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    """
    Admin for Audit model.
    """
    list_display = ('action', 'entity_type', 'entity_id', 'user', 'timestamp')
    list_filter = ('action', 'entity_type', 'user', 'timestamp')
    search_fields = ('entity_id', 'user__username', 'reason')
    readonly_fields = ('id', 'entity_type', 'entity_id', 'action', 'timestamp', 'user', 
                     'data_before', 'data_after', 'reason', 'extended_attributes',
                     'metadata', 'change_request')
    
    fieldsets = (
        (None, {
            'fields': ('id', 'entity_type', 'entity_id', 'action', 'user', 'timestamp')
        }),
        ('Change Data', {
            'fields': ('data_before', 'data_after', 'reason', 'change_request')
        }),
        ('Extended Attributes', {
            'fields': ('extended_attributes', 'metadata'),
            'classes': ('collapse',),
        }),
    )
    
    def has_add_permission(self, request):
        """
        Disable adding audit entries manually.
        """
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Disable deleting audit entries.
        """
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        Disable editing audit entries.
        """
        return False
