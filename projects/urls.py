from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("list/", views.project_list, name="project_list"),
    path("create-project/", views.create_or_edit_project, name="create_project"),
    path("<int:project_id>/edit/", views.create_or_edit_project, name="edit_project"),
    path("<int:project_id>/toggle-participate/", views.toggle_participation, name="toggle_participation"),
    path("<int:project_id>/complete/", views.complete_project, name="complete_project"),
    path("<int:project_id>/", views.project_detail, name="project_detail"),
]
