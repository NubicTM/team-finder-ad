from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm, UserLoginForm, UserProfileForm, UserRegisterForm
from .models import Project, Skill, User
from .constants import PAGINATION_LIMIT, AUTOCOMPLETE_LIMIT
from .services import (
    paginate_queryset,
    get_projects_with_optimization,
    get_user_with_optimization,
    handle_skill_addition,
    handle_skill_removal,
    get_user_list_with_filters,
)


def redirect_to_projects(request):
    """Перенаправляет на страницу со списком проектов."""
    return redirect('project_list')


def project_list(request):
    """Главная страница со списком проектов."""
    projects_list = get_projects_with_optimization().order_by('-created_at')

    skill_filter = request.GET.get('skill')
    if skill_filter:
        projects_list = projects_list.filter(
            skills__name=skill_filter
        ).distinct()

    page_obj = paginate_queryset(request, projects_list, PAGINATION_LIMIT)
    all_skills = Skill.objects.all().order_by('name')

    return render(request, 'projects/project_list.html', {
        'page_obj': page_obj,
        'all_skills': all_skills,
        'active_skill': skill_filter,
    })


def project_detail(request, pk):
    """Страница детального просмотра проекта."""
    project = get_object_or_404(Project, pk=pk)

    is_owner = (
        request.user.is_authenticated and request.user == project.owner
    )
    is_participant = (
        request.user.is_authenticated
        and project.participants.filter(id=request.user.id).exists()
    )
    is_favorite = (
        request.user.is_authenticated
        and request.user.favorites.filter(id=project.id).exists()
    )

    return render(request, 'projects/project-details.html', {
        'project': project,
        'is_owner': is_owner,
        'is_participant': is_participant,
        'is_favorite': is_favorite,
    })


@login_required
def project_create(request):
    """Создание нового проекта."""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            messages.success(request, 'Проект создан!')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm()

    return render(request, 'projects/create-project.html', {
        'form': form, 'is_edit': False
    })


@login_required
def project_edit(request, pk):
    """Редактирование проекта."""
    project = get_object_or_404(Project, pk=pk)

    if project.owner != request.user:
        messages.error(request, 'Нет прав')
        return redirect('project_detail', pk=pk)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Проект обновлён!')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(request, 'projects/create-project.html', {
        'form': form, 'is_edit': True, 'project': project
    })


@login_required
def toggle_participate(request, pk):
    """Участвовать/Отказаться от участия в проекте."""
    project = get_object_or_404(Project, pk=pk)

    if project.owner == request.user:
        return JsonResponse(
            {'error': 'Нельзя участвовать в своём проекте'},
            status=HttpResponseForbidden.status_code
        )

    is_participant = project.participants.filter(
        id=request.user.id
    ).exists()

    if is_participant:
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)

    return JsonResponse({'is_participant': not is_participant})


@login_required
def toggle_favorite(request, pk):
    """Добавить/удалить проект из избранного."""
    project = get_object_or_404(Project, pk=pk)

    is_favorite = request.user.favorites.filter(id=project.id).exists()

    if is_favorite:
        request.user.favorites.remove(project)
    else:
        request.user.favorites.add(project)

    return JsonResponse({'favorited': not is_favorite})


@login_required
def favorite_projects(request):
    """Страница избранных проектов."""
    projects = get_projects_with_optimization().filter(
        favorited_by=request.user
    )
    page_obj = paginate_queryset(request, projects, PAGINATION_LIMIT)

    return render(request, 'projects/favorite_projects.html', {
        'projects': page_obj
    })


def users_list(request):
    """Страница со списком пользователей."""
    users_list = get_user_list_with_filters(request)
    page_obj = paginate_queryset(request, users_list, PAGINATION_LIMIT)

    return render(request, 'projects/participants.html', {
        'page_obj': page_obj,
        'active_filter': request.GET.get('filter')
    })


def user_detail(request, pk):
    """Страница профиля пользователя."""
    user_profile = get_user_with_optimization(pk)
    is_owner = request.user.is_authenticated and request.user == user_profile

    return render(request, 'projects/user-details.html', {
        'user': user_profile,
        'is_owner': is_owner,
        'projects': user_profile.owned_projects.all(),
    })


def register(request):
    """Регистрация нового пользователя."""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.normalize_phone()
            user.save()
            login(request, user)
            return redirect('project_list')
    else:
        form = UserRegisterForm()

    return render(request, 'projects/register.html', {'form': form})


def user_login(request):
    """Авторизация пользователя."""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user = User.objects.get(email=email)
                authenticated_user = authenticate(
                    request,
                    username=user.email,
                    password=password
                )
                if authenticated_user:
                    login(request, authenticated_user)
                    return redirect('project_list')
            except User.DoesNotExist:
                pass

            form.add_error(None, 'Неверный email или пароль')
    else:
        form = UserLoginForm()

    return render(request, 'projects/login.html', {'form': form})


@login_required
def user_logout(request):
    """Выход из аккаунта."""
    logout(request)
    return redirect('project_list')


@login_required
def edit_profile(request):
    """Редактирование профиля пользователя."""
    if request.method == 'POST':
        form = UserProfileForm(
            request.POST, request.FILES, instance=request.user
        )
        if form.is_valid():
            user = form.save(commit=False)
            user.normalize_phone()
            user.save()
            return redirect('user_detail', pk=request.user.pk)
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'projects/edit_profile.html', {'form': form})


@login_required
def change_password(request):
    """Смена пароля пользователя."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            return redirect('user_detail', pk=request.user.pk)
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'projects/change_password.html', {'form': form})


def get_skills_autocomplete(request):
    """Общая функция для автодополнения навыков."""
    search_term = request.GET.get('q', '')
    skills = Skill.objects.filter(
        name__icontains=search_term
    ).order_by('name')[:AUTOCOMPLETE_LIMIT]

    return JsonResponse(
        [{'id': skill.id, 'name': skill.name} for skill in skills],
        safe=False
    )


@login_required
def add_project_skill(request, pk):
    """Добавление навыка к проекту."""
    project = get_object_or_404(Project, pk=pk)

    if project.owner != request.user:
        return JsonResponse(
            {'status': 'error', 'message': 'Нет прав'},
            status=HttpResponseForbidden.status_code
        )

    return handle_skill_addition(project, request.POST, 'skills')


@login_required
def remove_project_skill(request, pk, skill_id):
    """Удаление навыка из проекта."""
    project = get_object_or_404(Project, pk=pk)
    skill = get_object_or_404(Skill, pk=skill_id)

    if project.owner != request.user:
        return JsonResponse(
            {'status': 'error', 'message': 'Нет прав'},
            status=HttpResponseForbidden.status_code
        )

    return handle_skill_removal(project, skill, 'skills')


@login_required
def add_user_skill(request, pk):
    """Добавление навыка пользователю."""
    user_profile = get_object_or_404(User, pk=pk)

    if user_profile != request.user:
        return JsonResponse(
            {'status': 'error', 'message': 'Нет прав'},
            status=HttpResponseForbidden.status_code
        )

    return handle_skill_addition(user_profile, request.POST, 'skills')


@login_required
def remove_user_skill(request, pk, skill_id):
    """Удаление навыка у пользователя."""
    user_profile = get_object_or_404(User, pk=pk)
    skill = get_object_or_404(Skill, pk=skill_id)

    if user_profile != request.user:
        return JsonResponse(
            {'status': 'error', 'message': 'Нет прав'},
            status=HttpResponseForbidden.status_code
        )

    return handle_skill_removal(user_profile, skill, 'skills')
