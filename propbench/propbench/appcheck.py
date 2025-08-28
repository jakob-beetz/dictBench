"""
This module provides a helper to check if Django apps are ready.
"""
from django.apps import apps

def is_ready():
    """
    Check if Django apps are ready.
    
    Returns:
        bool: True if apps are ready, False otherwise.
    """
    try:
        return apps.apps_ready
    except Exception:
        return False