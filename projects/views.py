from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import Project
from .forms import ProjectForm


def project_list(request):
    """Список проектов"""
    projects = Project.objects.all().order_by("-created_at")
    paginator = Paginator(projects, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "projects/project_list.html", {"projects": page_obj.object_list})


@ensure_csrf_cookie
def project_detail(request, project_id):
    """Информация о проекте"""
    project = get_object_or_404(Project, pk=project_id)
    return render(request, "projects/project-details.html", {"project": project})


@login_required
@require_POST
def toggle_participation(request, project_id):
    """Присоединение к проекту"""
    project = get_object_or_404(Project, pk=project_id)
    user = request.user

    if project.owner == user:
        return JsonResponse({"status": "error", "error": "Owner cannot toggle participation"}, status=400)

    participating = project.participants.filter(pk=user.pk).exists()
    if not participating and project.status == "closed":
        return JsonResponse({"status": "error", "error": "Cannot join closed project"}, status=400)

    if participating:
        project.participants.remove(user)
    else:
        project.participants.add(user)

    return JsonResponse({"status": "ok", "participant": not participating})


@login_required
@require_POST
def complete_project(request, project_id):
    """Завершение проекта"""
    project = get_object_or_404(Project, pk=project_id)
    user = request.user

    if project.owner != user:
        return JsonResponse({"status": "error", "error": "Only owner can complete project"}, status=403)
    if project.status != "open":
        return JsonResponse({"status": "error", "error": "Project is not open"}, status=400)

    project.status = "closed"
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": "closed"})


@login_required
def create_or_edit_project(request, project_id=None):
    """Общая view для создания и редактирования проекта"""
    project = None
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        if project.owner != request.user and not request.user.is_staff:
            return redirect("projects:project_list")
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            obj = form.save(commit=False)
            if not project:
                obj.owner = request.user
            obj.save()
            form.save_m2m()
            return redirect("projects:project_detail", project_id=obj.id)
    else:
        form = ProjectForm(instance=project)
    return render(request, "projects/create-project.html", {"form": form, "is_edit": bool(project)})