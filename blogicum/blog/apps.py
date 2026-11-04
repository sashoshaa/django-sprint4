"""Конфигурация приложения blog."""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Настройки приложения «Блог»."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    verbose_name = 'Блог'
