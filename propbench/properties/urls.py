from django.urls import path, include
from django.urls import path
from django.shortcuts import render
from . import grid_views, views
from .views import PropertyCreateView, LoadReplacedPropertiesView, LoadParameterPropertiesView, PropertyCompactDetailView
app_name = 'properties'

urlpatterns = [
    # Index route
    path('', views.index_view, name='index'),

    # Complete CRUD URL patterns for properties
    path('properties/', views.property_list, name='property_list'),
    path('properties/create/', views.property_create, name='property_create'),
    path('properties/<uuid:pk>/', views.property_detail, name='property_detail'),
    path('properties/<uuid:pk>/edit/', views.property_edit, name='property_edit'),
    path('properties/<uuid:pk>/delete/', views.property_delete, name='property_delete'),
    path('properties/<uuid:pk>/edit2/', views.property_edit2, name='property_edit2'),
    
    
    #new crispy forms
    path("properties/create_crisp/", PropertyCreateView.as_view(), name="property_create_crisp"),
    path("properties/load-replaced/", LoadReplacedPropertiesView.as_view(), name="load_replaced_properties"),
    path("properties/load-parameter/", LoadParameterPropertiesView.as_view(), name="load_parameter_properties"),
    # Grid URLs - main grid functionality
    path('properties/grid/', grid_views.PropertyGridView.as_view(), name='property_grid'),
    path('properties/api/grid-data/', grid_views.property_grid_data, name='property_grid_data'),
    path('properties/api/properties/', grid_views.create_property, name='api_create_property'),
    path('properties/api/properties/<str:property_id>/', grid_views.update_property, name='api_update_property'),
    path('properties/api/properties/<str:property_id>/delete/', grid_views.delete_property, name='api_delete_property'),
    path('properties/api/properties/bulk-edit/', grid_views.bulk_edit_properties, name='api_bulk_edit'),
    path('properties/api/properties/<str:property_id>/versions/', grid_views.get_property_versions, name='api_property_versions'),
    path('properties/api/units/search/', grid_views.search_units, name='api_search_units'),
    path('properties/api/physical-quantities/search/', grid_views.search_physical_quantities, name='api_search_quantities'),
    path('properties/api/classifications/search/', grid_views.search_classifications, name='api_search_classifications'),
    # path('properties/api/dictionaries/', views.get_dictionaries_api, name='api_dictionaries'),

    # Property versions page
    path('properties/property/<uuid:pk>/versions/', views.property_versions, name='property_versions'),
    path('properties/recent-changes/', views.recent_changes, name='recent_changes'),

    # External import view
    path('import/iso16757/', views.iso16757_import_view, name='iso16757_import'),
    
    path('<uuid:pk>/compact/', PropertyCompactDetailView.as_view(), name='property_compact_detail'),
    
    # API routes for library
    path('api/library/upload/', views.upload_library, name='library_upload_api'),
    path('api/library/items/', views.library_items_autocomplete, name='library_items_autocomplete'),
    path('api/library/items/options/', views.library_items_options, name='library_items_options'),
    path('libraries/upload/', views.upload_library_view, name='library_upload'),
    path('libraries/upload/success/', lambda r: render(r, 'properties/library_upload_success.html'), name='library_upload_success'),
]
