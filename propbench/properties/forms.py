from django import forms
from django.forms import inlineformset_factory, ModelForm
from .models import Property, PropertyName, PropertyDefinition, PhysicalQuantity
from groups.models import PropertyGroup
from dictionaries.models import PropertyDictionary
import json
from .widgets import JSONEditorWidget

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Row, Column, HTML
from crispy_forms.bootstrap import StrictButton
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


class PropertyForm(ModelForm):
    """
    ISO 23386 compliant form for creating and updating properties with all mandatory and optional fields.
    
    This form provides comprehensive property management capabilities including:
    - Multi-dictionary support with automatic group filtering
    - ISO 23386 PA code compliance (PA001-PA022 implemented)
    - Technical specifications with data types and units
    - Classification systems integration (IFC, BSDD, OmniClass)
    - Geographic and regulatory context management
    - User audit trail and version control
    - Multi-language support through related formsets
    
    Form Sections:
    🏛️ Core Information - Dictionary assignment and basic identification
    ⚙️ Technical Specifications - Data types, units, value domains  
    🏷️ Classification & Grouping - Property groups and external systems
    🌍 Geographic & Regulatory - Regional applicability and compliance
    📋 System Information - Audit trail and metadata
    """
    
    # Group selection with Select2
    groups = forms.ModelMultipleChoiceField(
        queryset=PropertyGroup.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'select2-multiple',
            'data-placeholder': 'Select groups...'
        }),
        required=False,
        help_text="PA006 - Property groups this property belongs to"
    )
    
    # Physical quantity selection
    physical_quantity = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.Select(attrs={
            'class': 'select2',
            'data-placeholder': 'Select physical quantity...'
        }),
        required=False,
        help_text="PA008 - Physical quantity this property measures (Length, Mass, Temperature, etc.)"
    )
    
    # Version and revision tracking
    version_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 1.0, 2.1, 3.0-beta'
        }),
        required=False,
        help_text="Version number for change tracking and compatibility"
    )
    
    revision_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Rev A, R01, 1.2.3'
        }),
        required=False,
        help_text="Revision number for detailed change management"
    )
    
    # Authority and registration
    registration_authority = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., ISO, EN, ASTM, buildingSMART'
        }),
        required=False,
        help_text="Organization or authority that registered/defined this property"
    )
    
    registration_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        help_text="Date when this property was officially registered or published"
    )
    
    # Language and localization
    creators_language = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., en-US, de-DE, fr-FR'
        }),
        initial='en-EN',
        help_text="Language code of the property creator (affects default language selection)"
    )
    
    # Documentation and metadata
    deprecation_explanation = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Explain why this property was deprecated and what to use instead'
        }),
        required=False,
        help_text="Explanation for deprecation (required when status is 'deprecated')"
    )
    
    # Extended attributes for custom PA codes
    extended_attributes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control json-editor',
            'rows': 4,
            'placeholder': '{"PA043": "Custom attribute", "PA044": "Another attribute"}'
        }),
        required=False,
        help_text="JSON field for storing additional PA codes and custom attributes"
    )
    
    # Generic metadata
    metadata = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control json-editor',
            'rows': 4,
            'placeholder': '{"source": "Standard XYZ", "calculation": "L*W*H", "precision": "±0.1%"}'
        }),
        required=False,
        help_text="JSON field for flexible metadata storage (calculation methods, sources, etc.)"
    )
    
    class Meta:
        model = Property
        fields = [
            # 🏛️ Core identification (PA001-PA003)
            'dictionary', 
            'version_number',
            'revision_number',
            
            # ⚙️ Technical specification (PA004-PA010)  
            'data_type', 
            'unit_of_measurement', 
            'value_domain',
            'physical_quantity',
            
            # 🏷️ Classification (PA011-PA015)
            'classification_system', 
            'classification_reference',
            
            # 📋 Lifecycle & Authority (PA016-PA020)
            'status', 
            'registration_authority',
            'registration_date',
            
            # 🌍 Geographic & Localization (PA021-PA025)
            'country_of_origin', 
            'countries_of_use',
            'creators_language',
            
            # 📖 Documentation & Metadata
            'deprecation_explanation',
            'extended_attributes',
            'metadata'
        ]
        
        widgets = {
            # Core fields with Select2
            'dictionary': forms.Select(attrs={
                'class': 'select2',
                'data-placeholder': 'Select dictionary...'
            }),
            'version_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1.0, 2.1, 3.0-beta'
            }),
            'revision_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Rev A, R01, 1.2.3'
            }),
            
            # Technical fields
            'data_type': forms.Select(attrs={
                'class': 'select2',
                'data-placeholder': 'Select data type...'
            }),
            'unit_of_measurement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., m, kg, °C, W/m²K'
            }),
            'value_domain': forms.Textarea(attrs={
                'class': 'form-control json-editor',
                'rows': 3,
                'placeholder': 'e.g., {"min": 0, "max": 100} or ["red", "green", "blue"]'
            }),
            'physical_quantity': forms.Select(attrs={
                'class': 'select2',
                'data-placeholder': 'Select physical quantity...'
            }),
            
            # Classification
            'classification_system': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., IFC, BSDD, OmniClass, UniFormat'
            }),
            'classification_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'External system reference ID or URI'
            }),
            
            # Status & Authority
            'status': forms.Select(attrs={
                'class': 'select2',
                'data-placeholder': 'Select status...'
            }),
            'registration_authority': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., ISO, EN, ASTM, buildingSMART'
            }),
            'registration_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            
            # Geographic & Localization
            'country_of_origin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ISO 3166-1 alpha-2 code, e.g., DE, US, GB'
            }),
            'countries_of_use': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'JSON array: ["DE", "AT", "CH"] or comma-separated: DE, AT, CH'
            }),
            'creators_language': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IETF language tag, e.g., en-US, de-DE, fr-FR'
            }),
            
            # Documentation
            'deprecation_explanation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Required when status is deprecated. Explain the reason and alternatives.'
            }),
            'extended_attributes': forms.Textarea(attrs={
                'class': 'form-control json-editor',
                'rows': 4,
                'placeholder': '{"tolerance": "±2%", "measurement_method": "ASTM D5334", "calibration": "annual"}'
            }),
            'metadata': forms.Textarea(attrs={
                'class': 'form-control json-editor',
                'rows': 4,
                'placeholder': '{"source": "Standard XYZ", "formula": "A*B/C", "assumptions": ["dry conditions", "20°C"]}'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Compact crispy helper (Bootstrap5)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_tag = True
        self.helper.form_class = "row g-2 align-items-start"   # small gutters
        self.helper.label_class = "form-label small"
        # use small controls to reduce vertical space
        self.helper.field_class = "form-control form-control-sm"
        self.helper.include_media = False

        # adjust column spacing in existing Layout — prefer 'mb-1' or 'mb-2'
        # Example convert Column("pa_code", css_class="col-md-6") -> css_class="col-md-6 mb-1"
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] += ' mb-1'
        
        # Disable system fields
        for fld in ('created_by', 'updated_by', 'created_at', 'updated_at'):
            if fld in self.fields:
                self.fields[fld].required = False
                self.fields[fld].disabled = True
        
        # Set up group queryset
        if self.instance and self.instance.pk and hasattr(self.instance, 'dictionary'):
            try:
                self.fields['groups'].queryset = PropertyGroup.objects.filter(
                    dictionary=self.instance.dictionary
                )
            except Exception:
                self.fields['groups'].queryset = PropertyGroup.objects.all()
        else:
            default_dict = PropertyDictionary.objects.filter(is_default=True).first()
            if default_dict:
                self.fields['groups'].queryset = PropertyGroup.objects.filter(
                    dictionary=default_dict
                )
            else:
                self.fields['groups'].queryset = PropertyGroup.objects.all()
        
        # Set up physical quantity queryset
        self.fields['physical_quantity'].queryset = PhysicalQuantity.objects.all()
        
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
        
        # Add comprehensive help text with PA codes to all fields
        field_help_texts = {
            # Core Information (PA001-PA003)
            'dictionary': 'PA001 - The dictionary this property belongs to. Dictionaries organize related properties by domain or standard.',
            'version_number': 'PA002 - Version number for tracking property definition changes (e.g., 1.0, 2.1, 3.0-beta)',
            'revision_number': 'PA003 - Revision identifier for detailed change management (e.g., Rev A, R01, 1.2.3)',
            
            # Technical Specification (PA004-PA010)
            'data_type': 'PA004 - The data type of this property (String, Integer, Real, Boolean, Complex)',
            'unit_of_measurement': 'PA005 - Unit of measurement for numeric properties (m, kg, °C, W/m²K, etc.)',
            'groups': 'PA006 - Property groups this property belongs to for logical organization',
            'value_domain': 'PA007 - Permitted value range, enumeration, or constraints (JSON format)',
            'physical_quantity': 'PA008 - Physical quantity this property measures (Length, Mass, Temperature, etc.)',
            
            # Classification (PA011-PA015)
            'classification_system': 'PA011 - External classification system (IFC, BSDD, OmniClass, UniFormat)',
            'classification_reference': 'PA012 - Reference ID or URI in the external classification system',
            
            # Status & Authority (PA016-PA020)
            'status': 'PA016 - Current lifecycle status (Draft, Candidate, Active, Deprecated, Inactive, Rejected)',
            'registration_authority': 'PA017 - Organization that registered/standardized this property (ISO, EN, ASTM, etc.)',
            'registration_date': 'PA018 - Official registration or publication date of this property',
            
            # Geographic & Localization (PA021-PA025)
            'country_of_origin': 'PA021 - ISO 3166-1 alpha-2 country code where this property originated',
            'countries_of_use': 'PA022 - Countries/regions where this property is used (JSON array or comma-separated)',
            'creators_language': 'PA023 - IETF language tag of the property creator (affects UI defaults)',
            
            # Documentation & Metadata
            'deprecation_explanation': 'Required when status is "deprecated". Explain the reason and suggest alternatives.',
            'extended_attributes': 'JSON field for custom PA codes and extended attributes beyond the standard',
            'metadata': 'JSON field for flexible metadata (calculation methods, sources, assumptions, etc.)',
        }
        
        # Update field help texts
        for field_name, help_text in field_help_texts.items():
            if field_name in self.fields:
                self.fields[field_name].help_text = help_text
        
        # Mark required fields with visual indicators
        required_fields = ['dictionary', 'data_type', 'status']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
                if 'class' in self.fields[field_name].widget.attrs:
                    self.fields[field_name].widget.attrs['class'] += ' required-field'
                else:
                    self.fields[field_name].widget.attrs['class'] = 'required-field'
        
        # Add conditional requirements based on status
        if self.instance and self.instance.status == 'deprecated':
            self.fields['deprecation_explanation'].required = True
            if 'class' in self.fields['deprecation_explanation'].widget.attrs:
                self.fields['deprecation_explanation'].widget.attrs['class'] += ' required-field'
    
    def clean(self):
        """Validate form data with business rules."""
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        deprecation_explanation = cleaned_data.get('deprecation_explanation')
        
        # Require deprecation explanation when status is deprecated
        if status == 'deprecated' and not deprecation_explanation:
            raise forms.ValidationError({
                'deprecation_explanation': 'This field is required when status is "deprecated".'
            })
        
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
        
        # Validate value domain JSON if provided
        value_domain = cleaned_data.get('value_domain')
        if value_domain:
            try:
                import json
                json.loads(str(value_domain))
            except (json.JSONDecodeError, TypeError):
                raise forms.ValidationError({
                    'value_domain': 'Must be valid JSON format (e.g., {"min": 0, "max": 100} or ["option1", "option2"]).'
                })
        
        return cleaned_data
    
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
    
    
class CrispyJSONField(forms.CharField):
    """
    Lightweight wrapper so ModelForm.field_classes can map JSON model fields
    to a CharField that uses JSONEditorWidget and tolerates encoder kwargs.
    """
    def __init__(self, *args, **kwargs):
        # accept and drop extra kwargs Django's JSONField.formfield may pass
        kwargs.pop("encoder", None)
        kwargs.pop("decoder", None)
        kwargs.pop("max_length", None)
        kwargs.setdefault("required", False)
        # create widget instance without passing options here (some widget impls don't accept options kwarg)
        kwargs.setdefault("widget", JSONEditorWidget())
        # ensure initial is JSON string for widgets that expect text
        if kwargs.get("initial") is None:
            kwargs["initial"] = "{}"
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value is None:
            return ""
        return super().to_python(value)

class PropertyFormCrisp(ModelForm):
    class Meta:
        model = Property
        fields = "__all__"
        widgets = {
            "date_of_activation": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "date_of_version": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "date_of_revision": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "date_of_deactivation": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "date_of_deprecation": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "registration_date": forms.DateInput(attrs={"type": "date"}),

            # create widget instances without options here
            "countries_of_use": JSONEditorWidget(),
            "subdivisions_of_use": JSONEditorWidget(),
            "permissible_units": JSONEditorWidget(),
            "value_domain": JSONEditorWidget(),
            "external_identifiers": JSONEditorWidget(),
            "dimension": JSONEditorWidget(),
            "defining_names": JSONEditorWidget(),
            "defining_values": JSONEditorWidget(),
            "tolerance": JSONEditorWidget(),
            "digital_format": JSONEditorWidget(),
            "boundary_values": JSONEditorWidget(),
            "property_media": JSONEditorWidget(),
            "extended_attributes": JSONEditorWidget(),
            "metadata": JSONEditorWidget(),
        }

        # map model JSONFields to a CharField so crispy sees a normal BoundField
        field_classes = {
            "countries_of_use": CrispyJSONField,
            "subdivisions_of_use": CrispyJSONField,
            "permissible_units": CrispyJSONField,
            "value_domain": CrispyJSONField,
            "external_identifiers": CrispyJSONField,
            "dimension": CrispyJSONField,
            "defining_names": CrispyJSONField,
            "defining_values": CrispyJSONField,
            "tolerance": CrispyJSONField,
            "digital_format": CrispyJSONField,
            "boundary_values": CrispyJSONField,
            "property_media": CrispyJSONField,
            "extended_attributes": CrispyJSONField,
            "metadata": CrispyJSONField,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # per-field JSONEditor options (safe assign)
        json_options = {
            "countries_of_use": {"mode": "tree"},
            "subdivisions_of_use": {"mode": "tree"},
            "permissible_units": {"mode": "form"},
            "value_domain": {"mode": "form"},
            "external_identifiers": {"mode": "form"},
            "dimension": {"mode": "form"},
            "defining_names": {"mode": "tree"},
            "defining_values": {"mode": "form"},
            "tolerance": {"mode": "form"},
            "digital_format": {"mode": "form"},
            "boundary_values": {"mode": "form"},
            "property_media": {"mode": "tree"},
            "extended_attributes": {"mode": "code"},
            "metadata": {"mode": "code"},
        }

        for fname, opts in json_options.items():
            if fname not in self.fields:
                continue
            widget = self.fields[fname].widget
            # try the common attribute name first
            if hasattr(widget, "options"):
                try:
                    widget.options = opts
                except Exception:
                    widget.attrs.setdefault("data-jsoneditor-options", json.dumps(opts))
            else:
                # fall back to data attribute so client init JS can read it
                widget.attrs.setdefault("data-jsoneditor-options", json.dumps(opts))

        # Compact crispy helper (Bootstrap5)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_tag = True
        self.helper.form_class = "row g-2 align-items-start"   # small gutters
        self.helper.label_class = "form-label small"
        # use small controls to reduce vertical space
        self.helper.field_class = "form-control form-control-sm"
        self.helper.include_media = False
        self.helper.layout = Layout(
            
            Row(
                Column("pa_code", css_class="col-md-6 mb-1"),
                Column("status", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("version_number", css_class="col-md-4 mb-1"),
                Column("revision_number", css_class="col-md-4 mb-1"),
                Column("data_type", css_class="col-md-4 mb-1"),
            ),
            Row(
                Column("date_of_activation", css_class="col-md-3 mb-1"),
                Column("date_of_version", css_class="col-md-3 mb-1"),
                Column("date_of_revision", css_class="col-md-3 mb-1"),
                Column("date_of_deactivation", css_class="col-md-3 mb-1"),
            ),
            Row(
                Column("registration_authority", css_class="col-md-6 mb-1"),
                Column("registration_date", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("country_of_origin", css_class="col-md-6 mb-1"),
                Column("creators_language", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("physical_quantity", css_class="col-md-6 mb-1"),
                Column("unit_of_measurement", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("dictionary", css_class="col-md-6 mb-1"),
                Column("classification_system", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("replaced_properties", css_class="col-md-6 mb-1"),
                Column("parameter_properties", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("dynamic_property", css_class="col-md-6 mb-1"),
                Column("method_of_measurement", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("deprecation_explanation", css_class="col-md-12 mb-1"),
            ),
            Row(
                Column(HTML("<h4>JSON Fields</h4>"), css_class="col-md-12"),
            ),
            Row(
                Column("countries_of_use", css_class="col-md-6 mb-1"),
                Column("subdivisions_of_use", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("permissible_units", css_class="col-md-6 mb-1"),
                Column("value_domain", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("dimension", css_class="col-md-6 mb-1"),
                Column("defining_names", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("defining_values", css_class="col-md-6 mb-1"),
                Column("tolerance", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("digital_format", css_class="col-md-6 mb-1"),
                Column("boundary_values", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("property_media", css_class="col-md-6 mb-1"),
                Column("extended_attributes", css_class="col-md-6 mb-1"),
            ),
            Row(
                Column("metadata", css_class="col-md-12 mb-1"),
            ),
            Submit("submit", "Save", css_class="btn-sm btn-primary mt-2"),
        )