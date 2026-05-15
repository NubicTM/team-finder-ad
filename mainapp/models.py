import random
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from .constants import (
    AVATAR_COLORS,
    AVATAR_SIZE,
    NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    PHONE_REGEX_PATTERN,
    ABOUT_MAX_LENGTH,
    SKILL_NAME_MAX_LENGTH,
    PROJECT_NAME_MAX_LENGTH,
    STATUS_MAX_LENGTH,
    STATUS_CHOICES,
    STATUS_OPEN,
)
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Модель пользователя."""

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    email = models.EmailField('Электронная почта', unique=True)
    name = models.CharField('Имя', max_length=NAME_MAX_LENGTH)
    surname = models.CharField('Фамилия', max_length=NAME_MAX_LENGTH)
    avatar = models.ImageField(
        'Аватар', upload_to='avatars/', blank=True, null=True
    )
    phone = models.CharField(
        'Телефон',
        max_length=PHONE_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=PHONE_REGEX_PATTERN,
                message='Неверный формат номера'
            )
        ]
    )
    github_url = models.URLField('GitHub', blank=True)
    about = models.TextField('О себе', max_length=ABOUT_MAX_LENGTH, blank=True)
    is_active = models.BooleanField('Активный', default=True)
    is_staff = models.BooleanField('Администратор', default=False)
    date_joined = models.DateTimeField('Дата регистрации', default=timezone.now)

    favorites = models.ManyToManyField(
        'Project', related_name='favorited_by', blank=True
    )
    skills = models.ManyToManyField('Skill', related_name='users', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'surname']

    objects = UserManager()

    def __str__(self) -> str:
        return self.get_full_name()

    def get_full_name(self) -> str:
        """Возвращает полное имя пользователя."""
        return f"{self.name} {self.surname}"

    def normalize_phone(self) -> None:
        """Приводит номер телефона к формату +7XXXXXXXXXX."""
        if self.phone and self.phone.startswith('8'):
            self.phone = '+7' + self.phone[1:]

    def generate_avatar(self) -> None:
        """Генерирует аватарку с инициалом имени."""
        if self.avatar:
            return

        size = AVATAR_SIZE
        color = random.choice(AVATAR_COLORS)
        image = Image.new('RGB', (size, size), color)
        draw = ImageDraw.Draw(image)

        letter = self.name[0].upper() if self.name else '?'

        try:
            font = ImageFont.truetype("arial.ttf", 50)
            bbox = draw.textbbox((0, 0), letter, font=font)
            x = (size - (bbox[2] - bbox[0])) // 2
            y = (size - (bbox[3] - bbox[1])) // 2
            draw.text((x, y), letter, fill='white', font=font)
        except Exception:
            draw.text((size // 2, size // 2), letter, fill='white', anchor='mm')

        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)

        self.avatar.save(
            f'avatar_{self.email}.png',
            ContentFile(buffer.read()),
            save=False
        )


class Skill(models.Model):
    """Модель навыка."""

    class Meta:
        verbose_name = 'Навык'
        verbose_name_plural = 'Навыки'

    name = models.CharField(
        'Название навыка',
        max_length=SKILL_NAME_MAX_LENGTH,
        unique=True
    )

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    """Модель проекта."""

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'

    name = models.CharField(
        'Название проекта',
        max_length=PROJECT_NAME_MAX_LENGTH
    )
    description = models.TextField('Описание', blank=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owned_projects'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    github_url = models.URLField('GitHub', blank=True)
    status = models.CharField(
        'Статус',
        max_length=STATUS_MAX_LENGTH,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN
    )
    participants = models.ManyToManyField(
        User, related_name='participated_projects', blank=True
    )
    skills = models.ManyToManyField(Skill, related_name='projects', blank=True)

    def __str__(self) -> str:
        return self.name
