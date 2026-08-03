from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # Auth
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Recurring task templates — renamed from /habits/ now that the habits
    # app owns that URL for the full habit tracker (Yes/No, Numeric,
    # Checklist types). This feature still works, it's just at a new path.
    path('recurring-tasks/', views.habits, name='recurring_tasks'),
    path('recurring-tasks/<uuid:template_id>/toggle/', views.habit_toggle_active, name='recurring_task_toggle_active'),
    path('recurring-tasks/<uuid:template_id>/delete/', views.habit_delete, name='recurring_task_delete'),

    # Task CRUD (JSON API)
    path('api/tasks/create/', views.task_create, name='task_create'),
    path('api/tasks/<uuid:task_id>/toggle/', views.task_toggle, name='task_toggle'),
    path('api/tasks/<uuid:task_id>/edit/', views.task_edit, name='task_edit'),
    path('api/tasks/<uuid:task_id>/delete/', views.task_delete, name='task_delete'),
    path('api/tasks/clear-completed/', views.tasks_clear_completed, name='tasks_clear_completed'),

    # Subtasks (JSON API)
    path('api/tasks/<uuid:task_id>/subtasks/create/', views.subtask_create, name='subtask_create'),
    path('api/subtasks/<uuid:task_id>/toggle/', views.subtask_toggle, name='subtask_toggle'),
    path('api/subtasks/<uuid:task_id>/delete/', views.subtask_delete, name='subtask_delete'),

    # Export / Import
    path('export/json/', views.export_json, name='export_json'),
    path('export/txt/', views.export_txt, name='export_txt'),
    path('import/json/', views.import_json, name='import_json'),

    path('accounts/logout/', views.logout_view, name='logout'),
]
