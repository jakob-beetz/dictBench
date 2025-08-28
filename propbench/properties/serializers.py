"""
Serializers for the properties app.
"""
from rest_framework import serializers

# Import models inside the serializer to avoid early imports
class PropertyNameSerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyName model.
    """
    class Meta:
        from .models import PropertyName
        model = PropertyName
        fields = ['id', 'name', 'language']


class PropertyDefinitionSerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyDefinition model.
    """
    class Meta:
        from .models import PropertyDefinition
        model = PropertyDefinition
        fields = ['id', 'definition', 'language']


class PropertySerializer(serializers.ModelSerializer):
    """
    Serializer for Property model.
    """
    created_by = serializers.ReadOnlyField(source='created_by.username')
    updated_by = serializers.ReadOnlyField(source='updated_by.username')
    dictionary_name = serializers.ReadOnlyField(source='dictionary.name')
    names = PropertyNameSerializer(many=True, read_only=True)
    definitions = PropertyDefinitionSerializer(many=True, read_only=True)
    
    # Additional field for API to set dictionary by ID
    dictionary_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        from .models import Property
        model = Property
        fields = [
            'guid', 'data_type', 'unit_of_measurement', 'value_domain',
            'classification_system', 'classification_reference', 'status',
            'country_of_origin', 'countries_of_use', 'dictionary', 
            'dictionary_name', 'dictionary_id', 'created_by', 'created_at',
            'updated_by', 'updated_at', 'extended_attributes', 'names', 
            'definitions'
        ]
        read_only_fields = ['guid', 'created_by', 'created_at', 'updated_by', 'updated_at']
