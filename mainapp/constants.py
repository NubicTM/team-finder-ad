"""
Константы для проекта TeamFinder
"""

from enum import Enum


class AvatarColor(str, Enum):
    """Цвета для аватарок"""
    INDIGO = '#4F46E5'
    GREEN = '#10B981'
    ORANGE = '#F59E0B'
    RED = '#EF4444'
    PURPLE = '#8B5CF6'
    PINK = '#EC4899'
    CYAN = '#06B6D4'
    LIME = '#84CC16'
    AMBER = '#F97316'
    BLUE = '#6366F1'


# Список цветов для аватарок
AVATAR_COLORS = [
    AvatarColor.INDIGO,
    AvatarColor.GREEN,
    AvatarColor.ORANGE,
    AvatarColor.RED,
    AvatarColor.PURPLE,
    AvatarColor.PINK,
    AvatarColor.CYAN,
    AvatarColor.LIME,
    AvatarColor.AMBER,
    AvatarColor.BLUE,
]

# Настройки аватарок
AVATAR_DEFAULT_COLOR = AvatarColor.INDIGO
AVATAR_SIZE = 100
AVATAR_FONT_SIZE = 50
AVATAR_TEXT_COLOR = 'white'

# Длины полей
NAME_MAX_LENGTH = 124
PHONE_MAX_LENGTH = 12
ABOUT_MAX_LENGTH = 256
SKILL_NAME_MAX_LENGTH = 124
PROJECT_NAME_MAX_LENGTH = 200
STATUS_MAX_LENGTH = 6

# Регулярное выражение для телефона
PHONE_REGEX_PATTERN = r'^(\+7|8)\d{10}$'

# Сообщение для валидации GitHub URL
GITHUB_VALIDATION_MESSAGE = 'Ссылка должна вести на GitHub'

# Статусы проектов
STATUS_OPEN = 'open'
STATUS_CLOSED = 'closed'

STATUS_CHOICES = [
    (STATUS_OPEN, 'Открыт'),
    (STATUS_CLOSED, 'Закрыт'),
]

# Пагинация
PAGINATION_LIMIT = 12

# Автодополнение
AUTOCOMPLETE_LIMIT = 10
