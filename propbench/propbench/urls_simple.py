"""URL configuration for propbench project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # HTMX interface
    path('dictionaries/', include('dictionaries.htmx_urls')),
    
    # Simplified basic views
    path('properties/', include('properties.urls')),
    path('groups/', include('groups.urls')),
    
    # Redirect root to dictionaries list
    path('', RedirectView.as_view(url='/dictionaries/'), name='index'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
