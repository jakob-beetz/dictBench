from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Check if we're running a management command
        import sys
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
            # Skip importing signals during migrations
            return
            
        # Import signals when Django is ready, not at module level
        import accounts.signals
