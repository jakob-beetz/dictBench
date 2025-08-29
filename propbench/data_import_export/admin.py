from django.contrib import admin
from .models import ImportJob, ExportJob


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    """
    Admin for ImportJob model.
    """
    list_display = ('name', 'status', 'file_type', 'target_entity', 'created_by', 'created_at')
    list_filter = ('status', 'file_type', 'target_entity')
    search_fields = ('name', 'description', 'created_by__username')
    readonly_fields = ('id', 'created_by', 'created_at', 'updated_at', 'started_at', 'completed_at')
    
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'description', 'file', 'file_type')
        }),
        ('Import Configuration', {
            'fields': ('target_entity', 'dictionary', 'options')
        }),
        ('Status', {
            'fields': ('status', 'result_summary', 'error_log')
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at', 'started_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to track the user who created the import job.
        """
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    """
    Admin for ExportJob model.
    """
    list_display = ('name', 'status', 'file_type', 'source_entity', 'created_by', 'created_at')
    list_filter = ('status', 'file_type', 'source_entity')
    search_fields = ('name', 'description', 'created_by__username')
    readonly_fields = ('id', 'created_by', 'created_at', 'updated_at', 'started_at', 'completed_at')
    
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'description', 'file', 'file_type')
        }),
        ('Export Configuration', {
            'fields': ('source_entity', 'dictionary', 'filters')
        }),
        ('Status', {
            'fields': ('status', 'result_summary', 'error_log')
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at', 'started_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to track the user who created the export job.
        """
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
