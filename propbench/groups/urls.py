from django.urls import path
from . import views

app_name = 'groups'

urlpatterns = [
    # Complete CRUD URL patterns for groups
    path('', views.group_list, name='group_list'),
    path('create/', views.group_create, name='group_create'),
    path('<uuid:pk>/', views.group_detail, name='group_detail'),
    path('<uuid:pk>/edit/', views.group_edit, name='group_edit'),
    path('<uuid:pk>/delete/', views.group_delete, name='group_delete'),
]
