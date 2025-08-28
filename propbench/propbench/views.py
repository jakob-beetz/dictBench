"""
Main project views.
"""
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin


class IndexView(LoginRequiredMixin, RedirectView):
    """
    Redirect to the dictionary list view.
    """
    pattern_name = 'dictionary_list'
    
class AboutView(TemplateView):
    """
    Display information about the application.
    """
    template_name = 'about.html'
