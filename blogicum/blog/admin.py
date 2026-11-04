"""Регистрация моделей блога в админке."""

from django.contrib import admin

from .models import Category, Comment, Location, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Настройки категории в админке."""

    list_display = ('title', 'is_published', 'created_at')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Настройки местоположения в админке."""

    list_display = ('name', 'is_published', 'created_at')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Настройки публикации в админке."""

    list_display = (
        'title',
        'pub_date',
        'author',
        'category',
        'location',
        'is_published',
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Настройки комментария в админке."""

    list_display = ('text', 'post', 'author', 'created_at')
