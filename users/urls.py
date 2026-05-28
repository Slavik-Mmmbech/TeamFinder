from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("list/", views.participants_list, name="participants_list"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("skills/", views.skills_search, name="skills_search"),
    path("skills/add/", views.add_skill, name="add_skill"),
    path("skills/<int:skill_id>/remove/", views.remove_skill, name="remove_skill"),
    path("<int:user_id>/", views.user_detail, name="user_detail"),
]
