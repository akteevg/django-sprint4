from django.contrib.auth import get_user_model
from django.db import models
from django.utils.timezone import now

from .constants import CHAR_FIELD_MAX_LENGTH
from .services import truncate_text


class PostQuerySet(models.QuerySet):
    """Кастомный QuerySet для модели Post."""

    def published(self):
        """Возвращает опубликованные посты."""
        return self.filter(
            is_published=True,
            pub_date__lte=now(),
            category__is_published=True
        )

    def with_comments_count(self):
        """Добавляет аннотацию с количеством комментариев."""
        return self.annotate(
            comment_count=models.Count('comments')
        )

    def published_with_comments(self):
        """Возвращает опубликованные посты с количеством комментариев."""
        return self.published().with_comments_count()


User = get_user_model()


class CreatedAtAbstract(models.Model):
    """Абстрактная модель с полем даты создания."""

    created_at = models.DateTimeField(
        'Добавлено',
        auto_now_add=True
    )

    class Meta:
        abstract = True
        ordering = ('created_at',)


class IsPublishedCreatedAtAbstract(CreatedAtAbstract):
    """Абстрактная модель с полями публикации и даты создания."""

    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    class Meta:
        abstract = True


class Post(IsPublishedCreatedAtAbstract):
    """Публикация."""

    objects = PostQuerySet.as_manager()

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
        verbose_name='Автор публикации'
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

    class Meta(CreatedAtAbstract.Meta):
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

    class Meta(CreatedAtAbstract.Meta):
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return truncate_text(self.name)


class Comment(CreatedAtAbstract):
    """Комментарий к публикации."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
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
