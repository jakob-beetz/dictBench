from django.db import models
from django.conf import settings
import uuid


class PropertyGroup(models.Model):
    """
    Model for property groups as specified in ISO 23386.
    Implements all GA codes (GA001-GA023) from the standard.
    """
    # GA001: Globally unique identifier
    guid = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text="Globally unique identifier for the property group (GA001)",
        verbose_name="Globally unique identifier"
    )
    
    # GA002: Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='inactive',
        help_text="Status of the group during its life cycle (GA002)",
        verbose_name="Status"
    )
    
    # GA003: Date of creation (handled by created_at)
    # GA004: Date of activation
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date after which the group can be used (GA004)",
        verbose_name="Date of activation"
    )
    
    # GA005: Date of last change (handled by updated_at)
    
    # GA006: Date of revision
    revision_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date of the revision (GA006)",
        verbose_name="Date of revision"
    )
    
    # GA007: Date of version
    version_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date of the version (GA007)",
        verbose_name="Date of version"
    )
    
    # GA008: Date of deactivation
    deactivated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date group becomes obsolete (GA008)",
        verbose_name="Date of deactivation"
    )
    
    # GA009: Version number
    version_number = models.PositiveIntegerField(
        default=1,
        help_text="Major-change tracking (GA009)",
        verbose_name="Version number"
    )
    
    # GA010: Revision number
    revision_number = models.PositiveIntegerField(
        default=0,
        help_text="Minor-change tracking (GA010)",
        verbose_name="Revision number"
    )
    
    # GA011: List of replaced groups
    replaced_groups = models.JSONField(
        blank=True,
        null=True,
        help_text="GUID(s) of groups replaced by this one (GA011)",
        verbose_name="List of replaced groups"
    )
    
    # GA012: List of replacing groups
    replacing_groups = models.JSONField(
        blank=True,
        null=True,
        help_text="GUID(s) of groups replacing this one (GA012)",
        verbose_name="List of replacing groups"
    )
    
    # GA013: Deprecation explanation
    deprecation_explanation = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for deprecation in English (GA013)",
        verbose_name="Deprecation explanation"
    )
    
    # GA014: Relation of group IDs in interconnected data dictionaries
    interconnected_dictionaries = models.JSONField(
        blank=True,
        null=True,
        help_text="Pairs (internalID, dataDictionaryID) for interconnected dictionaries (GA014)",
        verbose_name="Relation of group IDs in interconnected data dictionaries"
    )
    
    # GA015: Creator's language
    creators_language = models.CharField(
        max_length=10,
        default='en-EN',
        help_text="Language of creator (ISO 639) (GA015)",
        verbose_name="Creator's language"
    )
    
    # GA016: Names in language N (handled by GroupName model with related_name='names')
    # GA017: Definitions in language N (handled by GroupDefinition model with related_name='definitions')
    
    # GA018: Visual representation
    visual_representation = models.JSONField(
        blank=True,
        null=True,
        help_text="Sketch/photo/video/URL for visual representation (GA018)",
        verbose_name="Visual representation"
    )
    
    # GA019: Country of use
    countries_of_use = models.JSONField(
        blank=True,
        null=True,
        help_text="Country(ies) of applicability (ISO 3166-1) (GA019)",
        verbose_name="Country of use"
    )
    
    # GA020: Subdivision of use
    subdivisions_of_use = models.JSONField(
        blank=True,
        null=True,
        help_text="Geographical region within country (ISO 3166-2) (GA020)",
        verbose_name="Subdivision of use"
    )
    
    # GA021: Country of origin
    country_of_origin = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        help_text="Where requirement originated (ISO 3166-1) (GA021)",
        verbose_name="Country of origin"
    )
    
    # GA022: Category of group
    CATEGORY_CHOICES = [
        ('alternative_use', 'Alternative use'),
        ('class', 'Class'),
        ('composed_property', 'Composed property'),
        ('domain', 'Domain'),
        ('reference_document', 'Reference document'),
    ]
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text="Indicates which of 5 categories (GA022)",
        verbose_name="Category of group",
        default='class'
    )
    
    # GA023: Parent group of properties
    parent_group = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_groups',
        help_text="GUID of parent group (for tree structure) (GA023)",
        verbose_name="Parent group of properties"
    )
    
    # Backward compatibility fields (deprecated, use GA codes above)
    name = models.CharField(
        max_length=255,
        help_text="Primary name (use GroupName model for multi-language support)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Primary description (use GroupDefinition model for multi-language support)"
    )
    type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
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
        ],
        help_text="Deprecated: Use 'category' field instead"
    )
    
    # Many-to-many relationship with properties
    properties = models.ManyToManyField(
        'properties.Property',
        blank=True,
        related_name='groups',
        through='PropertyGroupMembership'
    )
    
    # Extended attributes for additional non-standard GA codes
    extended_attributes = models.JSONField(
        blank=True,
        null=True,
        help_text="Store additional GA codes (GA0001-GA9999) for non-standard group attributes"
    )
    
    # Dictionary association
    dictionary = models.ForeignKey(
        'dictionaries.PropertyDictionary',
        on_delete=models.CASCADE,
        related_name='groups',
        help_text="Property dictionary this group belongs to"
    )
    
    # Generic metadata
    metadata = models.JSONField(
        blank=True,
        null=True,
        help_text="Flexible JSON field for storing additional group metadata"
    )
    
    # System fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_groups',
        help_text="User who created this group"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_groups',
        help_text="User who last updated this group"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date of validation of group-creation request (GA003)",
        verbose_name="Date of creation"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date of validation of last change request (GA005)",
        verbose_name="Date of last change"
    )
    
    class Meta:
        verbose_name = "Property Group"
        verbose_name_plural = "Property Groups"
        ordering = ['name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['created_at']),
            models.Index(fields=['version_number', 'revision_number']),
        ]
    
    def __str__(self):
        return f"{self.name} (v{self.version_number}.{self.revision_number})"
    
    def get_primary_name(self, language='en'):
        """Get the name in specified language, fallback to English, then any name."""
        name_obj = self.names.filter(language=language).first()
        if not name_obj:
            name_obj = self.names.filter(language__startswith='en').first()
        if not name_obj:
            name_obj = self.names.first()
        return name_obj.name if name_obj else self.name
    
    def get_primary_definition(self, language='en'):
        """Get the definition in specified language, fallback to English, then any definition."""
        def_obj = self.definitions.filter(language=language).first()
        if not def_obj:
            def_obj = self.definitions.filter(language__startswith='en').first()
        if not def_obj:
            def_obj = self.definitions.first()
        return def_obj.definition if def_obj else self.description


class PropertyGroupMembership(models.Model):
    """
    Through model for the many-to-many relationship between PropertyGroup and Property.
    Allows storing additional metadata about the membership.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(PropertyGroup, on_delete=models.CASCADE, related_name='memberships')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order of property within the group"
    )
    is_required = models.BooleanField(
        default=False,
        help_text="Whether this property is required in the group"
    )
    metadata = models.JSONField(
        blank=True,
        null=True,
        help_text="Additional metadata for this membership"
    )
    
    class Meta:
        unique_together = ['group', 'property']
        ordering = ['order', 'property']
        verbose_name = "Group Membership"
        verbose_name_plural = "Group Memberships"
    
    def __str__(self):
        return f"{self.property} in {self.group}"


class GroupName(models.Model):
    """
    Model for multi-language group names (GA016).
    Implements ISO 23386 requirement for names in multiple languages.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(PropertyGroup, on_delete=models.CASCADE, related_name='names')
    name = models.CharField(
        max_length=255,
        help_text="Group name in specified language (GA016)",
        verbose_name="Name"
    )
    language = models.CharField(
        max_length=10,
        help_text="ISO 639 language code (e.g., en-EN, fr-FR)",
        verbose_name="Language"
    )
    
    class Meta:
        verbose_name = "Group Name"
        verbose_name_plural = "Group Names (GA016: Names in language N)"
        indexes = [
            models.Index(fields=['language']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.language})"


class GroupDefinition(models.Model):
    """
    Model for multi-language group definitions (GA017).
    Implements ISO 23386 requirement for definitions in multiple languages.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(PropertyGroup, on_delete=models.CASCADE, related_name='definitions')
    definition = models.TextField(
        help_text="Group definition in specified language (GA017)",
        verbose_name="Definition"
    )
    language = models.CharField(
        max_length=10,
        help_text="ISO 639 language code (e.g., en-EN, fr-FR)",
        verbose_name="Language"
    )
    
    class Meta:
        verbose_name = "Group Definition"
        verbose_name_plural = "Group Definitions (GA017: Definitions in language N)"
        # unique_together = ['group', 'language']
        indexes = [
            models.Index(fields=['language']),
        ]
    
    def __str__(self):
        return f"Definition in {self.language}"
