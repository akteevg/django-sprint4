from django.core.paginator import Paginator
from django.db.models import QuerySet

from .constants import (POSTS_LIMIT_ON_PAGE, TRUNCATE_LENGTH)


def truncate_text(text, length=TRUNCATE_LENGTH):
    """Функция обрезает тексты для удобного краткого отображения."""
    return text[:length] + '...' if len(text) > length else text


def paginate_posts(
        posts: QuerySet, page_number: str,
        page_size: int = POSTS_LIMIT_ON_PAGE
    ) -> tuple[Paginator, object]:
    """Создает пагинатор для постов и возвращает страницу."""
    paginator = Paginator(posts, page_size)
    page_obj = paginator.get_page(page_number)
    return paginator, page_obj
