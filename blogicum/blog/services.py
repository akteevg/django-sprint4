"""Сервисные функции для приложения blog."""

from .constants import TRUNCATE_LENGTH


def truncate_text(text, length=TRUNCATE_LENGTH):
    """Функция обрезает тексты для удобного краткого отображения."""
    return text[:length] + '...' if len(text) > length else text
