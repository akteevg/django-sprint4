from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

from .constants import POSTS_LIMIT_ON_PAGE, COMMENTS_LIMIT_ON_PAGE
from .forms import CommentForm, PostForm, ProfileEditForm
from .mixins import (AuthorCheckMixin,
                     PostMixin,
                     CommentMixin)
from .models import Category, Post
from .services import paginate_posts


class SignUpView(CreateView):
    """Класс для формы регистрации пользователя."""

    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


class ProfileView(ListView):
    """Класс отображения профиля."""

    template_name = 'blog/profile.html'
    context_object_name = 'posts'
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
        queryset = author.posts.with_comments_count()
        if self.request.user != author:
            queryset = queryset.filter_posts_by_publication()
        return queryset

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

    form_class = PostForm

    def get_success_url(self):
        """Перенаправление на страницу публикации после редактирования."""
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs[self.pk_url_kwarg]}
        )


class PostDeleteView(AuthorCheckMixin, PostMixin, DeleteView):
    """Удаление существующей публикации (только для автора)."""

    pass


def index(request):
    """Функция для главной страницы."""
    posts = (Post.objects.filter_posts_by_publication()
             .with_comments_count())
    page_obj = paginate_posts(posts, request.GET.get('page'))
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def category_posts(request, category_slug):
    """Функция для страницы категории."""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = (category
             .posts.filter_posts_by_publication()
             .with_comments_count())
    page_obj = paginate_posts(posts, request.GET.get('page'))

    return render(
        request, 'blog/category.html', {
            'category': category,
            'page_obj': page_obj
        }
    )


def post_detail(request, post_id):
    """Функция для страницы публикации."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'category', 'location')
            .with_comments_count(),
        pk=post_id)
    if not (request.user.is_authenticated and post.author == request.user):
        post = get_object_or_404(
            Post.objects.select_related('author', 'category', 'location')
                .filter_posts_by_publication()
                .with_comments_count(),
            pk=post_id
        )

    comments = post.comments.select_related('author')
    page_obj = paginate_posts(
        comments,
        request.GET.get('page'),
        COMMENTS_LIMIT_ON_PAGE
    )

    return render(request, 'blog/detail.html', {
        'post': post,
        'page_obj': page_obj,
        'form': CommentForm()
    })


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):
    """Создание комментария к публикации."""

    form_class = CommentForm

    def form_valid(self, form):
        """Присваиваем комментарию публикацию и автора."""
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)


class CommentEditView(AuthorCheckMixin, CommentMixin, UpdateView):
    """Редактирование комментария к публикации."""

    form_class = CommentForm


class CommentDeleteView(AuthorCheckMixin, CommentMixin, DeleteView):
    """Удаление комментария к публикации."""

    pass
