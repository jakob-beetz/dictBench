"""
Serializers for the dictionaries app.
"""
from rest_framework import serializers

# Import models inside the serializer to avoid early imports
class PropertyDictionarySerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyDictionary model.
    """
    created_by = serializers.ReadOnlyField(source='created_by.username')
    updated_by = serializers.ReadOnlyField(source='updated_by.username')
    
    class Meta:
        from .models import PropertyDictionary
        model = PropertyDictionary
        fields = [
            'guid', 'name', 'description', 'registration_authority', 
            'version', 'status', 'is_default', 'created_by', 
            'created_at', 'updated_by', 'updated_at'
        ]
        read_only_fields = ['guid', 'created_by', 'created_at', 'updated_by', 'updated_at']
