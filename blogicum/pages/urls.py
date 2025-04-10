from django.urls import path

from .views import AboutView, RulesView

app_name = 'pages'  # namespase для приложения pages.

urlpatterns = [
    # Страница "О проекте".
    path('about/', AboutView.as_view(), name='about'),
    # Страница "Правила".
    path('rules/', RulesView.as_view(), name='rules'),
]
