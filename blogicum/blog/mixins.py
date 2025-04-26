"""Миксины для приложения blog."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse


class AuthorCheckMixin(UserPassesTestMixin):
    """Миксин для проверки авторства."""

    def test_func(self):
        """Проверяет, является ли пользователь автором."""
        return self.get_object().author == self.request.user

    def handle_no_permission(self):
        """Перенаправление на страницу поста при отсутствии прав."""
        return redirect(
            'blog:post_detail',
            post_id=self.get_object().pk
        )


class PostMixin(LoginRequiredMixin):
    """Миксин для работы с постами."""

    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

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