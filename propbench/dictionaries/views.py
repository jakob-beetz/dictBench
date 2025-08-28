from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import PropertyDictionary
from .serializers import PropertyDictionarySerializer


class PropertyDictionaryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for property dictionaries.
    """
    queryset = PropertyDictionary.objects.all()
    serializer_class = PropertyDictionarySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_default', 'registration_authority']
    search_fields = ['name', 'description', 'registration_authority']
    ordering_fields = ['name', 'status', 'created_at', 'updated_at']
    
    def perform_create(self, serializer):
        """
        Set the created_by and updated_by fields on create.
        """
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
    
    def perform_update(self, serializer):
        """
        Set the updated_by field on update.
        """
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Set the dictionary as the default one.
        """
        dictionary = self.get_object()
        dictionary.is_default = True
        dictionary.save()
        
        return Response({'status': 'Dictionary set as default'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """
        Get the default dictionary.
        """
        dictionary = PropertyDictionary.objects.filter(is_default=True).first()
        
        if dictionary:
            serializer = self.get_serializer(dictionary)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'No default dictionary found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
