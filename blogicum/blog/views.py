from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.timezone import now
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, UpdateView

from .constants import POSTS_LIMIT_ON_MAIN_PAGE
from .forms import PostForm, CommentForm
from .models import Category, Post, Comment
from .services import filter_published_posts
from pages.views import csrf_failure


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
        context = super().get_context_data(**kwargs)
        posts = Post.objects.filter(author=self.object)
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
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})


class PostEditView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if post.author != self.request.user:
            raise PermissionDenied
        return post

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.object.pk})


def index(request):
    """Функция для главной страницы."""
    posts = filter_published_posts(Post.objects)
    paginator = Paginator(posts, POSTS_LIMIT_ON_MAIN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
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
    posts = filter_published_posts(category.posts.all())
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
    """Функция для страницы поста."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'category', 'location'),
        pk=post_id
    )

    # Условие видимости поста для всех.
    is_visible = (
        post.is_published
        and post.pub_date <= now()
        and post.category.is_published
    )

    # Автор, как исключение, видит все свои посты.
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


@login_required
def delete_post(request, post_id):
    """Функция удаления поста."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return csrf_failure(request, reason='Удаление чужой публикации запрещено')

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    
    # Для GET запроса создаем форму с пустыми полями, но передаем instance
    form = PostForm(instance=post)
    return render(request, 'blog/create.html', {
        'form': form,
        'object': post  # Передаем объект для использования в шаблоне
    })


@require_POST
def add_comment(request, post_id):
    """Функция создания комментария к посту."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid() and request.user.is_authenticated:
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return csrf_failure(request, reason="Редактирование чужого комментария запрещено")

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/comment.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return csrf_failure(request, reason="Удаление чужого комментария запрещено")

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, 'blog/comment.html', {'comment': comment})
