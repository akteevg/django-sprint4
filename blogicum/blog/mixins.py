from django import forms
from django.conf import settings
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from typing import Optional, Type

from .models import Comment, Post


class AuthorCheckMixin(UserPassesTestMixin):
    """Миксин для проверки авторства."""

    def test_func(self):
        obj = self.get_object()
        if not obj:
            # Для CreateView (создание) разрешено всем авторизованным.
            return self.request.user.is_authenticated
        return obj.author == self.request.user if obj else False
    
    def handle_no_permission(self):
        """Делегируем обработку к AuthorRedirectMixin."""
        return super().handle_no_permission()


class AuthorRedirectMixin(AccessMixin):
    """Миксин для перенаправления при отсутствии прав."""

    def handle_no_permission(self):
        """Обрабатываем всех пользователей, не прошедших проверку."""
        if not self.request.user.is_authenticated:
            # Неавторизованные — перенаправляем на страницу входа
            return redirect_to_login(self.request.get_full_path())
        # Авторизованные не авторы — перенаправляем на страницу публикации
        try:
            obj = self.get_object()
            post_id = obj.post_id if isinstance(obj, Comment) else obj.pk
        except (AttributeError, Comment.DoesNotExist, Post.DoesNotExist):
            post_id = self.kwargs.get('post_id', 1)
        return redirect('blog:post_detail', post_id=post_id)


class PostMixin(AuthorCheckMixin, AuthorRedirectMixin):
    """Миксин для работы с публикациями."""

    # form_class: Optional[Type[forms.ModelForm]] = None  # Аннотация типа.
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'


class CommentMixin(AuthorRedirectMixin):
    """Миксин для комментариев."""

    model = Comment
    pk_url_kwarg = 'comment_id'
