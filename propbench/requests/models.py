from django.db import models
from django.conf import settings
import uuid


class ChangeRequest(models.Model):
    """
    Model for change requests as specified in ISO 23386.
    """
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Target of the change request
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, 
                              related_name='change_requests', null=True, blank=True)
    group = models.ForeignKey('groups.PropertyGroup', on_delete=models.CASCADE, 
                           related_name='change_requests', null=True, blank=True)
    dictionary = models.ForeignKey('dictionaries.PropertyDictionary', on_delete=models.CASCADE,
                                related_name='change_requests', null=True, blank=True)
    
    # Change request details
    proposed_changes = models.JSONField(help_text="JSON representation of the proposed changes")
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
        ('cancelled', 'Cancelled')
    ], default='draft')
    
    # Extended attributes for RA codes 
    extended_attributes = models.JSONField(blank=True, null=True,
                                      help_text="Store RA codes like RA0001-RA0005 for request-specific attributes")
    
    # Generic metadata
    metadata = models.JSONField(blank=True, null=True,
                             help_text="Flexible JSON field for storing additional request metadata")
    
    # Tracking information
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='requested_changes')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, 
                                 related_name='reviewed_changes', null=True, blank=True)
    approved = models.BooleanField(null=True)
    review_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    implemented_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Change Request"
        verbose_name_plural = "Change Requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class ChangeRequestComment(models.Model):
    """
    Model for comments on change requests.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    change_request = models.ForeignKey(ChangeRequest, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='request_comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Change Request Comment"
        verbose_name_plural = "Change Request Comments"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author} on {self.change_request}"


class ChangeRequestReview(models.Model):
    """
    Model for expert reviews of change requests.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    change_request = models.ForeignKey(ChangeRequest, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='performed_reviews')
    decision = models.CharField(max_length=20, choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('request_changes', 'Request Changes')
    ])
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Change Request Review"
        verbose_name_plural = "Change Request Reviews"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Review by {self.reviewer} on {self.change_request}"
