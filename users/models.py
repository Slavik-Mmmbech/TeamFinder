import os
import uuid
from io import BytesIO
from random import choice

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from PIL import Image, ImageDraw, ImageFont


class HTTPSURLField(models.URLField):
    def formfield(self, **kwargs):
        return super().formfield(assume_scheme="https", **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, "django.db.models.URLField", args, kwargs


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


def _avatar_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return f"avatars/{uuid.uuid4()}.{ext}"


class Skill(models.Model):
    name = models.CharField(max_length=124, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)
    avatar = models.ImageField(upload_to=_avatar_upload_to, blank=True, null=True)
    phone = models.CharField(max_length=12, blank=True)
    github_url = HTTPSURLField(blank=True)
    about = models.TextField(max_length=256, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    skills = models.ManyToManyField(Skill, related_name="users", blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    objects = UserManager()

    def __str__(self):
        return f"{self.name} {self.surname} <{self.email}>"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        # generate avatar if creating and no avatar provided
        if creating and (not self.avatar):
            try:
                self._generate_initial_avatar()
            except Exception:
                # do not fail saving if avatar generation fails
                pass

    def _generate_initial_avatar(self):
        # create a simple avatar with first letter
        letter = (self.name or "?")[0].upper()
        size = (256, 256)
        colors = ["#1abc9c", "#2ecc71", "#3498db", "#9b59b6", "#34495e", "#16a085", "#27ae60"]
        bg = choice(colors)
        img = Image.new("RGB", size, bg)
        draw = ImageDraw.Draw(img)
        # try to use a truetype font if available, fallback to default
        try:
            font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf")
            font = ImageFont.truetype(font_path, 120)
        except Exception:
            font = ImageFont.load_default()
        w, h = draw.textsize(letter, font=font)
        draw.text(((size[0]-w)/2, (size[1]-h)/2), letter, fill="#ffffff", font=font)

        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        name = f"avatar_{uuid.uuid4().hex}.png"
        self.avatar.save(name, ContentFile(buf.read()), save=False)
        buf.close()
        # save again to update avatar field
        super().save(update_fields=["avatar"])