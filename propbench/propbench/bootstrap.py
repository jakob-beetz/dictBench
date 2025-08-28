"""
Bootstrap module for properly initializing Django before imports.
This can help with scripts that need to access Django models outside of a request.
"""

import os
import sys
import django

def setup_django():
    """Set up Django environment for scripts or modules that need it."""
    # Set the default Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'propbench.settings')
    
    # Add flag to indicate we're initializing Django
    if 'DJANGO_SETTING_UP' not in os.environ:
        os.environ['DJANGO_SETTING_UP'] = 'true'
    
    # Initialize Django
    try:
        django.setup()
        return True
    except Exception as e:
        print(f"Error initializing Django: {e}")
        return False
    finally:
        # Remove the flag
        if 'DJANGO_SETTING_UP' in os.environ:
            del os.environ['DJANGO_SETTING_UP']
    
# If this file is run directly, set up Django
if __name__ == "__main__":
    if setup_django():
        print("Django initialized successfully.")
    else:
        print("Failed to initialize Django.")