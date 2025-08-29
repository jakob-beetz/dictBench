from django.db import models
from django.conf import settings
import uuid


class PropertyGroup(models.Model):
    """
    Model for property groups as specified in ISO 23386.
    """
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=[
        ('class', 'Class'),
        ('domain', 'Domain'),
        ('reference_document', 'Reference Document'),
        ('composed_property', 'Composed Property'),
        ('alternative_use', 'Alternative Use'),
        ('collection', 'Collection'),
        ('derived_quantity', 'Derived Quantity'),
        ('base_quantity', 'Base Quantity'),
        ('template', 'Template'),
        ('functional', 'Functional Group'),
        ('classification', 'Classification Group')
    ])
    parent_group = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_groups')
    properties = models.ManyToManyField('properties.Property', blank=True, related_name='groups', through='PropertyGroupMembership')
    
    # Extended attributes for GA codes
    extended_attributes = models.JSONField(blank=True, null=True, 
                                       help_text="Store GA codes like GA0001-GA0005 for non-standard group attributes")
    
    # Dictionary association
    dictionary = models.ForeignKey('dictionaries.PropertyDictionary', on_delete=models.CASCADE, 
                                related_name='groups')
    
    # Generic metadata
    metadata = models.JSONField(blank=True, null=True,
                             help_text="Flexible JSON field for storing additional group metadata")
    
    # System fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_groups')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='updated_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Property Group"
        verbose_name_plural = "Property Groups"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class PropertyGroupMembership(models.Model):
    """
    Through model for the many-to-many relationship between PropertyGroup and Property.
    Allows storing additional metadata about the membership.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(PropertyGroup, on_delete=models.CASCADE)
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=False)
    metadata = models.JSONField(blank=True, null=True)
    
    class Meta:
        unique_together = ['group', 'property']
        ordering = ['order']
        verbose_name = "Group Membership"
        verbose_name_plural = "Group Memberships"
    
    def __str__(self):
        return f"{self.property} in {self.group}"


class GroupName(models.Model):
    """
    Model for multi-language group names.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(PropertyGroup, on_delete=models.CASCADE, related_name='names')
    name = models.CharField(max_length=255)
    language = models.CharField(max_length=10)  # ISO 639 language code
    
    class Meta:
        verbose_name = "Group Name"
        verbose_name_plural = "Group Names"
    
    def __str__(self):
        return f"{self.name} ({self.language})"


class GroupDefinition(models.Model):
    """
    Model for multi-language group definitions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(PropertyGroup, on_delete=models.CASCADE, related_name='definitions')
    definition = models.TextField()
    language = models.CharField(max_length=10)  # ISO 639 language code
    
    class Meta:
        verbose_name = "Group Definition"
        verbose_name_plural = "Group Definitions"
    
    def __str__(self):
        return f"Definition in {self.language}"
