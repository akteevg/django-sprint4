from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count
from django.utils.timezone import now

from .constants import CHAR_FIELD_MAX_LENGTH
from .services import truncate_text

User = get_user_model()


class CreatedAtAbstract(models.Model):
    """Абстрактная модель."""

    created_at = models.DateTimeField(
        'Добавлено', auto_now_add=True
    )

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class IsPublishedCreatedAtAbstract(CreatedAtAbstract):
    """Абстрактная модель."""

    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    class Meta(CreatedAtAbstract.Meta):
        abstract = True


class PostQuerySet(models.QuerySet):
    """Кастомизация QuerySet. Определяет методы для фильтрации и аннотации."""

    def published(self):
        """Фильтрация опубликованных публикаций."""
        return self.filter(
            is_published=True,
            pub_date__lte=now(),
            category__is_published=True
        )

    def annotate_comments_count(self):
        """Количество комментариев к каждой публикации."""
        return self.annotate(comment_count=Count('comments'))


class Post(IsPublishedCreatedAtAbstract):
    """Публикация."""

    title = models.CharField(
        'Заголовок',
        max_length=CHAR_FIELD_MAX_LENGTH
    )
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text='Если установить дату и время в будущем — '
                  'можно делать отложенные публикации.'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts'
    )
    location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='posts_images/',
        blank=True,
        null=True
    )
    objects = PostQuerySet.as_manager()

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        default_related_name = 'posts'
        ordering = ('-pub_date',)

    def __str__(self):
        return truncate_text(self.title)


class Category(IsPublishedCreatedAtAbstract):
    """Тематическая история."""

    title = models.CharField(
        'Заголовок',
        max_length=CHAR_FIELD_MAX_LENGTH
    )
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL; '
                  'разрешены символы латиницы, цифры, '
                  'дефис и подчёркивание.'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return truncate_text(self.title)


class Location(IsPublishedCreatedAtAbstract):
    """Географическая метка."""

    name = models.CharField(
        'Название места',
        max_length=CHAR_FIELD_MAX_LENGTH,
        default='Планета Земля'
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return truncate_text(self.name)


class Comment(CreatedAtAbstract):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Публикация'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    text = models.TextField('Текст комментария')

    class Meta(CreatedAtAbstract.Meta):
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'

    def __str__(self):
        return f'Комментарий {self.author.username} к посту {self.post.id}'
