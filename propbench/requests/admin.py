from django.contrib import admin
from .models import (
    ChangeRequest, ChangeRequestComment, ChangeRequestReview
)


class ChangeRequestCommentInline(admin.TabularInline):
    model = ChangeRequestComment
    extra = 1
    readonly_fields = ('author', 'created_at', 'updated_at')


class ChangeRequestReviewInline(admin.TabularInline):
    model = ChangeRequestReview
    extra = 1
    readonly_fields = ('reviewer', 'created_at')


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    """
    Admin for ChangeRequest model.
    """
    list_display = ('title', 'status', 'requested_by', 'created_at', 'reviewed_at')
    list_filter = ('status', 'approved')
    search_fields = ('title', 'description', 'requested_by__username')
    readonly_fields = (
        'guid', 'created_at', 'updated_at', 'submitted_at', 
        'reviewed_at', 'implemented_at', 'requested_by', 'reviewed_by'
    )
    inlines = [ChangeRequestCommentInline, ChangeRequestReviewInline]
    
    fieldsets = (
        (None, {
            'fields': ('guid', 'title', 'description', 'status', 'approved')
        }),
        ('Target', {
            'fields': ('property', 'group', 'dictionary')
        }),
        ('Changes', {
            'fields': ('proposed_changes', 'review_comments')
        }),
        ('Extended Attributes', {
            'fields': ('extended_attributes', 'metadata'),
            'classes': ('collapse',),
        }),
        ('System Information', {
            'fields': (
                'requested_by', 'reviewed_by', 'created_at', 'updated_at',
                'submitted_at', 'reviewed_at', 'implemented_at'
            ),
            'classes': ('collapse',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to track the user who created the change request.
        """
        if not obj.pk:
            obj.requested_by = request.user
        super().save_model(request, obj, form, change)
