"""Формы публикаций, комментариев и профиля."""

from django.contrib.auth import get_user_model
from django import forms

from .models import Comment, Post

User = get_user_model()


class PostForm(forms.ModelForm):
    """Форма создания и редактирования публикации."""

    class Meta:
        """Поля публикации, которые заполняет автор."""

        model = Post
        fields = (
            'title',
            'text',
            'pub_date',
            'category',
            'location',
            'image',
        )
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'},
            ),
        }


class CommentForm(forms.ModelForm):
    """Форма комментария к публикации."""

    class Meta:
        """В форме комментария редактируется только текст."""

        model = Comment
        fields = ('text',)


class ProfileForm(forms.ModelForm):
    """Форма редактирования данных пользователя."""

    class Meta:
        """Поля профиля, доступные владельцу аккаунта."""

        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
