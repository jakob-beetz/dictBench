"""
API views for the dictionaries app.
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

# Import models and serializers inside the viewset to avoid early imports
class PropertyDictionaryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows property dictionaries to be viewed or edited.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        from .models import PropertyDictionary
        return PropertyDictionary.objects.all()
    
    def get_serializer_class(self):
        from .serializers import PropertyDictionarySerializer
        return PropertyDictionarySerializer
    
    def perform_create(self, serializer):
        """Ensure created_by and updated_by fields are set."""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Ensure updated_by field is set."""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set this dictionary as the default one."""
        from .models import PropertyDictionary
        
        dictionary = self.get_object()
        
        # Unset all other dictionaries
        PropertyDictionary.objects.exclude(pk=dictionary.pk).update(is_default=False)
        
        # Set this one as default
        dictionary.is_default = True
        dictionary.save()
        
        serializer = self.get_serializer(dictionary)
        return Response(serializer.data)
