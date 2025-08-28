"""
Serializers for the groups app.
"""
from rest_framework import serializers

# Initialize Django first if needed
from propbench.bootstrap import setup_django
setup_django()

# Now we can safely import models
from .models import PropertyGroup, PropertyGroupMembership, GroupName, GroupDefinition


class GroupNameSerializer(serializers.ModelSerializer):
    """
    Serializer for GroupName model.
    """
    class Meta:
        model = GroupName
        fields = ['id', 'name', 'language']


class GroupDefinitionSerializer(serializers.ModelSerializer):
    """
    Serializer for GroupDefinition model.
    """
    class Meta:
        model = GroupDefinition
        fields = ['id', 'definition', 'language']


class PropertyGroupMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyGroupMembership model.
    """
    property_guid = serializers.UUIDField(source='property.guid', read_only=True)
    property_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyGroupMembership
        fields = ['id', 'property', 'property_guid', 'property_name', 'order', 'is_required', 'metadata']
    
    def get_property_name(self, obj):
        """
        Get the English name of the property or the first available name.
        """
        try:
            # Try to get English name first
            name = obj.property.names.filter(language='en-EN').first()
            if not name:
                name = obj.property.names.first()
            return name.name if name else f"Property {obj.property.guid}"
        except Exception:
            return f"Property {obj.property.guid}"


class PropertyGroupListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for PropertyGroup model used in list views.
    """
    names = GroupNameSerializer(many=True, read_only=True)
    dictionary_name = serializers.ReadOnlyField(source='dictionary.name')
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    property_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyGroup
        fields = [
            'guid', 'names', 'type', 'dictionary', 'dictionary_name', 
            'parent_group', 'created_by_username', 'property_count', 'created_at'
        ]
    
    def get_property_count(self, obj):
        """
        Get the number of properties in this group.
        """
        return obj.properties.count()


class PropertyGroupDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for PropertyGroup model.
    """
    names = GroupNameSerializer(many=True)
    definitions = GroupDefinitionSerializer(many=True, required=False)
    dictionary_name = serializers.ReadOnlyField(source='dictionary.name')
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    updated_by_username = serializers.ReadOnlyField(source='updated_by.username')
    memberships = PropertyGroupMembershipSerializer(source='propertygroupmembership_set', many=True, read_only=True)
    
    class Meta:
        model = PropertyGroup
        fields = [
            'guid', 'names', 'definitions', 'description', 'type',
            'parent_group', 'dictionary', 'dictionary_name', 'extended_attributes',
            'metadata', 'created_by', 'created_by_username', 'updated_by',
            'updated_by_username', 'created_at', 'updated_at', 'memberships'
        ]
        read_only_fields = [
            'guid', 'created_by', 'updated_by', 'created_at', 'updated_at',
            'created_by_username', 'updated_by_username'
        ]
    
    def create(self, validated_data):
        """
        Create a new property group with related names and definitions.
        """
        names_data = validated_data.pop('names')
        definitions_data = validated_data.pop('definitions', [])
        
        # Create the property group
        group = PropertyGroup.objects.create(**validated_data)
        
        # Create the names
        for name_data in names_data:
            GroupName.objects.create(group=group, **name_data)
        
        # Create the definitions
        for definition_data in definitions_data:
            GroupDefinition.objects.create(group=group, **definition_data)
        
        return group
    
    def update(self, instance, validated_data):
        """
        Update a property group with related names and definitions.
        """
        names_data = validated_data.pop('names', None)
        definitions_data = validated_data.pop('definitions', None)
        
        # Update the property group fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update names if provided
        if names_data is not None:
            # Delete existing names
            instance.names.all().delete()
            
            # Create new names
            for name_data in names_data:
                GroupName.objects.create(group=instance, **name_data)
        
        # Update definitions if provided
        if definitions_data is not None:
            # Delete existing definitions
            instance.definitions.all().delete()
            
            # Create new definitions
            for definition_data in definitions_data:
                GroupDefinition.objects.create(group=instance, **definition_data)
        
        return instance


class AddPropertiesToGroupSerializer(serializers.Serializer):
    """
    Serializer for adding properties to a group.
    """
    properties = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        help_text="List of property GUIDs to add to the group."
    )
    is_required = serializers.BooleanField(
        default=False,
        help_text="Whether these properties are required in the group."
    )


class PropertyGroupHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for property group history view.
    """
    names = GroupNameSerializer(many=True, read_only=True)
    audit_logs = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyGroup
        fields = [
            'guid', 'names', 'type', 'created_at', 'updated_at', 'audit_logs'
        ]
    
    def get_audit_logs(self, obj):
        """
        Get all audit logs for this property group.
        """
        from audit.serializers import AuditSerializer
        
        # Import here to avoid circular imports
        from audit.models import Audit
        
        audits = Audit.objects.filter(
            entity_type='PropertyGroup',
            entity_id=str(obj.guid)
        ).order_by('-timestamp')
        
        return AuditSerializer(audits, many=True).data


class PropertyGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyGroup model.
    """
    created_by = serializers.ReadOnlyField(source='created_by.username')
    updated_by = serializers.ReadOnlyField(source='updated_by.username')
    dictionary_name = serializers.ReadOnlyField(source='dictionary.name')
    parent_group_name = serializers.ReadOnlyField(source='parent_group.name', allow_null=True)
    
    # Additional field for API to set dictionary by ID
    dictionary_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        from .models import PropertyGroup
        model = PropertyGroup
        fields = [
            'guid', 'name', 'description', 'type', 'parent_group', 
            'dictionary', 'dictionary_name', 'parent_group_name', 
            'dictionary_id', 'created_by', 'created_at', 
            'updated_by', 'updated_at', 'extended_attributes'
        ]
        read_only_fields = ['guid', 'created_by', 'created_at', 'updated_by', 'updated_at']
