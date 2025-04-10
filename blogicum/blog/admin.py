from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html

from .models import Category, Location, Post

User = get_user_model()  # Получаем модель пользователя.

admin.site.unregister(User)  # Удаляем регистрацию стандартной модели.
admin.site.unregister(Group)  # Удаляем группы.


@admin.register(User)  # Регистрируем кастомизированную админку.
class BlogUserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'posts_count',
        'date_joined'
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active'
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name'
    )

    @admin.display(description='Кол-во постов у пользователя')
    def posts_count(self, author):
        return author.posts.count()


class PostInline(admin.TabularInline):
    model = Post
    extra = 0
    fields = (
        'title',
        'author',
        'pub_date',
        'is_published',
        'created_at'
    )
    readonly_fields = ('created_at',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'description',
        'is_published',
        'created_at'
    )
    list_editable = ('is_published',)
    search_fields = ('title',)
    inlines = [PostInline]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'image_preview',
        'pub_date',
        'author',
        'category',
        'location',
        'is_published',
    )
    list_display_links = (
        'title',
        'author',
        'category',
        'location',
    )
    list_editable = ('is_published',)
    list_filter = ('category', 'location', 'author', 'is_published')
    search_fields = ('title', 'text')

    @admin.display(description='Изображение')
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "Нет изображения"


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at')
    list_editable = ('is_published',)
    list_filter = ('name', 'is_published',)


admin.site.empty_value_display = 'Не задано'
