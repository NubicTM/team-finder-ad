from django.urls import path

from . import views

urlpatterns = [
    path('', views.redirect_to_projects),
    path('projects/list/', views.project_list, name='project_list'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path(
        'projects/create-project/',
        views.project_create,
        name='project_create'
    ),
    path(
        'projects/<int:pk>/edit/',
        views.project_edit,
        name='project_edit'
    ),
    path(
        'projects/<int:pk>/toggle-participate/',
        views.toggle_participate,
        name='toggle_participate'
    ),
    path(
        'projects/<int:pk>/toggle-favorite/',
        views.toggle_favorite,
        name='toggle_favorite'
    ),
    path(
        'projects/favorites/',
        views.favorite_projects,
        name='favorite_projects'
    ),
    path(
        'projects/skills/',
        views.project_skills_autocomplete,
        name='project_skills_autocomplete'
    ),
    path(
        'projects/<int:pk>/skills/add/',
        views.add_project_skill,
        name='add_project_skill'
    ),
    path(
        'projects/<int:pk>/skills/<int:skill_id>/remove/',
        views.remove_project_skill,
        name='remove_project_skill'
    ),
    path('users/list/', views.users_list, name='users_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/register/', views.register, name='register'),
    path('users/login/', views.user_login, name='login'),
    path('users/logout/', views.user_logout, name='logout'),
    path(
        'users/edit-profile/',
        views.edit_profile,
        name='edit_profile'
    ),
    path(
        'users/change-password/',
        views.change_password,
        name='change_password'
    ),
    path(
        'users/skills/',
        views.user_skills_autocomplete,
        name='user_skills_autocomplete'
    ),
    path(
        'users/<int:pk>/skills/add/',
        views.add_user_skill,
        name='add_user_skill'
    ),
    path(
        'users/<int:pk>/skills/<int:skill_id>/remove/',
        views.remove_user_skill,
        name='remove_user_skill'
    ),
]
