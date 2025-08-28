"""
Custom admin configuration.
"""

from django.contrib.admin import AdminSite
from accounts.views import CustomLoginView

class PropBenchAdminSite(AdminSite):
    """
    Custom admin site to use our custom login view.
    """
    login_template = 'accounts/login.html'
    
    def login(self, request, extra_context=None):
        """Use our custom login view for admin login."""
        return CustomLoginView.as_view(
            template_name=self.login_template,
            extra_context=extra_context,
        )(request)
