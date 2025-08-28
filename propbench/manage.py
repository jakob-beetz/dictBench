#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Set Django settings environment variable before any other imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'propbench.settings')

def main():
    """Run administrative tasks."""
    try:
        # Import and setup Django first
        import django
        django.setup()
        
        # Now that Django is set up, execute the command
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv)
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc


if __name__ == '__main__':
    main()