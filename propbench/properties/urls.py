from django.urls import path, include
from django.urls import path
from . import grid_views, views

app_name = 'properties'

urlpatterns = [
    # Complete CRUD URL patterns for properties
    path('', views.property_list, name='property_list'),
    path('create/', views.property_create, name='property_create'),
    path('<uuid:pk>/', views.property_detail, name='property_detail'),
    path('<uuid:pk>/edit/', views.property_edit, name='property_edit'),
    path('<uuid:pk>/delete/', views.property_delete, name='property_delete'),

    # Grid URLs - main grid functionality
    path('grid/', grid_views.PropertyGridView.as_view(), name='property_grid'),
    path('api/grid-data/', grid_views.property_grid_data, name='property_grid_data'),
    path('api/properties/', grid_views.create_property, name='api_create_property'),
    path('api/properties/<str:property_id>/', grid_views.update_property, name='api_update_property'),
    path('api/properties/<str:property_id>/delete/', grid_views.delete_property, name='api_delete_property'),
    path('api/properties/bulk-edit/', grid_views.bulk_edit_properties, name='api_bulk_edit'),
    path('api/properties/<str:property_id>/versions/', grid_views.get_property_versions, name='api_property_versions'),
    path('api/units/search/', grid_views.search_units, name='api_search_units'),
    path('api/physical-quantities/search/', grid_views.search_physical_quantities, name='api_search_quantities'),
    path('api/classifications/search/', grid_views.search_classifications, name='api_search_classifications'),
    path('api/dictionaries/', views.get_dictionaries_api, name='api_dictionaries'),
]
