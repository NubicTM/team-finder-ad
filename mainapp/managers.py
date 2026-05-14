"""
Менеджеры моделей
"""

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Менеджер для модели User"""

    def create_user(self, email, name, surname, password=None, **extra_fields):
        """Создание обычного пользователя"""
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

    def create_superuser(self, email, name, surname,
                         password=None, **extra_fields):
        """Создание суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, name, surname, password, **extra_fields)
