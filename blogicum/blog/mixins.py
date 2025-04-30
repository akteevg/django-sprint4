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
        return redirect(
            'blog:post_detail',
            post_id=self.kwargs[self.pk_url_kwarg]
        )

    def get_success_url(self):
        """Перенаправление в профиль после успешного действия."""
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )

    def get_context_data(self, **kwargs):
        """Добавляет форму в контекст."""
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
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
