from django.db import models
from django.conf import settings
import uuid


class Audit(models.Model):
    """
    Comprehensive audit log model for tracking all changes to ISO 23386 entities.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=100, help_text="The type of entity being audited (Property, Group, etc.)")
    entity_id = models.CharField(max_length=100, help_text="The UUID of the entity being audited")
    action = models.CharField(max_length=50, choices=[
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('deprecate', 'Deprecate'),
        ('restore', 'Restore'),
        ('status_change', 'Status Change'),
        ('relationship_add', 'Add Relationship'),
        ('relationship_remove', 'Remove Relationship'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('implement', 'Implement'),
        ('submit', 'Submit')
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='audit_logs')
    data_before = models.JSONField(null=True, blank=True)
    data_after = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True)
    
    # Extended attributes for DA codes
    extended_attributes = models.JSONField(blank=True, null=True,
                                       help_text="Store DA codes like DA0001-DA0005 for audit-specific attributes")
    
    # Generic metadata
    metadata = models.JSONField(blank=True, null=True,
                             help_text="Flexible JSON field for storing additional audit metadata")
    
    # Related change request (if applicable)
    change_request = models.ForeignKey('requests.ChangeRequest', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='audit_logs')
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.action} on {self.entity_type} {self.entity_id} by {self.user}"
