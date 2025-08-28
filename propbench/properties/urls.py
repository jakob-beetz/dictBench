from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    # Complete CRUD URL patterns for properties
    path('', views.property_list, name='property_list'),
    path('create/', views.property_create, name='property_create'),
    path('<uuid:pk>/', views.property_detail, name='property_detail'),
    path('<uuid:pk>/edit/', views.property_edit, name='property_edit'),
    path('<uuid:pk>/delete/', views.property_delete, name='property_delete'),
]
