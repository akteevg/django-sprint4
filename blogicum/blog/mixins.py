from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.db.models import Q
from django.utils.timezone import now
from django.views.generic import View


class AuthorCheckMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Миксин для проверки авторства."""

    def test_func(self):
        """Проверяет, является ли пользователь автором."""
        return self.get_object().author == self.request.user

    def handle_no_permission(self):
        """Перенаправление при отсутствии прав."""
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        if hasattr(self.get_object(), 'post'):
            return redirect(
                'blog:post_detail',
                post_id=self.get_object().post.pk
            )
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


class PostVisibilityMixin(View):
    """Миксин для проверки видимости постов."""

    def __init__(self, request=None):
        super().__init__()
        self.request = request

    def get_visible_posts(self):
        """Возвращает queryset с учетом видимости постов."""
        if self.request and self.request.user.is_authenticated:
            return Q(
                is_published=True,
                pub_date__lte=now(),
                category__is_published=True
            ) | Q(author=self.request.user)
        return Q(
            is_published=True,
            pub_date__lte=now(),
            category__is_published=True
        )


class CommentMixin:
    """Миксин для работы с комментариями."""

    template_name = 'blog/comment.html'

    def get_success_url(self):
        """Перенаправление на страницу публикации после успешного действия."""
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )
