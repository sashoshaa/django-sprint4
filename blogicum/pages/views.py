"""Статические страницы и обработчики ошибок."""

from django.shortcuts import render
from django.views.generic import TemplateView


class About(TemplateView):
    """Страница «О проекте»."""

    template_name = 'pages/about.html'


class Rules(TemplateView):
    """Страница «Наши правила»."""

    template_name = 'pages/rules.html'


def page_not_found(request, exception):
    """Показывает страницу ошибки 404."""
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    """Показывает страницу ошибки 500."""
    return render(request, 'pages/500.html', status=500)


def csrf_failure(request, reason=''):
    """Показывает страницу ошибки 403 CSRF."""
    return render(request, 'pages/403csrf.html', status=403)
