from django.apps import AppConfig


class SingerConfig(AppConfig):
    """
    App configuration for the singer application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'singer'
