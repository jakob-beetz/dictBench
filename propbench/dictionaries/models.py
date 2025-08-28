from django.db import models
from django.conf import settings
import uuid


class PropertyDictionary(models.Model):
    """
    Model representing a property dictionary as defined in ISO 23386.
    Users can create multiple dictionaries and switch between them.
    """
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    registration_authority = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('deprecated', 'Deprecated'),
        ('inactive', 'Inactive')
    ], default='draft')
    is_default = models.BooleanField(default=False)
    
    # Extended attributes
    extended_attributes = models.JSONField(blank=True, null=True,
                                       help_text="Dictionary-specific extended attributes")
    
    # Generic metadata
    metadata = models.JSONField(blank=True, null=True,
                             help_text="Flexible JSON field for storing additional dictionary metadata")
    
    # System fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_dictionaries')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='updated_dictionaries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_of_activation = models.DateTimeField(blank=True, null=True)
    date_of_deprecation = models.DateTimeField(blank=True, null=True)
    date_of_deactivation = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Property Dictionary"
        verbose_name_plural = "Property Dictionaries"
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} v{self.version}"
    
    def save(self, *args, **kwargs):
        # If this is set as default, unset default flag on all other dictionaries
        if self.is_default:
            PropertyDictionary.objects.filter(is_default=True).update(is_default=False)
        
        # If no dictionaries exist, make this one default
        if not PropertyDictionary.objects.exists():
            self.is_default = True
            
        super().save(*args, **kwargs)
