from django.apps import AppConfig


class DictionariesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dictionaries'
    
    def ready(self):
        import dictionaries.signals
