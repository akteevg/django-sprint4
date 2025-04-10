from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Форма для создания/редактирования поста."""

    class Meta:
        model = Post
        fields = [
            'title',     # Заголовок поста.
            'text',      # Основной текст.
            'pub_date',  # Дата публикации.
            'category',  # Категория.
            'location',  # Местоположение.
            'image'      # Изображение.
        ]
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},  # HTML-элемент даты/время
                format='%Y-%m-%dT%H:%M'  # Формат для отображения даты
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Инициализация формы с преобразованием даты для корректного вида.
        При редактировании существующей публикации преобразует datetime в
        формат, совместимый с datetime-local input.
        """
        super().__init__(*args, **kwargs)
        # Если instance передан (редактирование существующего поста).
        if self.instance and self.instance.pk:
            # Преобразуем дату в нужный формат для.
            self.initial['pub_date'] = self.instance.pub_date.strftime(
                '%Y-%m-%dT%H:%M'
            )


class CommentForm(forms.ModelForm):
    """Форма для добавления/редактирования комментария."""

    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }
