from django.core.paginator import Paginator

from .constants import TRUNCATE_LENGTH


def truncate_text(text, length=TRUNCATE_LENGTH):
    """Функция обрезает тексты для удобного краткого отображения."""
    return text[:length] + '...' if len(text) > length else text


def get_paginated_page(queryset, request, per_page):
    """Создаем пагинатор и возвращаем страницу с объектами."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
