from django.urls import path
from . import views

app_name = 'requests'

urlpatterns = [
    path('', views.change_request_list, name='change_request_list'),
    path('create/', views.change_request_create, name='change_request_create'),
    path('<uuid:pk>/', views.change_request_detail, name='change_request_detail'),
    path('<uuid:pk>/review/', views.change_request_review, name='change_request_review'),
    path('<uuid:pk>/implement/', views.change_request_implement, name='change_request_implement'),
]
