from django.db import models
from django.conf import settings
import uuid


class ImportJob(models.Model):
    """
    Model for tracking import jobs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='imports/')
    file_type = models.CharField(max_length=20, choices=[
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML')
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    target_entity = models.CharField(max_length=50, choices=[
        ('property', 'Property'),
        ('group', 'Group'),
        ('dictionary', 'Dictionary'),
        ('physical_quantity', 'Physical Quantity')
    ])
    dictionary = models.ForeignKey('dictionaries.PropertyDictionary', on_delete=models.CASCADE,
                                related_name='import_jobs', null=True, blank=True)
    options = models.JSONField(blank=True, null=True)
    result_summary = models.JSONField(blank=True, null=True)
    error_log = models.TextField(blank=True)
    
    # User and timestamp information
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='import_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Import Job"
        verbose_name_plural = "Import Jobs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"


class ExportJob(models.Model):
    """
    Model for tracking export jobs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='exports/', null=True, blank=True)
    file_type = models.CharField(max_length=20, choices=[
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML')
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    source_entity = models.CharField(max_length=50, choices=[
        ('property', 'Property'),
        ('group', 'Group'),
        ('dictionary', 'Dictionary'),
        ('physical_quantity', 'Physical Quantity')
    ])
    dictionary = models.ForeignKey('dictionaries.PropertyDictionary', on_delete=models.CASCADE,
                                related_name='export_jobs', null=True, blank=True)
    filters = models.JSONField(blank=True, null=True)
    result_summary = models.JSONField(blank=True, null=True)
    error_log = models.TextField(blank=True)
    
    # User and timestamp information
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='export_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Export Job"
        verbose_name_plural = "Export Jobs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
