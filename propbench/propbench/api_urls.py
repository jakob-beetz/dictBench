"""
API URLs configuration for the REST Framework.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# We'll import viewsets directly in the urlpatterns to avoid early imports
# DO NOT import models or viewsets at module level

# Create a router
router = DefaultRouter()

# Register our viewsets with it in a function to delay imports
def register_viewsets(router):
    # Import viewsets only when needed
    from dictionaries.api_views import PropertyDictionaryViewSet
    from properties.api_views import PropertyViewSet
    from groups.api_views import PropertyGroupViewSet
    
    router.register(r'dictionaries', PropertyDictionaryViewSet, basename='dictionary')
    router.register(r'properties', PropertyViewSet, basename='property')
    router.register(r'groups', PropertyGroupViewSet, basename='group')
    
    return router

urlpatterns = [
    path('', include(register_viewsets(router).urls)),
    path('api-auth/', include('rest_framework.urls')),
]
