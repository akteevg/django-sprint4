from django.utils.timezone import now

from blog.constants import TRUNCATE_LENGTH


def truncate_text(text, length=TRUNCATE_LENGTH):
    """Функция обрезает тексты для удобного краткого отображения."""
    return text[:length] + '...' if len(text) > length else text


def filter_published_posts(queryset):
    """Фильтр для всех пользователей (только опубликованные посты)."""
    return queryset.filter(
        is_published=True,
        pub_date__lte=now(),
        category__is_published=True
    )
