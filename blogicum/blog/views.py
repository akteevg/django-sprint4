from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, UpdateView

from pages.views import csrf_failure

from .constants import POSTS_LIMIT_ON_MAIN_PAGE
from .forms import CommentForm, PostForm
from .models import Category, Comment, Post


class SignUpView(CreateView):
    """Класс для формы регистрации пользователя."""

    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


class ProfileView(DetailView):
    """Класс отображения профиля."""

    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        """Добавляем пагинацию постов пользователя в контекст."""
        context = super().get_context_data(**kwargs)
        posts = Post.objects.filter(
            author=self.object
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
        paginator = Paginator(posts, POSTS_LIMIT_ON_MAIN_PAGE)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        return context


class ProfileEditForm(forms.ModelForm):
    """Создаем свою форму с ограниченным набором доступных полей."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def clean_username(self):
        """Проверка уникальности username при редактировании профиля."""
        username = self.cleaned_data['username']  # Новый username из формы
        # Ищем пользователей с таким же username,
        # исключая текущего (self.instance).
        if User.objects.exclude(
            pk=self.instance.pk
        ).filter(username=username).exists():
            raise forms.ValidationError('Это имя пользователя уже занято.')
        return username  # Если проверка пройдена — возвращаем значение


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Класс редактирования профиля."""

    form_class = ProfileEditForm
    template_name = 'blog/user.html'

    def get_success_url(self):
        """Перенаправление в профиль после редактирования."""
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )

    def get_object(self, queryset=None):
        """Проверяем, что пользователь редактирует свой профиль."""
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied
        return user


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание новой публикации (только для авторизованных)."""

    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        """Авторство присваиваем текущему пользователю."""
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Перенаправление в профиль после создания."""
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostEditView(LoginRequiredMixin, UpdateView):
    """Редактирование существующей публикации (только для автора)."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def check_access(self, request, *args, **kwargs):
        """
        Проверка прав доступа.
        1. Если пользователь не авторизован -> редирект на публикацию.
        2. Если пользователь не автор -> редирект на публикацию.
        3. Если проверки пройдены -> разрешено редактирование публикации.
        """
        # Получаем публикацию.
        post = self.get_object()

        # Проверяем на авторизацию:
        if not request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=post.pk)

        # Проверяем на автора:
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)

        return None  # Если проверки пройдены.

    def dispatch(self, request, *args, **kwargs):
        """
        Основной метод обработки запроса.
        Вызывается первым для любых типов запросов (GET, POST и т.д.).
        """
        # Проверка доступа.
        if (access_error := self.check_access(request, *args, **kwargs)):
            return access_error

        # Если проверки пройдены - продолжается стандартная обработка.
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Перенаправление на страницу публикации после редактирования."""
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk}
        )


def index(request):
    """Функция для главной страницы."""
    posts = Post.objects.published().annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    paginator = Paginator(posts, POSTS_LIMIT_ON_MAIN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request, 'blog/index.html', {'page_obj': page_obj}
    )


def category_posts(request, category_slug):
    """Функция для страницы категории."""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = category.posts.published().annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    paginator = Paginator(posts, POSTS_LIMIT_ON_MAIN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

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
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date'),
        pk=post_id
    )

    # Условие видимости публикации для всех.
    is_visible = (
        post.is_published
        and post.pub_date <= now()
        and post.category.is_published
    )

    # Автор, как исключение, видит все свои публикации.
    if not is_visible and (
        not request.user.is_authenticated
        or post.author != request.user
    ):
        raise Http404

    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': post.comments.all(),
        'form': CommentForm()
    })


@login_required  # Только для залогиненых.
def delete_post(request, post_id):
    """Функция удаления публикации."""
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:  # Проверка авторства.
        return csrf_failure(
            request,
            reason='Удаление чужой публикации запрещено'
        )

    # Подтверждение удаления публикации через POST-запрос.
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    # Форма удаления через GET-запрос.
    form = PostForm(instance=post)
    return render(request, 'blog/create.html', {
        'form': form,
        'object': post  # Передаем объект для использования в шаблоне.
    })


@require_POST  # Только для POST-запросов.
@login_required  # Только для залогиненых.
def add_comment(request, post_id):
    """Функция создания комментария к посту."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required  # Только для залогиненых.
def edit_comment(request, post_id, comment_id):
    """Функция редактирования комментария к публикации."""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)

    if comment.author != request.user:  # Проверка авторства.
        return csrf_failure(
            request,
            reason="Редактирование чужого комментария запрещено"
        )

    # Сохранение изменения через POST-запрос.
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        # Форма изменения через GET-запрос.
        form = CommentForm(instance=comment)

    return render(
        request,
        'blog/comment.html',
        {'form': form, 'comment': comment}
    )


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
