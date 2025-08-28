from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div, Fieldset
from .models import Property, PropertyName, PropertyDefinition
from groups.models import PropertyGroup
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


class PropertyNameForm(forms.ModelForm):
    """Form for property names in different languages."""
    class Meta:
        model = PropertyName
        fields = ['name', 'language']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Property name'}),
            'language': forms.Select(choices=LANGUAGE_CHOICES, attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['language'].required = True
        self.fields['language'].choices = LANGUAGE_CHOICES


# Create formset for multiple names
PropertyNameFormSet = inlineformset_factory(
    Property, 
    PropertyName, 
    form=PropertyNameForm,
    extra=0,  # Show 1 empty form by default
    min_num=1,  # Require at least 1 name
    validate_min=True,
    can_delete=True
)


class PropertyDefinitionForm(forms.ModelForm):
    """Form for property definitions in different languages."""
    class Meta:
        model = PropertyDefinition
        fields = ['definition', 'language']
        widgets = {
            'definition': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Property definition'}),
            'language': forms.Select(choices=LANGUAGE_CHOICES, attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['definition'].required = True
        self.fields['language'].required = True
        self.fields['language'].choices = LANGUAGE_CHOICES


# Create formset for multiple definitions
PropertyDefinitionFormSet = inlineformset_factory(
    Property,
    PropertyDefinition,
    form=PropertyDefinitionForm,
    extra=0,  # Show 1 empty form by default
    min_num=1,  # Require at least 1 definition
    validate_min=True,
    can_delete=True
)


class PropertyForm(forms.ModelForm):
    """
    ISO 23386 compliant form for creating and updating properties with all mandatory and optional fields.
    """
    # Group selection with Select2
    groups = forms.ModelMultipleChoiceField(
        queryset=PropertyGroup.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'select2-multiple',
            'data-placeholder': 'Select groups...'
        }),
        required=False,
        help_text="PA006 - Groups this property belongs to"
    )
    
    class Meta:
        model = Property
        fields = [
            # Core identification (PA001)
            'dictionary', 
            
            # Technical specification (PA004-PA007)  
            'data_type', 'unit_of_measurement', 'value_domain',
            
            # Classification (PA011-PA012)
            'classification_system', 'classification_reference',
            
            # Status & Geographic (PA016, PA021-PA022)
            'status', 'country_of_origin', 'countries_of_use'
        ]
        
        widgets = {
            # Core fields with Select2
            'dictionary': forms.Select(attrs={
                'class': 'select2',
                'data-placeholder': 'Select dictionary...'
            }),
            
            # Technical fields
            'data_type': forms.Select(attrs={
                'class': 'select2',
                'data-placeholder': 'Select data type...'
            }),
            'unit_of_measurement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., m, kg, °C'
            }),
            'value_domain': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'e.g., 0-100, enum(red,green,blue)'
            }),
            
            # Classification
            'classification_system': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., IFC, BSDD, OmniClass'
            }),
            'classification_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'External reference ID'
            }),
            
            # Status & Geographic
            'status': forms.Select(attrs={
                'class': 'select2',
                'data-placeholder': 'Select status...'
            }),
            'country_of_origin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ISO country code, e.g., DE, US, GB'
            }),
            'countries_of_use': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Comma-separated ISO country codes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set up group queryset
        if self.instance and self.instance.pk and hasattr(self.instance, 'dictionary'):
            try:
                self.fields['groups'].queryset = PropertyGroup.objects.filter(
                    dictionary=self.instance.dictionary
                )
            except:
                self.fields['groups'].queryset = PropertyGroup.objects.all()
        else:
            default_dict = PropertyDictionary.objects.filter(is_default=True).first()
            if default_dict:
                self.fields['groups'].queryset = PropertyGroup.objects.filter(
                    dictionary=default_dict
                )
            else:
                self.fields['groups'].queryset = PropertyGroup.objects.all()
        
        # Set selected groups for existing properties
        if self.instance and self.instance.pk:
            try:
                if hasattr(self.instance, 'groups'):
                    self.fields['groups'].initial = self.instance.groups.all()
                elif hasattr(self.instance, 'property_groups'):
                    self.fields['groups'].initial = self.instance.property_groups.all()
                else:
                    self.fields['groups'].initial = PropertyGroup.objects.filter(properties=self.instance)
            except Exception:
                pass
        
        # Add help text with PA codes to fields
        field_help_texts = {
            'dictionary': 'PA001 - The dictionary this property belongs to',
            'data_type': 'PA004 - The data type of this property (e.g., String, Integer, Boolean)',
            'unit_of_measurement': 'PA005 - Unit of measurement for numeric properties (e.g., m, kg, °C)',
            'groups': 'PA006 - Property groups this property belongs to',
            'value_domain': 'PA007 - Permitted value range or enumeration (e.g., 0-100, enum(red,green,blue))',
            'classification_system': 'PA011 - External classification system (e.g., IFC, BSDD, OmniClass)',
            'classification_reference': 'PA012 - External reference ID in the classification system',
            'status': 'PA016 - Current status of this property (Draft, Active, Deprecated, etc.)',
            'country_of_origin': 'PA021 - ISO country code where this property originated (e.g., DE, US, GB)',
            'countries_of_use': 'PA022 - ISO country codes where this property is used (comma-separated)',
        }
        
        # Update field help texts
        for field_name, help_text in field_help_texts.items():
            if field_name in self.fields:
                self.fields[field_name].help_text = help_text
        
        # Mark required fields
        required_fields = ['dictionary', 'data_type', 'status']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
                self.fields[field_name].widget.attrs['class'] += ' required-field'
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ensure user fields are set
        if self.user:
            if not instance.pk:  # New property
                instance.created_by = self.user
            instance.updated_by = self.user
        else:
            # Fallback - this shouldn't happen in normal usage
            from django.contrib.auth import get_user_model
            User = get_user_model()
            default_user = User.objects.first()
            if default_user:
                if not instance.pk:
                    instance.created_by = default_user
                instance.updated_by = default_user
        
        if commit:
            instance.save()
            self.save_m2m()
            
            # Handle group assignments
            selected_groups = self.cleaned_data.get('groups', [])
            if hasattr(instance, 'groups'):
                instance.groups.set(selected_groups)
            elif hasattr(instance, 'property_groups'):
                instance.property_groups.set(selected_groups)
            else:
                # Handle through reverse relationship
                for group in selected_groups:
                    group.properties.add(instance)
        
        return instance