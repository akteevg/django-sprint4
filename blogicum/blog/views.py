from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

from pages.views import csrf_failure

from .constants import POSTS_LIMIT_ON_PAGE, COMMENTS_LIMIT_ON_PAGE
from .forms import CommentForm, PostForm, ProfileEditForm
from .mixins import AuthorCheckMixin, PostMixin, PostVisibilityMixin, CommentMixin
from .models import Category, Comment, Post
from .services import paginate_posts


class SignUpView(CreateView):
    """Класс для формы регистрации пользователя."""

    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


class ProfileView(PostVisibilityMixin, ListView):
    """Класс отображения профиля."""

    template_name = 'blog/profile.html'
    context_object_name = 'page_obj'
    paginate_by = POSTS_LIMIT_ON_PAGE

    def get_author(self):
        """Получает автора по username из URL."""
        return get_object_or_404(
            User,
            username=self.kwargs['username']
        )

    def get_queryset(self):
        """Возвращает посты автора с аннотацией количества комментариев."""
        author = self.get_author()
        return author.posts.filter(
            self.get_visible_posts()
        ).with_comments_count().order_by('-pub_date')

    def get_context_data(self, **kwargs):
        """Добавляет автора в контекст."""
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_author()
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Класс редактирования профиля."""

    form_class = ProfileEditForm
    template_name = 'blog/user.html'

    def get_success_url(self):
        """Перенаправление в профиль после редактирования."""
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )

    def get_object(self, queryset=None):
        """Возвращает текущего пользователя для редактирования."""
        return self.request.user


class PostCreateView(PostMixin, CreateView):
    """Создание новой публикации (только для авторизованных)."""

    form_class = PostForm

    def form_valid(self, form):
        """Авторство присваиваем текущему пользователю."""
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostEditView(AuthorCheckMixin, PostMixin, UpdateView):
    """Редактирование существующей публикации (только для автора)."""

    model = Post
    form_class = PostForm

    def get_success_url(self):
        """Перенаправление на страницу публикации после редактирования."""
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk}
        )


class PostDeleteView(AuthorCheckMixin, PostMixin, DeleteView):
    """Удаление существующей публикации (только для автора)."""
    
    model = Post
    template_name = 'blog/create.html'


def index(request):
    """Функция для главной страницы."""
    posts = Post.objects.published_with_comments().order_by('-pub_date')
    _, page_obj = paginate_posts(posts, request.GET.get('page'))
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def category_posts(request, category_slug):
    """Функция для страницы категории."""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = category.posts.published_with_comments().order_by('-pub_date')
    _, page_obj = paginate_posts(posts, request.GET.get('page'))

    return render(
        request, 'blog/category.html', {
            'category': category,
            'page_obj': page_obj
        }
    )


def post_detail(request, post_id):
    """Функция для страницы публикации."""
    post = get_object_or_404(
        Post.objects.select_related(
            'author',
            'category',
            'location'
        ).with_comments_count().order_by('-pub_date'),
        PostVisibilityMixin(request).get_visible_posts(),
        pk=post_id
    )

    comments = post.comments.select_related('author').order_by('created_at')
    _, page_obj = paginate_posts(
        comments,
        request.GET.get('page'),
        COMMENTS_LIMIT_ON_PAGE
    )

    return render(request, 'blog/detail.html', {
        'post': post,
        'page_obj': page_obj,
        'form': CommentForm()
    })


class CommentCreateView(CommentMixin, CreateView):
    """Создание комментария к публикации."""
    
    def form_valid(self, form):
        """Присваиваем комментарию публикацию и автора."""
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)


class CommentEditView(AuthorCheckMixin, CommentMixin, UpdateView):
    """Редактирование комментария к публикации."""
    
    model = Comment
    pk_url_kwarg = 'comment_id'


@login_required  # Только для залогиненых.
def delete_comment(request, post_id, comment_id):
    """Функция удаления комментария к публикации."""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)

    if comment.author != request.user:  # Проверка авторства.
        return csrf_failure(
            request,
            reason="Удаление чужого комментария запрещено"
        )

    if request.method == 'POST':  # Удаление только через POST-запрос.
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    # Страница подтверждения через GET-запрос.
    return render(request, 'blog/comment.html', {'comment': comment})
