from django.db import models
from django.conf import settings
import uuid


class Property(models.Model):
    """
    Core Property model following ISO 23386 specifications.
    """
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # PA identifier field for handcrafted codes (PA001, PA002, etc.)
    pa_code = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        unique=False,
        help_text="Optional handcrafted PA identifier (e.g., PA001, PA002). Must be unique if provided.",
        verbose_name="PA Code "
    )
    
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
    status = models.CharField(
        max_length=20, 
        choices=[
            ('draft', 'Draft'),
            ('candidate', 'Candidate'),
            ('active', 'Active'),
            ('deprecated', 'Deprecated'),
            ('inactive', 'Inactive'),
            ('rejected', 'Rejected')
            
        ], 
        help_text="Status of the property during its life cycle",
        verbose_name="Status (PA002)",  
        default='draft')
    deprecation_explanation = models.TextField(blank=True)
    country_of_origin = models.CharField(max_length=50, blank=True)
    countries_of_use = models.JSONField(blank=True, null=True)
    subdivisions_of_use = models.JSONField(blank=True, null=True, help_text="Optional subdivisions/regions (ISO3166-2)")
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
    permissible_units = models.JSONField(blank=True, null=True, help_text="Optional list of permissible units")
    value_domain = models.JSONField(blank=True, null=True)
    
    # Classification
    classification_system = models.CharField(max_length=255, blank=True, null=True)
    classification_reference = models.CharField(max_length=255, blank=True, null=True)
    
    # Dictionary association
    dictionary = models.ForeignKey('dictionaries.PropertyDictionary', on_delete=models.CASCADE, 
                                related_name='properties')
    
    # External identifiers mapping to other dictionaries (PA014)
    external_identifiers = models.JSONField(blank=True, null=True, help_text="Map of external dictionary IDs")

    # Replaced / replacing properties (PA011 / PA012)
    replaced_properties = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='replacing_properties')

    # Dynamic property flags and parameter relations (PA031 / PA032)
    dynamic_property = models.BooleanField(default=False, help_text="Is this property a computed/dynamic property?")
    parameter_properties = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='parameter_of')

    # Dimension / exponent vector (PA028)
    dimension = models.JSONField(blank=True, null=True, help_text="Dimension exponent vector (e.g. {\"L\":1, \"T\":-2})")

    # Method of measurement (PA029)
    method_of_measurement = models.CharField(max_length=255, blank=True)

    # Array headers / defining values (PA034 / PA035)
    defining_names = models.JSONField(blank=True, null=True, help_text="Names of defining values (for arrays)")
    defining_values = models.JSONField(blank=True, null=True, help_text="Actual header values for arrays")

    # Tolerance, formats, boundaries (PA036, PA037, PA038, PA040)
    tolerance = models.JSONField(blank=True, null=True, help_text="Tolerance information")
    digital_format = models.JSONField(blank=True, null=True, help_text="Numeric/digital format (precision etc.)")
    text_format = models.CharField(max_length=255, blank=True, help_text="Text encoding/format details")
    boundary_values = models.JSONField(blank=True, null=True, help_text="Boundary intervals and units")

    # Media / visual representation (PA023)
    property_media = models.JSONField(blank=True, null=True, help_text="Media entries: url, type, caption")

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
            display_name = name.name if name else f"Property {self.guid}"
            # Include PA code if available
            if self.pa_code:
                return f"{self.pa_code}: {display_name}"
            return display_name
        except Exception:
            return f"{self.pa_code or self.guid}"


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


class PropertyExample(models.Model):
    """Model for multi-language examples for a Property (PA018).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='examples')
    example = models.TextField()
    language = models.CharField(max_length=10, blank=True)

    class Meta:
        verbose_name = 'Property Example'
        verbose_name_plural = 'Property Examples'

    def __str__(self):
        return f"Example ({self.language})"


class PropertyDescription(models.Model):
    """Alternate model for descriptions if you prefer separate storage (PA019).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='descriptions')
    description = models.TextField()
    language = models.CharField(max_length=10, blank=True)

    class Meta:
        verbose_name = 'Property Description'
        verbose_name_plural = 'Property Descriptions'

    def __str__(self):
        return f"Description ({self.language})"


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


class ExternalLibrary(models.Model):
    SCOPE_GLOBAL = "global"
    SCOPE_DICTIONARY = "dictionary"
    SCOPE_USER = "user"
    SCOPE_CHOICES = [
        (SCOPE_GLOBAL, "Global"),
        (SCOPE_DICTIONARY, "Dictionary"),
        (SCOPE_USER, "User"),
    ]

    guid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    slug = models.SlugField(max_length=200, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default=SCOPE_GLOBAL)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    dictionary = models.ForeignKey('dictionaries.PropertyDictionary', null=True, blank=True, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    version = models.CharField(max_length=50, default="1")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['scope','dictionary'])
        ]

    def __str__(self):
        return f"{self.name} ({self.slug})"


class LibraryItem(models.Model):
    guid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    library = models.ForeignKey(ExternalLibrary, related_name='items', on_delete=models.CASCADE)
    code = models.CharField(max_length=200)   # canonical code e.g. "kWh"
    label = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)  # extensible payload
    active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = ('library', 'code')
        ordering = ['order', 'label']

    def __str__(self):
        return f"{self.label} ({self.code})"


class LibraryImport(models.Model):
    """Record of uploaded file (CSV/JSON) for audit and re-import."""
    guid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    library = models.ForeignKey(ExternalLibrary, null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    raw = models.BinaryField()   # store original content
    content_type = models.CharField(max_length=100)
    notes = models.TextField(blank=True)


class FieldLibraryBinding(models.Model):
    """Configure which ExternalLibrary(ies) feed values for a specific model field.

    target_model: full app model path, e.g. "properties.Property"
    target_field: field name on the model, e.g. "unit_item"
    """
    guid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name = models.CharField(max_length=200)
    target_model = models.CharField(max_length=255, help_text="app.ModelName e.g. properties.Property")
    target_field = models.CharField(max_length=200, help_text="field name e.g. unit_item")
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} -> {self.target_model}.{self.target_field}"


class FieldLibraryBindingEntry(models.Model):
    """Orderable list of libraries used by a binding plus optional filters/transforms.

    Each entry links a binding to an ExternalLibrary and can contain a small filter/transform JSON
    that is applied when building the final option list.
    """
    guid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    binding = models.ForeignKey(FieldLibraryBinding, related_name="entries", on_delete=models.CASCADE)
    # reference to the ExternalLibrary model (kept as string import to avoid circular import on module load)
    library = models.ForeignKey('properties.ExternalLibrary', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)
    filter_json = models.JSONField(default=dict, blank=True,
                                   help_text="Optional filter e.g. {\"active\": true, \"code__startswith\":\"k\"}")
    transform_json = models.JSONField(default=dict, blank=True,
                                      help_text="Optional transform e.g. {\"label_prefix\":\"(std) \"}")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.binding.name} - {self.library.slug} (order={self.order})"
