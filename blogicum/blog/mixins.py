from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.views.generic import DeleteView
from django.shortcuts import redirect
from django.urls import reverse

from .models import Comment, Post


class AuthorCheckMixin(UserPassesTestMixin):
    """Миксин для проверки авторства."""

    def test_func(self):
        obj = self.get_object()
        if not obj:
            # Для CreateView (создание) разрешено всем авторизованным.
            return self.request.user.is_authenticated
        return obj.author == self.request.user if obj else False


class AuthorRedirectMixin(AccessMixin):
    """Миксин для перенаправления при отсутствии прав."""

    def handle_no_permission(self):
        """Обрабатываем всех пользователей, не прошедших проверку."""
        if not self.request.user.is_authenticated:
            # Неавторизованные — перенаправляем на страницу входа.
            return redirect_to_login(self.request.get_full_path())
        # Авторизованные не авторы — перенаправляем на страницу публикации.
        try:
            obj = self.get_object()
            post_id = obj.post_id if isinstance(obj, Comment) else obj.pk
        except (AttributeError, Comment.DoesNotExist, Post.DoesNotExist):
            post_id = self.kwargs.get('post_id', 1)
        return redirect('blog:post_detail', post_id=post_id)


class SuccessUrlMixin:
    """Миксин определет success_url для перенаправления."""

    def get_success_url(self):
        # Для удаления публикации: перенаправление в профиль.
        if isinstance(self, DeleteView) and self.model == Post:
            return reverse(
                'blog:profile',
                kwargs={'username': self.request.user.username}
            )

        # Для комментариев или если post_id передан в URL.
        if 'post_id' in self.kwargs:
            return reverse(
                'blog:post_detail', 
                kwargs={'post_id': self.kwargs['post_id']}
            )

        # Для создания/редактирования публикации: используем ID объекта.
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk}
        )


class PostMixin(AuthorCheckMixin, AuthorRedirectMixin):
    """Миксин для работы с публикациями."""

    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'


class CommentMixin(AuthorRedirectMixin):
    """Миксин для комментариев."""

    model = Comment
    pk_url_kwarg = 'comment_id'
