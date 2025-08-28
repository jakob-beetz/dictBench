"""
API views for the properties app.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


# Import models inside the viewset to avoid early imports
class PropertyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows properties to be viewed or edited.
    An active dictionary must be set.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers import PropertySerializer
        return PropertySerializer
    
    def get_queryset(self):
        """
        Filter properties by dictionary if provided in query params.
        """
        from .models import Property
        
        queryset = Property.objects.all()
        dictionary_id = self.request.query_params.get('dictionary_id', None)
        
        if dictionary_id:
            queryset = queryset.filter(dictionary__guid=dictionary_id)
            
        return queryset
    
    def perform_create(self, serializer):
        """
        Create a new property.
        Ensure created_by and updated_by fields are set.
        Require a dictionary to be specified.
        """
        from dictionaries.models import PropertyDictionary
        from .models import PropertyName, PropertyDefinition
        
        dictionary_id = self.request.data.get('dictionary_id')
        if not dictionary_id:
            # Try to use the default dictionary
            default_dict = PropertyDictionary.objects.filter(is_default=True).first()
            if default_dict:
                dictionary = default_dict
            else:
                return Response(
                    {"error": "No dictionary specified and no default dictionary found."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            dictionary = get_object_or_404(PropertyDictionary, guid=dictionary_id)
        
        property_instance = serializer.save(
            dictionary=dictionary,
            created_by=self.request.user,
            updated_by=self.request.user
        )
        
        # Handle names and definitions if provided
        names_data = self.request.data.get('names', [])
        for name_data in names_data:
            PropertyName.objects.create(
                property=property_instance,
                name=name_data.get('name'),
                language=name_data.get('language', 'en')
            )
            
        definitions_data = self.request.data.get('definitions', [])
        for definition_data in definitions_data:
            PropertyDefinition.objects.create(
                property=property_instance,
                definition=definition_data.get('definition'),
                language=definition_data.get('language', 'en')
            )
    
    def perform_update(self, serializer):
        """
        Update a property.
        Ensure updated_by field is set.
        """
        serializer.save(updated_by=self.request.user)
