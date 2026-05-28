from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from projects.models import Project
import json

from .models import User, Skill
from .forms import RegistrationForm, LoginForm, EditProfileForm, ChangePasswordForm


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

    paginator = Paginator(participants.order_by("id"), 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    all_skills = Skill.objects.all()

    return render(request, "users/participants.html", {"participants": page_obj.object_list, "all_skills": all_skills, "active_skill": skill, "active_filter": active_filter})


def user_detail(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    return render(request, "users/user-details.html", {"user": user})


def register(request):
    """Регистрация нового пользователя"""
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # сразу вход после регистрации
            login(request, user)
            return redirect("projects:project_list")
    else:
        form = RegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    """Вход по email и паролю"""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            # использую username=email при authenticate, т.к. USERNAME_FIELD='email'
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect("projects:project_list")
            else:
                messages.error(request, "Неверный email или пароль")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("users:login")


@login_required
def edit_profile(request):
    """Редактирование профиля пользователя"""
    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Профиль сохранён")
            return redirect("users:user_detail", user_id=user.id)
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    """Смена пароля для авторизованного пользователя"""
    if request.method == "POST":
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            # обновление сессии, чтобы пользователь остался в системе
            update_session_auth_hash(request, request.user)
            messages.success(request, "Пароль успешно изменён")
            return redirect("users:user_detail", user_id=request.user.id)
    else:
        form = ChangePasswordForm(user=request.user)
    return render(request, "users/change_password.html", {"form": form})


@login_required
def skills_search(request):
    """Поиск навыков для автокомплита. Возвращает JSON список {id,name}"""
    q = request.GET.get("q", "").strip()
    qs = Skill.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    results = list(qs.order_by("name").values("id", "name")[:20])
    return JsonResponse(results, safe=False)


@login_required
@require_POST
def add_skill(request):
    """Добавить навык текущему пользователю. Ожидает JSON {skill_id} или {name}. Возвращает объект навыка в JSON."""
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
