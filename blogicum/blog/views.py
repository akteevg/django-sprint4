from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

from .constants import POSTS_LIMIT_ON_PAGE, COMMENTS_LIMIT_ON_PAGE
from .forms import CommentForm, PostForm, ProfileEditForm
from .mixins import AuthorCheckMixin, CommentMixin, PostMixin, SuccessUrlMixin
from .models import Category, Comment, Post
from .services import get_paginated_page


class SignUpView(CreateView):
    """Класс для формы регистрации пользователя."""

    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


class ProfileView(ListView):
    """Класс отображения профиля."""

    model = Post
    template_name = 'blog/profile.html'
    context_object_name = 'posts'
    paginate_by = POSTS_LIMIT_ON_PAGE

    def _get_author(self):
        """Получаем автора по username из URL."""
        return get_object_or_404(
            User,
            username=self.kwargs['username']
        )

    def get_queryset(self):
        """Фильтруем посты текущего пользователя и добавляем аннотацию."""
        author = self._get_author()
        queryset = (
            author.posts
            .annotate_comments_count()
            .order_by('-pub_date')
        )
        if self.request.user != author:
            queryset = queryset.published()
        return queryset

    def get_context_data(self, **kwargs):
        """Добавляем объект пользователя в контекст."""
        context = super().get_context_data(**kwargs)
        context['profile'] = self._get_author()
        return context


class ProfileEditView(
    LoginRequiredMixin,
    UpdateView
):
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
        """Возвращаем текущего пользователя для редактирования."""
        return self.request.user


class PostCreateView(
    PostMixin,
    SuccessUrlMixin,
    CreateView
):
    """Создание новой публикации (только для авторизованных)."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_object(self):
        """
        Переопределяем, чтобы избежать поиска объекта.
        PostMixin ожидает post_id в URL, что не требуется для CreateView.
        """
        return None

    def form_valid(self, form):
        """Авторство присваиваем текущему пользователю."""
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostEditView(
    PostMixin,
    SuccessUrlMixin,
    UpdateView
):
    """Редактирование существующей публикации (только для автора)."""

    model = Post
    form_class = PostForm


class DeletePostView(
    PostMixin,
    SuccessUrlMixin,
    DeleteView
):
    """Удаление публикации (для автора)."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_form(self, form_class=None):
        return None

    def get_context_data(self, **kwargs):
        """Удаляем форму из контекста."""
        context = super().get_context_data(**kwargs)
        context['form'] = None
        context['object'] = self.get_object()
        return context

    def post(self, request, *args, **kwargs):
        """Обработка POST-запроса без использования формы."""
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return redirect(success_url)
    

class CommentCreateView(
    CommentMixin,
    SuccessUrlMixin,
    CreateView
):
    """Создание комментария (для авторизованных)."""

    form_class = CommentForm

    def form_valid(self, form):
        """Присваиваем автора и публикацию."""
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)


class CommentEditView(
    AuthorCheckMixin,
    CommentMixin,
    SuccessUrlMixin,
    UpdateView
):
    """Редактирование комментария."""

    form_class = CommentForm
    template_name = 'blog/comment.html'


class CommentDeleteView(
    AuthorCheckMixin,
    CommentMixin,
    SuccessUrlMixin,
    DeleteView
):
    """Удаление комментария (для автора)."""

    template_name = 'blog/comment.html'

    def get_object(self):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post_id=self.kwargs['post_id']
        )


def index(request):
    """Функция для главной страницы."""
    posts = Post.objects.published().annotate_comments_count()
    page_obj = get_paginated_page(posts, request, POSTS_LIMIT_ON_PAGE)
    return render(
        request, 'blog/index.html', {'page_obj': page_obj}
    )


def category_posts(request, category_slug):
    """Функция для страницы категории."""
    category = get_object_or_404(  # Получаем категорию или 404.
        Category,
        slug=category_slug,  # Категория со slug существует.
        is_published=True  # Пост опубликован.
    )
    posts = category.posts.published().annotate_comments_count()
    page_obj = get_paginated_page(posts, request, POSTS_LIMIT_ON_PAGE)
    return render(
        request, 'blog/category.html', {
            'category': category,
            'page_obj': page_obj
        }
    )


def post_detail(request, post_id):
    """Функция для страницы публикации."""
    post = get_object_or_404(
        Post.objects.annotate(comment_count=Count('comments'))
        .select_related(
            'author',
            'category',
            'location'
        ),
        (
            Q(is_published=True, pub_date__lte=now(),
              category__is_published=True)
            | Q(author=request.user)
            if request.user.is_authenticated
            else Q()
        ),
        pk=post_id
    )
    # Получаем комментарии с авторами и пагинацией.
    comments = post.comments.select_related('author').all()
    page_obj = get_paginated_page(comments, request, COMMENTS_LIMIT_ON_PAGE)
    return render(request, 'blog/detail.html', {
        'post': post,
        'page_obj': page_obj,
        'form': CommentForm()
    })
