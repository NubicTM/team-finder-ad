from django.core.paginator import Paginator, Page
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404

from .constants import PAGINATION_LIMIT
from .models import Skill, User, Project


def paginate_queryset(request, queryset,
                      limit: int = PAGINATION_LIMIT) -> Page:
    """
    Универсальная функция для пагинации queryset'а

    Args:
        request: объект запроса Django
        queryset: QuerySet для пагинации
        limit: количество элементов на странице

    Returns:
        Page object
    """
    paginator = Paginator(queryset, limit)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def get_projects_with_optimization():
    """
    Возвращает QuerySet проектов с оптимизацией запросов к БД
    """
    return Project.objects.select_related('owner').prefetch_related(
        'participants', 'skills', 'favorited_by'
    )


def get_user_with_optimization(user_id: int):
    """
    Возвращает пользователя с оптимизацией запросов к БД
    """
    return User.objects.select_related().prefetch_related(
        'owned_projects', 'participated_projects', 'favorites', 'skills'
    ).get(id=user_id)


def get_user_list_with_filters(request):
    """
    Возвращает отфильтрованный список пользователей
    """
    users_list = User.objects.all().order_by('id')
    filter_type = request.GET.get('filter')

    if request.user.is_authenticated and filter_type:
        if filter_type == 'fav_authors':
            fav_ids = request.user.favorites.values_list('id', flat=True)
            users_list = users_list.filter(
                owned_projects__id__in=fav_ids
            ).distinct()

        elif filter_type == 'my_participants':
            part_ids = request.user.participated_projects.values_list(
                'id', flat=True
            )
            users_list = users_list.filter(
                owned_projects__id__in=part_ids
            ).exclude(id=request.user.id).distinct()

        elif filter_type == 'like_my_projects':
            my_ids = request.user.owned_projects.values_list('id', flat=True)
            users_list = users_list.filter(
                favorites__id__in=my_ids
            ).exclude(id=request.user.id).distinct()

        elif filter_type == 'my_project_members':
            my_ids = request.user.owned_projects.values_list('id', flat=True)
            users_list = users_list.filter(
                participated_projects__id__in=my_ids
            ).exclude(id=request.user.id).distinct()

    return users_list


def handle_skill_addition(obj, post_data, relation_name: str):
    """
    Универсальная функция для добавления навыка (проекту или пользователю)
    """
    skill_id = post_data.get('skill_id')
    skill_name = post_data.get('name')

    if not skill_id and not skill_name:
        return JsonResponse(
            {'status': 'error', 'message': 'Не указан навык'},
            status=HttpResponseBadRequest.status_code
        )

    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    else:
        skill, _ = Skill.objects.get_or_create(name=skill_name)

    related_manager = getattr(obj, relation_name)

    if not related_manager.filter(id=skill.id).exists():
        related_manager.add(skill)

    return JsonResponse({'status': 'ok', 'skill_id': skill.id})


def handle_skill_removal(obj, skill, relation_name: str):
    """
    Универсальная функция для удаления навыка (у проекта или пользователя)
    """
    related_manager = getattr(obj, relation_name)

    if related_manager.filter(id=skill.id).exists():
        related_manager.remove(skill)

    return JsonResponse({'status': 'ok'})
