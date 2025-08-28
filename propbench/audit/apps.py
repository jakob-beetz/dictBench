from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'
    
    def ready(self):
        """
        Connect signals when app is ready.
        Skip connecting signals during migrations.
        """
        import sys
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
            # Don't connect signals during migrations
            return
            
        # Import and connect signals
        import audit.signals
