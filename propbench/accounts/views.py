from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class CustomLoginView(LoginView):
    """
    Custom login view that adds additional session handling
    """
    
    def form_valid(self, form):
        """Process a valid form."""
        # Explicitly save the session before proceeding
        if hasattr(self.request, 'session'):
            self.request.session.save()
            
        # Log the login attempt
        logger.info(f"Login attempt for user: {form.get_user()}")
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Process an invalid form."""
        # Log the failed login attempt
        logger.warning(f"Failed login attempt for username: {form.cleaned_data.get('username', 'unknown')}")
        
        # Add a message for the user
        messages.error(self.request, "Invalid username or password. Please try again.")
        
        return super().form_invalid(form)
