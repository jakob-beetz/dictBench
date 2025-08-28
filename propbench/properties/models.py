from django.db import models
from django.conf import settings
import uuid


class Property(models.Model):
    """
    Core Property model following ISO 23386 specifications.
    """
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ISO 23386 identification fields
    version_number = models.CharField(max_length=50, blank=True, null=True)
    revision_number = models.CharField(max_length=50, blank=True, null=True)
    date_of_activation = models.DateTimeField(blank=True, null=True)
    date_of_version = models.DateTimeField(blank=True, null=True)
    date_of_revision = models.DateTimeField(blank=True, null=True)
    date_of_last_change = models.DateTimeField(auto_now=True)
    date_of_deactivation = models.DateTimeField(blank=True, null=True)
    date_of_deprecation = models.DateTimeField(blank=True, null=True)
    
    # Authority information
    registration_authority = models.CharField(max_length=255, blank=True, null=True)
    registration_date = models.DateField(blank=True, null=True)
    
    # Status and localization
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('candidate', 'Candidate'),
        ('active', 'Active'),
        ('deprecated', 'Deprecated'),
        ('inactive', 'Inactive'),
        ('rejected', 'Rejected')
    ], default='draft')
    deprecation_explanation = models.TextField(blank=True)
    country_of_origin = models.CharField(max_length=50, blank=True)
    countries_of_use = models.JSONField(blank=True, null=True)
    creators_language = models.CharField(max_length=10, default='en-EN')
    
    # Data type information
    data_type = models.CharField(max_length=20, choices=[
        ('string', 'String'),
        ('integer', 'Integer'),
        ('real', 'Real'),
        ('boolean', 'Boolean'),
        ('complex', 'Complex')
    ])
    physical_quantity = models.ForeignKey('PhysicalQuantity', on_delete=models.SET_NULL, 
                                       null=True, blank=True, related_name='properties')
    unit_of_measurement = models.CharField(max_length=50, blank=True)
    value_domain = models.JSONField(blank=True, null=True)
    
    # Classification
    classification_system = models.CharField(max_length=255, blank=True, null=True)
    classification_reference = models.CharField(max_length=255, blank=True, null=True)
    
    # Dictionary association
    dictionary = models.ForeignKey('dictionaries.PropertyDictionary', on_delete=models.CASCADE, 
                                related_name='properties')
    
    # Extended attributes (non-ISO 23386 PA codes)
    extended_attributes = models.JSONField(blank=True, null=True, 
                                       help_text="Store PA codes like PA0001-PA0010 for non-standard property attributes")
    
    # Generic metadata for additional flexible storage
    metadata = models.JSONField(blank=True, null=True,
                             help_text="Flexible JSON field for storing additional metadata")
    
    # Relationships (handled via separate models)
    
    # System fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_properties')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='updated_properties')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"
        ordering = ['created_at']
    
    def __str__(self):
        # Find the English name or use the first available name
        try:
            name = self.names.filter(language='en-EN').first()
            if not name:
                name = self.names.first()
            return name.name if name else f"Property {self.guid}"
        except Exception:
            return f"Property {self.guid}"


class PropertyName(models.Model):
    """
    Model for multi-language property names.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='names')
    name = models.CharField(max_length=255)
    language = models.CharField(max_length=10)  # ISO 639 language code
    
    class Meta:
        verbose_name = "Property Name"
        verbose_name_plural = "Property Names"
    
    def __str__(self):
        return f"{self.name} ({self.language})"


class PropertyDefinition(models.Model):
    """
    Model for multi-language property definitions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='definitions')
    definition = models.TextField()
    language = models.CharField(max_length=10)  # ISO 639 language code
    
    class Meta:
        verbose_name = "Property Definition"
        verbose_name_plural = "Property Definitions"
    
    def __str__(self):
        return f"Definition in {self.language}"


class PhysicalQuantity(models.Model):
    """
    Model for physical quantities (base or derived) as defined in ISO 23386.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=[
        ('base', 'Base Quantity'),
        ('derived', 'Derived Quantity')
    ])
    formula = models.CharField(max_length=255, blank=True, 
                            help_text="For derived quantities, the formula in terms of base quantities")
    
    class Meta:
        verbose_name = "Physical Quantity"
        verbose_name_plural = "Physical Quantities"
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"


class PropertyRelationship(models.Model):
    """
    Model for relationships between properties as defined in ISO 23386.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='outgoing_relationships')
    target_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='incoming_relationships')
    relationship_type = models.CharField(max_length=50, choices=[
        ('parent-child', 'Parent-Child'),
        ('dependency', 'Dependency'),
        ('alternative', 'Alternative'),
        ('equivalent', 'Equivalent'),
        ('component', 'Component')
    ])
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['source_property', 'target_property', 'relationship_type']
        verbose_name = "Property Relationship"
        verbose_name_plural = "Property Relationships"
    
    def __str__(self):
        return f"{self.source_property} -> {self.relationship_type} -> {self.target_property}"
