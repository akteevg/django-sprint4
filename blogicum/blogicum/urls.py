from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.decorators.http import require_GET
from django.shortcuts import redirect

from blog.views import SignUpView


@require_GET
def custom_logout(request):
    logout(request)
    return redirect('blog:index')



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blog.urls')),  # Подключаем маршруты из blog.
    path('pages/', include('pages.urls')),  # Подключаем маршруты из pages.
    path('auth/login/', auth_views.LoginView.as_view(), name='login'),
    path('auth/password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('auth/password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('auth/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('auth/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('auth/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Кастомный logout
    path('auth/logout/', custom_logout, name='logout'),
    path('auth/registration/', SignUpView.as_view(), name='registration'),
]

if settings.DEBUG:
    import debug_toolbar
    # Добавить к списку urlpatterns список
    # адресов из приложения debug_toolbar:
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'
