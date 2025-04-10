from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title',
            'text',
            'pub_date',
            'category',
            'location',
            'image'
        ]
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Если instance передан (редактирование существующего поста)
        if self.instance and self.instance.pk:
            # Преобразуем дату в нужный формат для input[type="datetime-local"]
            self.initial['pub_date'] = self.instance.pub_date.strftime('%Y-%m-%dT%H:%M')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }
