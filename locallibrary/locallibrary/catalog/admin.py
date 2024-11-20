from django.contrib import admin
from .models import Author, Genre, Book, BookInstance
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm
from .models import Profile


# admin.site.register(Book)
# admin.site.register(Author)
admin.site.register(Genre)
# admin.site.register(BookInstance)

class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'date_of_birth', 'date_of_death')
    fields = ['first_name', 'last_name', ('date_of_birth', 'date_of_death')]
    inlines = []

    # Добавляем встроенный список книг для авторов
    class BooksInline(admin.TabularInline):
        model = Book
        extra = 0  # не показывать пустые строки для добавления новых книг


# Register the admin class with the associated model
admin.site.register(Author, AuthorAdmin)

class BooksInstanceInline(admin.TabularInline):
    model = BookInstance

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_genre')
    inlines = [BooksInstanceInline]
# Register the Admin classes for BookInstance using the decorator

@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_filter = ('status', 'due_back')
    list_display = ('book', 'status', 'borrower', 'due_back', 'id')

    fieldsets = (
        (None, {
            'fields': ('book', 'imprint', 'id')
        }),
        ('Availability', {
            'fields': ('status', 'due_back', 'borrower')
        }),
    )

class CustomUserAdmin(UserAdmin):
    # Указываем кастомную форму для создания пользователей
    add_form = CustomUserCreationForm

    # Поля, которые будут отображаться в списке пользователей
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'secret_question')

    # Поля, доступные для фильтрации в списке пользователей
    list_filter = ('is_staff', 'is_superuser', 'groups')

    # Поля, которые будут отображаться в деталях пользователя
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'secret_question', 'secret_answer')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Поля, которые будут отображаться при добавлении пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'secret_question', 'secret_answer', 'is_staff')}
        ),
    )

    # Регистрируем модель в админке
    search_fields = ('username', 'email')
    ordering = ('username',)

# Регистрация модели в админке
admin.site.register(CustomUser, CustomUserAdmin)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'secret_question', 'secret_answer')
    search_fields = ('user__username', 'secret_question')

admin.site.register(Profile, ProfileAdmin)