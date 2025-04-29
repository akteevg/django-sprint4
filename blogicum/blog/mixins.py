from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse

from .models import Comment, Post


class AuthorCheckMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Миксин для проверки авторства."""

    def test_func(self):
        """Проверяет, является ли пользователь автором."""
        return self.get_object().author == self.request.user


class PostMixin(LoginRequiredMixin):
    """Миксин для работы с постами."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def handle_no_permission(self):
        """Перенаправление на страницу публикации, если нет прав."""
        if not self.request.user.is_authenticated:
            # Родительский метод (редирект на логин).
            return super().handle_no_permission()
        # Для авторизованных, не авторов (редирект на публикацию).
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])

    def get_success_url(self):
        """Перенаправление в профиль после успешного действия."""
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )

    def get_context_data(self, **kwargs):
        """Добавляет форму в контекст."""
        context = super().get_context_data(**kwargs)
        # Создаем форму, передаем текущую публикацию при редактировании.
        form = self.get_form()
        if self.object:  # Если публикация существует.
            form.instance = self.object  # Связываем форму с публикацией.
        context['form'] = form
        return context


class CommentMixin:
    """Миксин для работы с комментариями."""

    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        """Перенаправление на страницу публикации после успешного действия."""
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )
