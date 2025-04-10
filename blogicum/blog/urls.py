from django.urls import path

from . import views
from .views import PostCreateView, PostEditView, ProfileEditView, ProfileView

app_name = 'blog'  # namespase для приложения blog.

urlpatterns = [
    # Главная страница.
    path('', views.index, name='index'),

    # Страница создания публикации.
    path(
        'posts/create/',
        PostCreateView.as_view(),
        name='create_post'),

    # Страница публикации.
    path(
        'posts/<int:post_id>/',
        views.post_detail,
        name='post_detail'),

    # Страница редактирования публикации.
    path(
        'posts/<int:post_id>/edit/',
        PostEditView.as_view(),
        name='edit_post'),

    # Страница удаления публикации.
    path(
        'posts/<int:post_id>/delete/',
        views.delete_post,
        name='delete_post'),

    # Страница категории.
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'),

    # Страница редактирования профиля пользователя.
    path(
        'profile/edit/',
        ProfileEditView.as_view(), 
        name='edit_profile'),

    # Страница профиля пользователя.
    path(
        'profile/<str:username>/',
        ProfileView.as_view(),
        name='profile'),

    # Страница добавления комментария.
    path(
        'posts/<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'),

    # Страница редактирования комментария.
    path(
        'posts/<int:post_id>/edit_comment/<int:comment_id>/',
        views.edit_comment,
        name='edit_comment'),

    # Страница удаления комментария.
    path(
        'posts/<int:post_id>/delete_comment/<int:comment_id>/',
        views.delete_comment,
        name='delete_comment'),
]
