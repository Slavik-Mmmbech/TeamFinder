import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Count
from django.views.decorators.http import require_POST

from constants import STATUS_OPEN, STATUS_CLOSED, PAG_PER_PAGE, RESULTS_END
from .forms import RegistrationForm, LoginForm, EditProfileForm, ChangePasswordForm
from .models import User, Skill
from core.service import paginate

def participants_list(request):
    skill = request.GET.get("skill")
    active_filter = request.GET.get("filter")
    
    if skill:
        participants = User.objects.filter(skills__name=skill).distinct()
    elif active_filter and request.user.is_authenticated:
        
        if active_filter == "owners-of-participating-projects":
            # Авторы проектов, в которых я участвую
            participating_projects = request.user.participated_projects.all()
            participants = User.objects.filter(owned_projects__in=participating_projects).distinct()
        elif active_filter == "participants-of-my-projects":
            # Участники моих проектов
            my_projects = request.user.owned_projects.all()
            participants = User.objects.filter(participated_projects__in=my_projects).distinct()
        else:
            # Фильтры, требующие дополнительных полей модели
            participants = User.objects.none()
    else:
        participants = User.objects.all()

    page_obj = paginate(request, participants.order_by("id"), PAG_PER_PAGE)

    all_skills = Skill.objects.all()

    return render(request, "users/participants.html", {"participants": page_obj.object_list, "all_skills": all_skills, "active_skill": skill, "active_filter": active_filter})


def user_detail(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    owned_projects = (
        user.owned_projects.select_related("owner")
        .annotate(participant_count=Count("participants"))
        .order_by("-created_at")
    )
    return render(
        request,
        "users/user-details.html",
        {
            "user": user,
            "owned_projects": owned_projects,
            "STATUS_OPEN": STATUS_OPEN,
            "STATUS_CLOSED": STATUS_CLOSED
        },
    )


def register(request):
    """Регистрация нового пользователя"""
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("projects:project_list")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)    
            return redirect("projects:project_list")
        messages.error(request, "Неверный email или пароль")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("users:login")


@login_required
def edit_profile(request):
    form = EditProfileForm(
        request.POST or None, 
        request.FILES or None, 
        instance=request.user
    )
    if form.is_valid():
        user = form.save()
        messages.success(request, "Профиль сохранён")
        return redirect("users:user_detail", user_id=user.id)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    form = ChangePasswordForm(request.POST or None, user=request.user)
    if form.is_valid():
        form.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, "Пароль успешно изменён")
        return redirect("users:user_detail", user_id=request.user.id)
    return render(request, "users/change_password.html", {"form": form})


@login_required 
def skills_search(request): 
    """Поиск навыков для автокомплита. Возвращает JSON список {id,name}""" 
    q = request.GET.get("q", "").strip() 
    qs = Skill.objects.all() 
    
    if q:
        qs = qs.filter(name__istartswith=q) 
    
    results = list(qs.order_by("name").values("id", "name")[:10]) 

    return JsonResponse(results, safe=False)


@login_required
@require_POST
def add_skill(request):
    """Добавить навык текущему пользователю. 
    Ожидает JSON {skill_id} или {name}. Возвращает объект навыка в JSON."""
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    skill = None
    if data.get("skill_id"):
        try:
            skill = Skill.objects.get(pk=int(data.get("skill_id")))
        except Skill.DoesNotExist:
            return HttpResponseBadRequest("Skill not found")
    elif data.get("name"):
        name = data.get("name").strip()
        if not name:
            return HttpResponseBadRequest("Empty name")
        skill, _ = Skill.objects.get_or_create(name=name)
    else:
        return HttpResponseBadRequest("Missing parameters")

    # связывание с пользователем
    request.user.skills.add(skill)
    return JsonResponse({"id": skill.id, "name": skill.name})


@login_required
@require_POST
def remove_skill(request, skill_id):
    """Удалить навык из профиля пользователя"""
    try:
        skill = Skill.objects.get(pk=skill_id)
    except Skill.DoesNotExist:
        return HttpResponseBadRequest("Skill not found")
    request.user.skills.remove(skill)
    return JsonResponse({"status": "ok"})
