from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from blog.views import SignUpView


urlpatterns = [
    # Админка Django.
    path('admin/', admin.site.urls),

    # Основные URL приложения blog.
    path('', include('blog.urls')),

    # URL для дополнительных страниц приложения pages.
    path('pages/', include('pages.urls')),

    # Стандартные URL-адреса аутентификации Django.
    path('auth/', include('django.contrib.auth.urls')),

    # Регистрация пользователя.
    path('auth/registration/',
         SignUpView.as_view(),
         name='registration'),
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
