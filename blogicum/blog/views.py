"""Представления блога: публикации, профиль и комментарии."""

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CommentForm, PostForm, ProfileForm
from .models import Category, Comment, Post

User = get_user_model()
PAGINATE_BY = 10


def published_posts():
    """Публикации, которые видны всем посетителям."""
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    ).select_related('author', 'category', 'location')


def with_comment_count(queryset):
    """Добавляет число комментариев и сортирует посты от новых к старым."""
    return queryset.annotate(
        comment_count=Count('comments'),
    ).order_by('-pub_date')


def post_is_visible(post, user):
    """Проверяет, может ли посетитель открыть публикацию."""
    if user.is_authenticated and post.author_id == user.pk:
        return True
    category = post.category
    return (
        post.is_published
        and post.pub_date <= timezone.now()
        and category is not None
        and category.is_published
    )


class PostAuthorMixin:
    """Пускает к изменению публикации только её автора."""

    def dispatch(self, request, *args, **kwargs):
        """Чужой запрос перенаправляет на страницу публикации."""
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        if post.author_id != request.user.pk:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)


class CommentAuthorMixin:
    """Пускает к изменению комментария только его автора."""

    def dispatch(self, request, *args, **kwargs):
        """Чужой запрос перенаправляет на страницу публикации."""
        comment = get_object_or_404(
            Comment,
            pk=kwargs['comment_id'],
            post_id=kwargs['post_id'],
        )
        if comment.author_id != request.user.pk:
            return redirect(
                'blog:post_detail',
                post_id=comment.post_id,
            )
        return super().dispatch(request, *args, **kwargs)


class IndexListView(ListView):
    """Главная страница с пагинацией публикаций."""

    template_name = 'blog/index.html'
    paginate_by = PAGINATE_BY

    def get_queryset(self):
        """Возвращает опубликованные посты с числом комментариев."""
        return with_comment_count(published_posts())


class CategoryListView(ListView):
    """Публикации одной опубликованной категории."""

    template_name = 'blog/category.html'
    paginate_by = PAGINATE_BY

    def get_category(self):
        """Возвращает опубликованную категорию из адреса."""
        if not hasattr(self, 'category'):
            self.category = get_object_or_404(
                Category,
                slug=self.kwargs['category_slug'],
                is_published=True,
            )
        return self.category

    def get_queryset(self):
        """Возвращает опубликованные посты выбранной категории."""
        posts = published_posts().filter(category=self.get_category())
        return with_comment_count(posts)

    def get_context_data(self, **kwargs):
        """Добавляет категорию в контекст шаблона."""
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        return context


class ProfileListView(ListView):
    """Страница пользователя и его публикации."""

    template_name = 'blog/profile.html'
    paginate_by = PAGINATE_BY

    def get_author(self):
        """Возвращает пользователя из адреса страницы."""
        if not hasattr(self, 'author'):
            self.author = get_object_or_404(
                User,
                username=self.kwargs['username'],
            )
        return self.author

    def get_queryset(self):
        """Автору показывает все его посты, остальным — только открытые."""
        author = self.get_author()
        if self.request.user == author:
            posts = Post.objects.filter(author=author).select_related(
                'author',
                'category',
                'location',
            )
        else:
            posts = published_posts().filter(author=author)
        return with_comment_count(posts)

    def get_context_data(self, **kwargs):
        """Добавляет профиль пользователя в контекст шаблона."""
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_author()
        return context


class PostDetailView(DetailView):
    """Отдельная страница публикации и её комментарии."""

    template_name = 'blog/detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'
    queryset = Post.objects.select_related(
        'author',
        'category',
        'location',
    )

    def get_object(self, queryset=None):
        """Скрывает отложенные и снятые с публикации посты."""
        post = super().get_object(queryset)
        if not post_is_visible(post, self.request.user):
            raise Http404
        return post

    def get_context_data(self, **kwargs):
        """Передаёт форму и список комментариев."""
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related(
            'author',
        ).order_by('created_at')
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание новой публикации."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        """Назначает автором текущего пользователя."""
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """После создания открывает страницу автора."""
        return reverse(
            'blog:profile',
            args=[self.request.user.username],
        )


class PostUpdateView(LoginRequiredMixin, PostAuthorMixin, UpdateView):
    """Редактирование публикации автором."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        """После правки открывает страницу публикации."""
        return reverse('blog:post_detail', args=[self.object.pk])


class PostDeleteView(LoginRequiredMixin, PostAuthorMixin, DeleteView):
    """Удаление публикации после подтверждения."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        """Передаёт форму с публикацией для страницы подтверждения."""
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        """После удаления открывает главную страницу."""
        return reverse('blog:index')


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Добавление комментария к публикации."""

    form_class = CommentForm
    template_name = 'blog/detail.html'

    def dispatch(self, request, *args, **kwargs):
        """Проверяет, что публикация для комментария существует."""
        self.post_object = get_object_or_404(
            Post,
            pk=kwargs['post_id'],
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Сохраняет комментарий от текущего пользователя."""
        form.instance.author = self.request.user
        form.instance.post = self.post_object
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Показывает публикацию, если форма заполнена с ошибкой."""
        context = super().get_context_data(**kwargs)
        context['post'] = self.post_object
        context['comments'] = self.post_object.comments.select_related(
            'author',
        )
        return context

    def get_success_url(self):
        """После отправки возвращает на страницу публикации."""
        return reverse('blog:post_detail', args=[self.post_object.pk])


class CommentUpdateView(
    LoginRequiredMixin,
    CommentAuthorMixin,
    UpdateView,
):
    """Редактирование своего комментария."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    context_object_name = 'comment'

    def get_queryset(self):
        """Ограничивает комментарий указанной публикацией."""
        return Comment.objects.filter(post_id=self.kwargs['post_id'])

    def get_success_url(self):
        """После правки возвращает на страницу публикации."""
        return reverse('blog:post_detail', args=[self.object.post_id])


class CommentDeleteView(
    LoginRequiredMixin,
    CommentAuthorMixin,
    DeleteView,
):
    """Удаление своего комментария после подтверждения."""

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    context_object_name = 'comment'

    def get_queryset(self):
        """Ограничивает комментарий указанной публикацией."""
        return Comment.objects.filter(post_id=self.kwargs['post_id'])

    def get_success_url(self):
        """После удаления возвращает на страницу публикации."""
        return reverse('blog:post_detail', args=[self.object.post_id])


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование своего профиля."""

    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        """Редактируется только аккаунт текущего пользователя."""
        return self.request.user

    def get_success_url(self):
        """После сохранения открывает страницу профиля."""
        return reverse('blog:profile', args=[self.object.username])


class RegistrationView(CreateView):
    """Регистрация нового пользователя."""

    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')
