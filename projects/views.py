from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from http import HTTPStatus

from .models import Project
from constants import STATUS_OPEN, STATUS_CLOSED, PAG_PER_PAGE
from .forms import ProjectForm
from core.service import paginate


def project_list(request):
    """Список проектов"""
    projects = (
        Project.objects.select_related("owner")
        .annotate(participant_count=Count("participants"))
        .order_by("-created_at")
    )
    page_obj = paginate(request, projects, PAG_PER_PAGE)
    return render(
        request,
        "projects/project_list.html",
        {"projects": page_obj.object_list,
         "STATUS_OPEN": STATUS_OPEN,
         "STATUS_CLOSED": STATUS_CLOSED
        },
    )


@ensure_csrf_cookie
def project_detail(request, project_id):
    """Информация о проекте"""
    qs = (
        Project.objects.select_related("owner")
        .prefetch_related("participants")
        .annotate(participant_count=Count("participants"))
    )
    project = get_object_or_404(qs, pk=project_id)
    return render(
        request,
        "projects/project-details.html",
        {"project": project,
         "STATUS_OPEN": STATUS_OPEN,
         "STATUS_CLOSED": STATUS_CLOSED
         },
    )

@login_required
@require_POST
def toggle_participation(request, project_id):
    """Присоединение к проекту"""
    project = get_object_or_404(Project, pk=project_id)
    user = request.user

    if project.owner == user:
        return redirect("projects:project_detail", project_id=project_id)

    participating = project.participants.filter(pk=user.pk).exists()
    if not participating and project.status == STATUS_CLOSED:
        return redirect("projects:project_detail", project_id=project_id)

    if participating:
        project.participants.remove(user)
    else:
        project.participants.add(user)

    return redirect("projects:project_detail", project_id=project_id)


@login_required
@require_POST
def complete_project(request, project_id):
    """Завершение проекта"""
    project = get_object_or_404(Project, pk=project_id)
    user = request.user

    if project.owner != user:
        return JsonResponse(
            {"status": "error", "error": "Only owner can complete project"},
            status=HTTPStatus.FORBIDDEN
        )
    if project.status != STATUS_OPEN:
        return JsonResponse(
            {"status": "error", "error": "Project is not open"},
            status=HTTPStatus.BAD_REQUEST
        )

    project.status = STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": project.status})


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
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": bool(project)}
    )