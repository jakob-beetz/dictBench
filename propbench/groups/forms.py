from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div, Fieldset

from properties.models import Property
from .models import PropertyGroup, GroupName, GroupDefinition, PropertyGroupMembership
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


class GroupDefinitionForm(forms.ModelForm):
    """Form for property group definitions in different languages."""
    class Meta:
        model = GroupDefinition
        fields = ['definition', 'language']
        widgets = {
            'definition': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Property group definition'
            }),
            'language': forms.Select(choices=LANGUAGE_CHOICES, attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['definition'].required = True
        self.fields['language'].required = True
        self.fields['language'].choices = LANGUAGE_CHOICES


# Create formsets for names and definitions
GroupNameFormSet = inlineformset_factory(
    PropertyGroup,
    GroupName,
    form=GroupNameForm,
    extra=0,  # Change from 1 to 0 to prevent empty forms
    min_num=1,  # Require at least one name
    validate_min=True,
    can_delete=True
)

GroupDefinitionFormSet = inlineformset_factory(
    PropertyGroup,
    GroupDefinition,
    form=GroupDefinitionForm,
    extra=0,  # Change from 1 to 0 to prevent empty forms
    min_num=0,  # Definitions are optional
    can_delete=True
)


class PropertyGroupForm(forms.ModelForm):
    """Form for creating/editing property groups with all GA code fields organized in accordions."""
    
    class Meta:
        model = PropertyGroup
        fields = [
            # Basic info
            'name', 'description', 'dictionary',
            # GA002: Status
            'status',
            # GA004, GA006-GA008: Dates
            'activated_at', 'revision_date', 'version_date', 'deactivated_at',
            # GA009-GA010: Versioning
            'version_number', 'revision_number',
            # GA011-GA013: Deprecation
            'replaced_groups', 'replacing_groups', 'deprecation_explanation',
            # GA014-GA015: Internationalization
            'interconnected_dictionaries', 'creators_language',
            # GA018: Visual
            'visual_representation',
            # GA019-GA021: Geography
            'countries_of_use', 'subdivisions_of_use', 'country_of_origin',
            # GA022-GA023: Structure
            'category', 'parent_group',
            # Legacy
            'type',
            # Additional
            'extended_attributes', 'metadata',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primary group name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Primary description'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'activated_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'revision_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'version_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'deactivated_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'version_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'revision_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'deprecation_explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'creators_language': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., en-EN'}),
            'country_of_origin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ISO 3166-1 code'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'parent_group': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'dictionary': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Set initial values for new instances
        if not self.instance.pk:
            self.fields['version_number'].initial = 1
            self.fields['revision_number'].initial = 0
            self.fields['status'].initial = 'inactive'
            self.fields['creators_language'].initial = 'en-EN'
        
        # Setup Crispy Forms helper with accordion layout
        self.helper = FormHelper()
        self.helper.form_tag = False  # Form tag handled in template
        self.helper.layout = Layout(
            # Basic Information - Always visible
            Fieldset(
                'Basic Information',
                Row(
                    Column('name', css_class='col-md-6'),
                    Column('dictionary', css_class='col-md-6'),
                ),
                'description',
                css_class='mb-4'
            ),
            # GA022-GA023: Structure
            
            # Accordion for all other sections
            HTML('<div class="accordion" id="groupAccordion">'),
            
            HTML('''
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                data-bs-target="#structureSection">
                            <i class="bi bi-diagram-3 me-2"></i> Structure & Category (GA022-GA023)
                        </button>
                    </h2>
                    <div id="structureSection" class="accordion-collapse collapse" data-bs-parent="#groupAccordion">
                        <div class="accordion-body">
            '''),
            Row(
                Column('category', css_class='col-md-6'),
                Column('parent_group', css_class='col-md-6'),
            ),
            HTML('<small class="text-muted">Category defines group type; Parent creates hierarchical structure</small>'),
            HTML('</div></div></div>'),
            # GA002: Status & Lifecycle
            HTML('''
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button" type="button" data-bs-toggle="collapse" 
                                data-bs-target="#statusSection" aria-expanded="true">
                            <i class="bi bi-activity me-2"></i> Status & Lifecycle (GA002-GA008)
                        </button>
                    </h2>
                    <div id="statusSection" class="accordion-collapse collapse show" data-bs-parent="#groupAccordion">
                        <div class="accordion-body">
            '''),
            Row(
                Column('status', css_class='col-md-4'),
                Column('activated_at', css_class='col-md-4'),
                Column('deactivated_at', css_class='col-md-4'),
            ),
            Row(
                Column('revision_date', css_class='col-md-6'),
                Column('version_date', css_class='col-md-6'),
            ),
            HTML('</div></div></div>'),
            
            # GA009-GA010: Versioning
            HTML('''
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                data-bs-target="#versionSection">
                            <i class="bi bi-hash me-2"></i> Version Control (GA009-GA010)
                        </button>
                    </h2>
                    <div id="versionSection" class="accordion-collapse collapse" data-bs-parent="#groupAccordion">
                        <div class="accordion-body">
            '''),
            Row(
                Column('version_number', css_class='col-md-6'),
                Column('revision_number', css_class='col-md-6'),
            ),
            HTML('<small class="text-muted">Version for major changes, Revision for minor changes</small>'),
            HTML('</div></div></div>'),
            
            # GA011-GA013: Deprecation
            HTML('''
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                data-bs-target="#deprecationSection">
                            <i class="bi bi-exclamation-triangle me-2"></i> Deprecation (GA011-GA013)
                        </button>
                    </h2>
                    <div id="deprecationSection" class="accordion-collapse collapse" data-bs-parent="#groupAccordion">
                        <div class="accordion-body">
            '''),
            Field('replaced_groups', css_class='mb-2'),
            HTML('<small class="text-muted">JSON array of group GUIDs this group replaces</small>'),
            Field('replacing_groups', css_class='mb-2 mt-3'),
            HTML('<small class="text-muted">JSON array of group GUIDs that replace this group</small>'),
            Field('deprecation_explanation', css_class='mt-3'),
            HTML('</div></div></div>'),
            
            # GA014-GA015: Internationalization
            HTML('''
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                data-bs-target="#i18nSection">
                            <i class="bi bi-globe me-2"></i> Internationalization (GA014-GA015)
                        </button>
                    </h2>
                    <div id="i18nSection" class="accordion-collapse collapse" data-bs-parent="#groupAccordion">
                        <div class="accordion-body">
            '''),
            Field('creators_language'),
            HTML('<small class="text-muted">ISO 639 language code (e.g., en-EN, de-DE)</small>'),
            Field('interconnected_dictionaries', css_class='mt-3'),
            HTML('<small class="text-muted">JSON: pairs of (internalID, dataDictionaryID)</small>'),
            HTML('</div></div></div>'),
            
            # GA018: Visual Representation
            HTML('''
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                data-bs-target="#visualSection">
                            <i class="bi bi-image me-2"></i> Visual Representation (GA018)
                        </button>
                    </h2>
                    <div id="visualSection" class="accordion-collapse collapse" data-bs-parent="#groupAccordion">
                        <div class="accordion-body">
            '''),
            Field('visual_representation'),
            HTML('<small class="text-muted">JSON: URLs or paths to sketches, photos, videos</small>'),
            HTML('</div></div></div>'),
            
            # GA019-GA021: Geography
            HTML('''
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                data-bs-target="#geoSection">
                            <i class="bi bi-geo-alt me-2"></i> Geography (GA019-GA021)
                        </button>
                    </h2>
                    <div id="geoSection" class="accordion-collapse collapse" data-bs-parent="#groupAccordion">
                        <div class="accordion-body">
            '''),
            Field('countries_of_use'),
            HTML('<small class="text-muted">JSON array of ISO 3166-1 country codes</small>'),
            Field('subdivisions_of_use', css_class='mt-3'),
            HTML('<small class="text-muted">JSON array of ISO 3166-2 subdivision codes</small>'),
            Field('country_of_origin', css_class='mt-3'),
            HTML('<small class="text-muted">ISO 3166-1 country code where requirement originated</small>'),
            HTML('</div></div></div>'),
            
            # Advanced / Metadata
            HTML('''
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                data-bs-target="#advancedSection">
                            <i class="bi bi-gear me-2"></i> Advanced & Metadata
                        </button>
                    </h2>
                    <div id="advancedSection" class="accordion-collapse collapse" data-bs-parent="#groupAccordion">
                        <div class="accordion-body">
            '''),
            Field('type'),
            HTML('<small class="text-muted text-warning">⚠️ Deprecated: Use "category" field instead</small>'),
            Field('extended_attributes', css_class='mt-3'),
            HTML('<small class="text-muted">JSON: Additional non-standard GA codes (GA0001-GA9999)</small>'),
            Field('metadata', css_class='mt-3'),
            HTML('<small class="text-muted">JSON: Flexible storage for additional metadata</small>'),
            HTML('</div></div></div>'),
            
            HTML('</div>'),  # Close accordion
        )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set user fields if not already set
        if not instance.pk and self.user:
            instance.created_by = self.user
        if self.user:
            instance.updated_by = self.user
        
        if commit:
            instance.save()
        
        return instance


class GroupAddPropertiesForm(forms.Form):
    properties = forms.ModelMultipleChoiceField(
        queryset=Property.objects.none(),  # Set in __init__
        widget=forms.SelectMultiple(attrs={
            'class': 'tomselect-multiple form-control',
            'data-placeholder': 'Select properties to add...'
        }),
        required=True,
        label="Select properties to add to the group"
    )
    
    def __init__(self, *args, group=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get properties with their primary names
        queryset = Property.objects.all()
        
        if group:
            # Exclude properties already in the group (direct)
            existing_memberships = PropertyGroupMembership.objects.filter(group=group)
            existing_prop_pks = list(existing_memberships.values_list('property__pk', flat=True))
            
            # Also exclude inherited properties from parent groups
            if group.parent_group:
                parent = group.parent_group
                while parent:
                    parent_memberships = PropertyGroupMembership.objects.filter(group=parent)
                    existing_prop_pks.extend(parent_memberships.values_list('property__pk', flat=True))
                    parent = parent.parent_group
            
            queryset = queryset.exclude(pk__in=existing_prop_pks)
        
        self.fields['properties'].queryset = queryset.order_by('pa_code')
        
        # Optionally customize the label display
        self.fields['properties'].label_from_instance = lambda obj: f"{obj.pa_code} - {obj.names.first().name if obj.names.exists() else 'Unnamed'}"