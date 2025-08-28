from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div
from .models import PropertyDictionary


class PropertyDictionaryForm(forms.ModelForm):
    """
    Form for creating and updating property dictionaries.
    """
    class Meta:
        model = PropertyDictionary
        fields = ['name', 'description', 'registration_authority', 'version', 'status', 'is_default']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_id = 'dictionary-form'
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-10'
        
        self.helper.layout = Layout(
            Field('name', css_class='form-control', autocomplete='off'),
            Field('description', css_class='form-control'),
            Row(
                Column(Field('registration_authority', css_class='form-control'), css_class='col-md-6'),
                Column(Field('version', css_class='form-control'), css_class='col-md-6'),
            ),
            Row(
                Column(Field('status', css_class='form-select'), css_class='col-md-6'),
                Column(Field('is_default', css_class='form-check-input'), css_class='col-md-6'),
            ),
            Div(
                Submit('submit', 'Save', css_class='btn btn-primary me-2'),
                HTML('<a href="{% url "dictionaries:dictionary_list" %}" class="btn btn-secondary">Cancel</a>'),
                css_class='d-flex justify-content-end mt-3'
            )
        )
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            if not instance.pk:  # New dictionary
                instance.created_by = self.user
            
            instance.updated_by = self.user
            
        if commit:
            instance.save()
            self.save_m2m()
            
        return instance
