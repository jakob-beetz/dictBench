from django.urls import path, include
from . import grid_views

# Grid API URLs
grid_urlpatterns = [
    # Main grid view
    path('grid/', grid_views.PropertyGridView.as_view(), name='property_grid'),
    
    # Grid data API
    path('api/grid-data/', grid_views.property_grid_data, name='property_grid_data'),
    
    # CRUD operations
    path('api/create/', grid_views.create_property, name='api_create_property'),
    path('api/<str:property_id>/update/', grid_views.update_property, name='api_update_property'),
    path('api/<str:property_id>/delete/', grid_views.delete_property, name='api_delete_property'),
    
    # Bulk operations
    path('api/bulk-edit/', grid_views.bulk_edit_properties, name='api_bulk_edit'),
    
    # Versioning
    path('api/<str:property_id>/versions/', grid_views.get_property_versions, name='api_property_versions'),
    
    # Fuzzy search endpoints
    path('api/search/units/', grid_views.search_units, name='api_search_units'),
    path('api/search/quantities/', grid_views.search_physical_quantities, name='api_search_quantities'),
    path('api/search/classifications/', grid_views.search_classifications, name='api_search_classifications'),
]

# Include these in your main properties/urls.py
app_name = 'properties'
urlpatterns = [
    # Your existing URL patterns...
    
    # Grid URLs
    path('', include(grid_urlpatterns)),
]