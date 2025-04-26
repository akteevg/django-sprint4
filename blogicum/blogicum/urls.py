from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.decorators.http import require_GET
from django.shortcuts import render

from blog.views import SignUpView


@require_GET  # Разрешаем только GET-запросы для безопасности.
def custom_logout(request):
    """
    Функция-обработчик выхода из системы.
    Выполняет выход и показывает страницу выхода.
    """
    logout(request)
    return render(request, 'registration/logged_out.html')


urlpatterns = [
    # Админка Django.
    path('admin/', admin.site.urls),

    # Основные URL приложения blog.
    path('', include('blog.urls')),

    # URL для дополнительных страниц приложения pages.
    path('pages/', include('pages.urls')),

    # Кастомный logout с нашим шаблоном.
    path(
        'auth/logout/',
        auth_views.LogoutView.as_view(template_name='registration/logged_out.html'),
        name='logout'
    ),  # Выход из аккаунта.
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
