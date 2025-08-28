from rest_framework import serializers
from .models import PropertyDictionary


class PropertyDictionarySerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyDictionary model.
    """
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    updated_by_username = serializers.ReadOnlyField(source='updated_by.username')
    
    class Meta:
        model = PropertyDictionary
        fields = [
            'guid', 'name', 'description', 'registration_authority', 
            'version', 'status', 'is_default', 'extended_attributes', 
            'metadata', 'created_by', 'created_by_username', 'updated_by', 
            'updated_by_username', 'created_at', 'updated_at', 
            'date_of_activation', 'date_of_deprecation', 'date_of_deactivation'
        ]
        read_only_fields = [
            'guid', 'created_by', 'updated_by', 'created_at', 
            'updated_at', 'created_by_username', 'updated_by_username'
        ]
