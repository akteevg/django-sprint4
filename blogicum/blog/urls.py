from django.urls import path

from .views import ProfileView, ProfileEditView, PostCreateView, PostEditView

from . import views

app_name = 'blog'  # namespase для приложения blog.

urlpatterns = [
    # Главная страница.
    path('', views.index, name='index'),

    # Страница поста.
    path(
        'posts/<int:post_id>/',
        views.post_detail,
        name='post_detail'),
    path(
        'posts/<int:post_id>/edit/',
        PostEditView.as_view(),
        name='edit_post'),
    path(
        'posts/<int:post_id>/delete/',
        views.delete_post,
        name='delete_post'),

    # Страница категории.
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'),
    path(
        'profile/edit/',
        ProfileEditView.as_view(), 
        name='edit_profile'),
    path(
        'profile/<str:username>/',
        ProfileView.as_view(),
        name='profile'),
    path(
        'create/',
        PostCreateView.as_view(),
        name='create_post'),

    # Комментарии.
    path(
        'posts/<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'),
    path(
        'posts/<int:post_id>/edit_comment/<int:comment_id>/',
        views.edit_comment,
        name='edit_comment'),
    path(
        'posts/<int:post_id>/delete_comment/<int:comment_id>/',
        views.delete_comment,
        name='delete_comment'),
]
