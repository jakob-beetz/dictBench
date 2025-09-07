"""URL configuration for propbench project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.conf import settings
from django.urls import include, path
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # API endpoints
    path('api/', include('propbench.api_urls')),
    
    # HTMX interface
    path('dictionaries/', include('dictionaries.htmx_urls', namespace='dictionaries')),
    
    # Basic views with proper namespacing
    path('properties/', include('properties.urls', namespace='properties')),
    path('properties/', include('properties.urls')),
    path('groups/', include('groups.urls', namespace='groups')),
    path('requests/', include('requests.urls', namespace='requests')),
    path('audit/', include('audit.urls', namespace='audit')),
    
    # Redirect root to dictionaries list
    path('', RedirectView.as_view(pattern_name='dictionaries:dictionary_list'), name='index'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
