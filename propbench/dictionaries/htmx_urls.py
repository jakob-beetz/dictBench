from django.urls import path
from . import htmx_views

app_name = 'dictionaries'

urlpatterns = [
    path('', htmx_views.DictionaryListView.as_view(), name='dictionary_list'),
    path('create/', htmx_views.DictionaryCreateView.as_view(), name='dictionary_create'),
    path('<uuid:pk>/', htmx_views.DictionaryDetailView.as_view(), name='dictionary_detail'),
    path('<uuid:pk>/edit/', htmx_views.DictionaryUpdateView.as_view(), name='dictionary_edit'),
    path('<uuid:pk>/delete/', htmx_views.DictionaryDeleteView.as_view(), name='dictionary_delete'),
]
