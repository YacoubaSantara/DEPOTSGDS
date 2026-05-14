from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'SGDS.users'
    verbose_name = 'Gestion des utilisateurs'

    def ready(self):
        from . import signals  # noqa: F401
