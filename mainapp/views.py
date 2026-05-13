from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm, UserLoginForm, UserProfileForm, UserRegisterForm
from .models import Project, Skill, User


def redirect_to_projects(request):
    return redirect('project_list')


def project_list(request):
    projects_list = Project.objects.all().order_by('-created_at')
    skill_filter = request.GET.get('skill')

    if skill_filter:
        projects_list = projects_list.filter(
            skills__name=skill_filter
        ).distinct()

    paginator = Paginator(projects_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    all_skills = Skill.objects.all().order_by('name')

    return render(request, 'projects/project_list.html', {
        'page_obj': page_obj,
        'all_skills': all_skills,
        'active_skill': skill_filter,
    })


def project_detail(request, pk):
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
    project = get_object_or_404(Project, pk=pk)

    if project.owner == request.user:
        return JsonResponse(
            {'error': 'Нельзя участвовать в своём проекте'}, status=400
        )

    if project.participants.filter(id=request.user.id).exists():
        project.participants.remove(request.user)
        is_participant = False
    else:
        project.participants.add(request.user)
        is_participant = True

    return JsonResponse({'is_participant': is_participant})


@login_required
def toggle_favorite(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user.favorites.filter(id=project.id).exists():
        request.user.favorites.remove(project)
        is_favorite = False
    else:
        request.user.favorites.add(project)
        is_favorite = True

    return JsonResponse({'favorited': is_favorite})


@login_required
def favorite_projects(request):
    projects = request.user.favorites.all().order_by('-created_at')
    paginator = Paginator(projects, 12)
    page_number = request.GET.get('page')
    projects = paginator.get_page(page_number)

    return render(request, 'projects/favorite_projects.html', {'projects': projects})


def users_list(request):
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

    paginator = Paginator(users_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'projects/participants.html', {
        'page_obj': page_obj, 'active_filter': filter_type
    })


def user_detail(request, pk):
    user_profile = get_object_or_404(User, pk=pk)
    is_owner = request.user.is_authenticated and request.user == user_profile

    return render(request, 'projects/user-details.html', {
        'user': user_profile,
        'is_owner': is_owner,
        'projects': user_profile.owned_projects.all(),
    })


def register(request):
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
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(email=form.cleaned_data['email'])
                user = authenticate(
                    request,
                    username=user.email,
                    password=form.cleaned_data['password']
                )
                if user:
                    login(request, user)
                    return redirect('project_list')
            except User.DoesNotExist:
                pass
            form.add_error(None, 'Неверный email или пароль')
    else:
        form = UserLoginForm()

    return render(request, 'projects/login.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    return redirect('project_list')


@login_required
def edit_profile(request):
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
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            return redirect('user_detail', pk=request.user.pk)
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'projects/change_password.html', {'form': form})


def project_skills_autocomplete(request):
    q = request.GET.get('q', '')
    skills = Skill.objects.filter(name__icontains=q).order_by('name')[:10]

    return JsonResponse(
        [{'id': s.id, 'name': s.name} for s in skills], safe=False
    )


def user_skills_autocomplete(request):
    q = request.GET.get('q', '')
    skills = Skill.objects.filter(name__icontains=q).order_by('name')[:10]

    return JsonResponse(
        [{'id': s.id, 'name': s.name} for s in skills], safe=False
    )


@login_required
def add_project_skill(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if project.owner != request.user:
        return JsonResponse(
            {'status': 'error', 'message': 'Нет прав'}, status=403
        )

    skill_id = request.POST.get('skill_id')
    skill_name = request.POST.get('name')

    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    elif skill_name:
        skill, _ = Skill.objects.get_or_create(name=skill_name)
    else:
        return JsonResponse(
            {'status': 'error', 'message': 'Не указан навык'}, status=400
        )

    if not project.skills.filter(id=skill.id).exists():
        project.skills.add(skill)

    return JsonResponse({'status': 'ok', 'skill_id': skill.id})


@login_required
def remove_project_skill(request, pk, skill_id):
    project = get_object_or_404(Project, pk=pk)
    skill = get_object_or_404(Skill, pk=skill_id)

    if project.owner != request.user:
        return JsonResponse(
            {'status': 'error', 'message': 'Нет прав'}, status=403
        )

    if project.skills.filter(id=skill.id).exists():
        project.skills.remove(skill)

    return JsonResponse({'status': 'ok'})


@login_required
def add_user_skill(request, pk):
    user_profile = get_object_or_404(User, pk=pk)

    if user_profile != request.user:
        return JsonResponse(
            {'status': 'error', 'message': 'Нет прав'}, status=403
        )

    skill_id = request.POST.get('skill_id')
    skill_name = request.POST.get('name')

    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    elif skill_name:
        skill, _ = Skill.objects.get_or_create(name=skill_name)
    else:
        return JsonResponse(
            {'status': 'error', 'message': 'Не указан навык'}, status=400
        )

    if not user_profile.skills.filter(id=skill.id).exists():
        user_profile.skills.add(skill)

    return JsonResponse({'status': 'ok', 'skill_id': skill.id})


@login_required
def remove_user_skill(request, pk, skill_id):
    user_profile = get_object_or_404(User, pk=pk)
    skill = get_object_or_404(Skill, pk=skill_id)

    if user_profile != request.user:
        return JsonResponse(
            {'status': 'error', 'message': 'Нет прав'}, status=403
        )

    if user_profile.skills.filter(id=skill.id).exists():
        user_profile.skills.remove(skill)

    return JsonResponse({'status': 'ok'})