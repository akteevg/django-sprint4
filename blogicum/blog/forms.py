from django import forms

from .models import Comment, Post, User


class ProfileEditForm(forms.ModelForm):
    """Создаем свою форму с ограниченным набором доступных полей."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')

    def clean_username(self):
        """Проверка уникальности username при редактировании профиля."""
        username = self.cleaned_data['username']  # Новый username из формы.
        # Ищем пользователей с таким же username,
        # исключая текущего (self.instance).
        if User.objects.exclude(
            pk=self.instance.pk
        ).filter(username=username).exists():
            raise forms.ValidationError('Это имя пользователя уже занято.')
        return username  # Если проверка пройдена — возвращаем значение.


class PostForm(forms.ModelForm):
    """Форма для создания/редактирования поста."""

    class Meta:
        model = Post
        exclude = (
            'id',            # id.
            'is_published',  # Флаг публикации.
            'created_at',  # Дата пуб.
            'author',    # Категория.
        )
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},  # HTML-элемент даты/время.
                format='%Y-%m-%dT%H:%M'  # Формат для отображения даты.
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
