from django import forms

from .models import User


class RegistrationForm(forms.ModelForm):
    """Форма регистрации пользователя"""
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Форма входа по email и паролю"""
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)


class EditProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""

    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "phone", "github_url", "about", "skills"]
        widgets = {
            'about': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if url and not url.startswith("https://github.com/"):
            raise forms.ValidationError("GitHub URL должен быть вида https://github.com/username")
        return url


class ChangePasswordForm(forms.Form):
    """Форма смены пароля: старый пароль и два раза новый"""
    old_password = forms.CharField(label="Текущий пароль", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Новый пароль", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Новый пароль (повтор)", widget=forms.PasswordInput)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        old = self.cleaned_data.get("old_password")
        if not self.user.check_password(old):
            raise forms.ValidationError("Неверный текущий пароль")
        return old

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Новые пароли не совпадают")
        return cleaned

    def save(self):
        new = self.cleaned_data.get("new_password1")
        self.user.set_password(new)
        self.user.save()
        return self.user
