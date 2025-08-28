from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin for the User model.
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'organization', 'job_title')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_expert', 'groups', 'user_permissions'),
        }),
        (_('Preferences'), {'fields': ('preferred_language',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'last_active')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'organization', 'is_staff', 'is_expert')
    list_filter = ('is_staff', 'is_superuser', 'is_expert', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'organization')
    readonly_fields = ('last_login', 'date_joined', 'last_active')
