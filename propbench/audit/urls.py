from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'audit'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'', views.AuditViewSet, basename='audit')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('', views.audit_list, name='audit_list'),
    path('<uuid:pk>/', views.audit_detail, name='audit_detail'),
    path('entity/<str:entity_type>/<str:entity_id>/', views.entity_audit_history, name='entity_audit_history'),
]
