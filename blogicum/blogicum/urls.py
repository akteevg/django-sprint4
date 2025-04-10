from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import include, path
from django.views.decorators.http import require_GET

from blog.views import SignUpView


@require_GET  # Разрешаем только GET-запросы для безопасности.
def custom_logout(request):
    """
    Функция-обработчик выхода из системы.
    Выполняет выход и перенаправляет на главную страницу.
    """
    logout(request)
    return redirect('blog:index')


urlpatterns = [
    # Админка Django.
    path('admin/', admin.site.urls),

    # Основные URL приложения blog.
    path('', include('blog.urls')),

    # URL для дополнительных страниц приложения pages.
    path('pages/', include('pages.urls')),

    # Авторизация.
    path('auth/login/',
         auth_views.LoginView.as_view(),
         name='login'),  # Вход в аккаунт.
    path('auth/password_change/',
         auth_views.PasswordChangeView.as_view(),
         name='password_change'),  # Смена пароля.
    path('auth/password_change/done/',
         auth_views.PasswordChangeDoneView.as_view(),
         name='password_change_done'),  # Подтверждение смены пароля.
    path('auth/password_reset/',
         auth_views.PasswordResetView.as_view(),
         name='password_reset'),  # Запрос на сброс пароля.
    path('auth/password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),  # Подтверждение запроса на сброс пароля.
    path('auth/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),  # Форма ввода нового пароля.
    path('auth/reset/done/',
         auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),  # Подтверждение нового пароля.

    # Кастомный logout.
    path('auth/logout/', custom_logout, name='logout'),  # Выход из аккаунта.
    path('auth/registration/',
         SignUpView.as_view(),
         name='registration'),  # Регистрация пользователя.

    # Стандартные URL-адреса аутентификации Django.
    path('auth/', include('django.contrib.auth.urls')),
]

# Отладочные URL в режиме разработки.
if settings.DEBUG:
    import debug_toolbar

    # Добавить к списку urlpatterns список
    # адресов из приложения debug_toolbar:
    urlpatterns += [
        # Панель Debug Toolbar.
        path('__debug__/', include(debug_toolbar.urls)),
    ] + static(
        # Обслуживание медиа-файлов при DEBUG=True.
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

# Обработчики ошибок
handler403 = 'pages.views.csrf_failure'  # Обработчик 403 ошибки
handler404 = 'pages.views.page_not_found'  # Обработчик 404 ошибки
handler500 = 'pages.views.server_error'  # Обработчик 500 ошибки
