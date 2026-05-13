import random
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

AVATAR_COLORS = [
    '#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1',
]


class UserManager(BaseUserManager):
    def create_user(self, email, name, surname, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)

        user = self.model(
            email=email, name=name, surname=surname, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)

        if not user.avatar:
            user.generate_avatar()
            user.save(using=self._db)

        return user

    def create_superuser(self, email, name, surname, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, name, surname, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField('Электронная почта', unique=True)
    name = models.CharField('Имя', max_length=124)
    surname = models.CharField('Фамилия', max_length=124)
    avatar = models.ImageField(
        'Аватар', upload_to='avatars/', blank=True, null=True
    )
    phone = models.CharField(
        'Телефон',
        max_length=12,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^(\+7|8)\d{10}$',
                message='Неверный формат номера'
            )
        ]
    )
    github_url = models.URLField('GitHub', blank=True)
    about = models.TextField('О себе', max_length=512, blank=True)
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

    def __str__(self):
        return f"{self.name} {self.surname}"

    def get_full_name(self):
        return f"{self.name} {self.surname}"

    def normalize_phone(self):
        if self.phone and self.phone.startswith('8'):
            self.phone = '+7' + self.phone[1:]

    def generate_avatar(self):
        size = 100
        color = random.choice(AVATAR_COLORS)
        image = Image.new('RGB', (size, size), color)
        draw = ImageDraw.Draw(image)

        letter = self.name[0].upper() if self.name else '?'

        try:
            font = ImageFont.truetype("arial.ttf", 50)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), letter, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (size - text_width) // 2
        y = (size - text_height) // 2

        draw.text((x, y), letter, fill='white', font=font)

        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)

        self.avatar.save(
            f'avatar_{self.email}.png',
            ContentFile(buffer.read()),
            save=False
        )


class Skill(models.Model):
    name = models.CharField('Название навыка', max_length=124, unique=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    STATUS_CHOICES = [
        ('open', 'Открыт'),
        ('closed', 'Закрыт'),
    ]

    name = models.CharField('Название проекта', max_length=200)
    description = models.TextField('Описание', blank=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owned_projects'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    github_url = models.URLField('GitHub', blank=True)
    status = models.CharField(
        'Статус', max_length=6, choices=STATUS_CHOICES, default='open'
    )
    participants = models.ManyToManyField(
        User, related_name='participated_projects', blank=True
    )
    skills = models.ManyToManyField(Skill, related_name='projects', blank=True)

    def __str__(self):
        return self.name
