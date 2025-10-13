import json
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Column, Layout, Row, Submit
from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import Property, PropertyDefinition, PropertyName


# best-effort shim: try to import central binding applier, otherwise noop
def apply_binding_to_field(form_instance, target_model, target_field):
    try:
        # prefer utils implementation
        from .utils import apply_binding_to_field as _impl
    except Exception:
        _impl = None
    if _impl:
        try:
            return _impl(form_instance, target_model, target_field)
        except Exception:
            return None
    # fallback noop
    return None
# from .models import Property, PropertyName, PhysicalQuantity, PropertyDictionary
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
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.request = kwargs.pop('request', None)
        self.library_slug = kwargs.pop('library_slug', None)
        super().__init__(*args, **kwargs)

        # Apply Tom Select classes to appropriate fields
        select2_fields = ['dictionary', 'status', 'data_type', 'creators_language',
                          'physical_quantity', 'countries_of_use', 'country_of_origin']
        
        for field_name in select2_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'tomselect-field form-control form-control-sm'
                })
                
        # Multi-select fields
        multi_select_fields = ['countries_of_use']
        for field_name in multi_select_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'tomselect-multiple form-control form-control-sm'
                })

        # Configure crispy form layout
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_tag = True
        self.helper.form_class = "row g-2 align-items-start"
        self.helper.label_class = "form-label small"
        self.helper.field_class = "form-control form-control-sm"
        
        # Define the layout with all fields
        self.helper.layout = Layout(
            Row(
                Column('dictionary', css_class='col-md-6'),
                Column('version_number', css_class='col-md-3'),
                Column('revision_number', css_class='col-md-3'),
            ),
            Row(
                Column('pa_code', css_class='col-md-4'),
                Column('creators_language', css_class='col-md-4'),
                Column('status', css_class='col-md-4'),
            ),
            Row(
                Column('data_type', css_class='col-md-4'),
                Column('unit_of_measurement', css_class='col-md-4'),
                Column('physical_quantity', css_class='col-md-4'),
            ),
            HTML('<hr/>'),
            Row(Column('value_domain', css_class='col-12')),
            HTML('<h5 class="mt-3">Metadata & Extended Attributes</h5>'),
            Row(
                Column('extended_attributes', css_class='col-md-6'),
                Column('metadata', css_class='col-md-6'),
            ),
            Row(
                Column('countries_of_use', css_class='col-md-6'),
                Column('country_of_origin', css_class='col-md-6'),
            ),
            Submit('save', 'Save', css_class='btn btn-primary mt-3')
        )
    
    class Meta:
        model = Property
        fields = ['dictionary', 'version_number', 'revision_number', 
                 'pa_code', 'status', 'creators_language',
                 'data_type', 'unit_of_measurement', 'physical_quantity',
                 'value_domain', 'extended_attributes', 'metadata',
                 'countries_of_use', 'country_of_origin']
        widgets = {
            # Define any special widgets here
        }

    def save(self, commit=True):
        if commit:
            instance = super().save(commit=True)
            return instance
        else:
            return super().save(commit=False)

# Provide alias for backwards compatibility / imports
PropertyFormCrisp = PropertyForm