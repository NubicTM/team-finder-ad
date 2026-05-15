from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Project, Skill, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админ-панель для модели пользователя с кастомными полями."""

    # Поля, отображаемые в списке пользователей
    list_display = (
        'email', 'name', 'surname', 'phone', 'is_staff', 'is_active'
    )
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    search_fields = ('email', 'name', 'surname', 'phone')
    filter_horizontal = ('skills', 'favorites', 'groups', 'user_permissions')
    readonly_fields = ('date_joined',)
    ordering = ('email',)

    # Разделение на поля для формы редактирования
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': (
                'name', 'surname', 'avatar', 'phone', 'github_url', 'about'
            )
        }),
        (_('Skills and Favorites'), {
            'fields': ('skills', 'favorites'),
            'classes': ('collapse',)
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        (_('Important dates'), {'fields': ('date_joined', 'last_login')}),
    )

    # Поля для формы создания нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'name', 'surname', 'phone', 'password1', 'password2'
            ),
        }),
    )

    def get_queryset(self, request):
        """Оптимизация запросов для списка пользователей."""
        return super().get_queryset(request).select_related().prefetch_related(
            'skills', 'favorites'
        )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Админ-панель для модели навыков."""

    list_display = ('name', 'get_users_count', 'get_projects_count')
    search_fields = ('name',)
    ordering = ('name',)

    @admin.display(description='Пользователей', ordering='users__count')
    def get_users_count(self, obj):
        """Количество пользователей с этим навыком."""
        return obj.users.count()

    @admin.display(description='Проектов', ordering='projects__count')
    def get_projects_count(self, obj):
        """Количество проектов с этим навыком."""
        return obj.projects.count()

    def get_queryset(self, request):
        """Оптимизация запросов для подсчёта."""
        return super().get_queryset(request).prefetch_related('users', 'projects')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Админ-панель для модели проектов."""

    list_display = (
        'name', 'owner_link', 'status', 'participants_count',
        'skills_count', 'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'owner__email', 'owner__name', 'owner__surname')
    filter_horizontal = ('participants', 'skills')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    @admin.display(description='Владелец', ordering='owner')
    def owner_link(self, obj):
        """Ссылка на профиль владельца в админке."""
        url = reverse('admin:mainapp_user_change', args=[obj.owner.id])
        return format_html('<a href="{}">{}</a>', url, obj.owner.get_full_name())

    @admin.display(description='Участников', ordering='participants__count')
    def participants_count(self, obj):
        """Количество участников проекта."""
        count = obj.participants.count()
        url = reverse('admin:mainapp_user_changelist')
        if count > 0:
            participants_ids = ','.join(str(p.id) for p in obj.participants.all())
            return format_html(
                '<a href="{}?id__in={}">{}</a>',
                url, participants_ids, count
            )
        return count

    @admin.display(description='Навыков', ordering='skills__count')
    def skills_count(self, obj):
        """Количество навыков в проекте."""
        return obj.skills.count()

    def get_queryset(self, request):
        """Оптимизация запросов для подсчёта."""
        return super().get_queryset(request).select_related('owner').prefetch_related(
            'participants', 'skills'
        )

    # Действия для массовых операций
    actions = ['make_open', 'make_closed']

    @admin.action(description='Открыть выбранные проекты')
    def make_open(self, request, queryset):
        """Открывает выбранные проекты."""
        queryset.update(status='open')
        self.message_user(request, f'{queryset.count()} проектов открыто')

    @admin.action(description='Закрыть выбранные проекты')
    def make_closed(self, request, queryset):
        """Закрывает выбранные проекты."""
        queryset.update(status='closed')
        self.message_user(request, f'{queryset.count()} проектов закрыто')
