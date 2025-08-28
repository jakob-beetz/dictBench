"""URL configuration for propbench project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    # Temporarily commented out until those apps are properly set up
    # path('api/properties/', include('properties.urls')),
    # path('api/groups/', include('groups.urls')),
    # path('api/requests/', include('requests.urls')),
    # path('api/audit/', include('audit.urls')),
    # path('api/import-export/', include('import_export.urls')),
    # path('api/dictionaries/', include('dictionaries.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
