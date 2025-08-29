from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div, Fieldset
from .models import PropertyGroup, GroupName, GroupDefinition
from dictionaries.models import PropertyDictionary


# Language choices for ISO 23386 compliance
LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('de', 'German'),
    ('fr', 'French'),
    ('es', 'Spanish'),
    ('it', 'Italian'),
    ('nl', 'Dutch'),
    ('pt', 'Portuguese'),
    ('sv', 'Swedish'),
    ('da', 'Danish'),
    ('no', 'Norwegian'),
    ('fi', 'Finnish'),
    ('pl', 'Polish'),
    ('cs', 'Czech'),
    ('hu', 'Hungarian'),
    ('ru', 'Russian'),
    ('zh', 'Chinese'),
    ('ja', 'Japanese'),
    ('ko', 'Korean'),
    ('ar', 'Arabic'),
    ('other', 'Other'),
]


class GroupNameForm(forms.ModelForm):
    """Form for property group names in different languages."""
    class Meta:
        model = GroupName
        fields = ['name', 'language']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Property group name'}),
            'language': forms.Select(choices=LANGUAGE_CHOICES, attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['language'].required = True
        self.fields['language'].choices = LANGUAGE_CHOICES


# Create formset for multiple names
GroupNameFormSet = inlineformset_factory(
    PropertyGroup, 
    GroupName, 
    form=GroupNameForm,
    extra=1,  # Show 1 empty form by default
    min_num=1,  # Require at least 1 name
    validate_min=True,
    can_delete=True
)


class GroupDefinitionForm(forms.ModelForm):
    """Form for property group definitions in different languages."""
    class Meta:
        model = GroupDefinition
        fields = ['definition', 'language']
        widgets = {
            'definition': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Property group definition and purpose'}),
            'language': forms.Select(choices=LANGUAGE_CHOICES, attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['definition'].required = True
        self.fields['language'].required = True
        self.fields['language'].choices = LANGUAGE_CHOICES


# Create formset for multiple definitions
GroupDefinitionFormSet = inlineformset_factory(
    PropertyGroup,
    GroupDefinition,
    form=GroupDefinitionForm,
    extra=1,  # Show 1 empty form by default
    min_num=1,  # Require at least 1 definition
    validate_min=True,
    can_delete=True
)


class PropertyGroupForm(forms.ModelForm):
    """
    ISO 23386 compliant form for creating and updating property groups with all mandatory and optional fields.
    
    This form provides comprehensive property group management capabilities including:
    - Multi-dictionary support with hierarchical organization
    - Parent-child relationships with circular reference prevention
    - Multi-language name and definition support through related formsets
    - Group type classification and metadata management
    - Extended attributes for custom GA codes
    - Generic metadata storage for flexible group information
    
    Form Sections:
    🏛️ Core Information - Dictionary assignment, name, description, and type
    📊 Hierarchical Structure - Parent-child group relationships
    📖 Documentation & Metadata - Extended attributes and generic metadata
    📋 System Information - Audit trail and timestamps
    """
    
    # Extended attributes for custom GA codes
    extended_attributes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control json-editor',
            'rows': 4,
            'placeholder': '{"GA001": "Custom group attribute", "GA002": "Another attribute"}'
        }),
        required=False,
        help_text="JSON field for storing additional GA codes and custom group attributes"
    )
    
    # Generic metadata
    metadata = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control json-editor',
            'rows': 4,
            'placeholder': '{"usage_context": "Building materials", "scope": "International", "keywords": ["thermal", "structural"]}'
        }),
        required=False,
        help_text="JSON field for flexible metadata storage (usage context, keywords, etc.)"
    )
    
    class Meta:
        model = PropertyGroup
        fields = [
            # 🏛️ Core Information
            'dictionary', 
            'name',
            'description',
            'type',
            
            # 📊 Hierarchical Structure
            'parent_group',
            
            # 📖 Documentation & Metadata
            'extended_attributes',
            'metadata'
        ]
        
        widgets = {
            # Core fields with Select2
            'dictionary': forms.Select(attrs={
                'class': 'select2',
                'data-placeholder': 'Select dictionary...'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unique name for this group (e.g., Structural Properties)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of this property group and its purpose'
            }),
            'type': forms.Select(attrs={
                'class': 'select2',
                'data-placeholder': 'Select group type...'
            }),
            
            # Hierarchical
            'parent_group': forms.Select(attrs={
                'class': 'select2',
                'data-placeholder': 'Select parent group (optional)...'
            }),
            
            # Documentation
            'extended_attributes': forms.Textarea(attrs={
                'class': 'form-control json-editor',
                'rows': 4,
                'placeholder': '{"authority": "ISO", "standard": "23386", "revision": "2020"}'
            }),
            'metadata': forms.Textarea(attrs={
                'class': 'form-control json-editor',
                'rows': 4,
                'placeholder': '{"domain": "Construction", "usage": "International", "examples": ["Length", "Width", "Height"]}'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set up parent group queryset (exclude self to prevent circular references)
        parent_qs = PropertyGroup.objects.all()
        if self.instance and self.instance.pk:
            parent_qs = parent_qs.exclude(pk=self.instance.pk)
            # Also exclude any descendants to prevent circular references
            descendants = self._get_descendants(self.instance)
            if descendants:
                parent_qs = parent_qs.exclude(pk__in=[d.pk for d in descendants])
        
        self.fields['parent_group'].queryset = parent_qs
        
        # Add comprehensive help text with field descriptions
        field_help_texts = {
            'dictionary': 'The dictionary this property group belongs to - groups organize properties within dictionaries',
            'name': 'Unique name for this group (e.g., Structural Properties, Thermal Properties)',
            'description': 'Description of this property group and its purpose within the dictionary',
            'type': 'Classification type of this group according to ISO 23386 specifications',
            'parent_group': 'Parent group for hierarchical organization (optional) - creates a tree structure',
            'extended_attributes': 'JSON field for storing additional GA codes and custom group attributes',
            'metadata': 'JSON field for flexible metadata storage (usage context, keywords, etc.)',
        }
        
        # Update field help texts
        for field_name, help_text in field_help_texts.items():
            if field_name in self.fields:
                self.fields[field_name].help_text = help_text
        
        # Mark required fields
        required_fields = ['dictionary', 'name', 'type']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
                if 'class' in self.fields[field_name].widget.attrs:
                    self.fields[field_name].widget.attrs['class'] += ' required-field'
                else:
                    self.fields[field_name].widget.attrs['class'] = 'required-field'
    
    def _get_descendants(self, group):
        """Get all descendant groups recursively to prevent circular references."""
        descendants = []
        children = PropertyGroup.objects.filter(parent_group=group)
        for child in children:
            descendants.append(child)
            descendants.extend(self._get_descendants(child))
        return descendants
    
    def clean(self):
        """Validate form data with business rules."""
        cleaned_data = super().clean()
        parent_group = cleaned_data.get('parent_group')
        
        # Prevent circular references
        if parent_group and self.instance.pk:
            if parent_group.pk == self.instance.pk:
                raise forms.ValidationError("A group cannot be its own parent.")
            
            # Check if the parent is actually a descendant
            descendants = self._get_descendants(self.instance)
            if parent_group in descendants:
                raise forms.ValidationError("Cannot set a descendant group as parent - this would create a circular reference.")
        
        # Validate JSON fields
        extended_attributes = cleaned_data.get('extended_attributes')
        if extended_attributes:
            try:
                import json
                json.loads(extended_attributes)
            except (json.JSONDecodeError, TypeError):
                raise forms.ValidationError({
                    'extended_attributes': 'Must be valid JSON format.'
                })
        
        metadata = cleaned_data.get('metadata')
        if metadata:
            try:
                import json
                json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                raise forms.ValidationError({
                    'metadata': 'Must be valid JSON format.'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ensure user fields are set if they exist in the model
        if self.user:
            if hasattr(instance, 'created_by') and not instance.pk:
                instance.created_by = self.user
            if hasattr(instance, 'updated_by'):
                instance.updated_by = self.user
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance