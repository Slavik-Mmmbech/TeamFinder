from io import BytesIO
import os
from random import choice
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageDraw, ImageFont

from constants import (
    AVATAR_COLORS,
    AVATAR_SIZE,
    AVATAR_FONT_NAME,
    AVATAR_FONT_SIZE,
    AVATAR_TEXT_COLOR,
    AVATAR_IMAGE_FORMAT,
    MAX_ABOUT_LENGTH,
    MAX_LENGTH_USER,
    PHONE_LENGTH
)
from .managers import UserManager


class HTTPSURLField(models.URLField):
    def formfield(self, **kwargs):
        return super().formfield(assume_scheme="https", **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, "django.db.models.URLField", args, kwargs


def _avatar_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return f"avatars/{uuid.uuid4()}.{ext}"


class Skill(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_USER, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=MAX_LENGTH_USER)
    surname = models.CharField(max_length=MAX_LENGTH_USER)
    avatar = models.ImageField(upload_to=_avatar_upload_to,
                               blank=True,
                               null=True
    )
    phone = models.CharField(max_length=PHONE_LENGTH, blank=True)
    github_url = HTTPSURLField(blank=True)
    about = models.TextField(max_length=MAX_ABOUT_LENGTH, blank=True)

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
        size = AVATAR_SIZE
        bg = choice(AVATAR_COLORS)
        img = Image.new("RGB", size, bg)
        draw = ImageDraw.Draw(img)
        try:
            font_path = os.path.join(settings.BASE_DIR,
                                     "static",
                                     "fonts",
                                     AVATAR_FONT_NAME
            )
            font = ImageFont.truetype(font_path, AVATAR_FONT_SIZE)
        except Exception:
            font = ImageFont.load_default(size=AVATAR_FONT_SIZE)
        bbox = draw.textbbox((0, 0), letter, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        draw.text(
            ((size[0]-w)/2, (size[1]-h)/2),
            letter,
            fill=AVATAR_TEXT_COLOR,
            font=font,
        )

        buf = BytesIO()
        img.save(buf, format=AVATAR_IMAGE_FORMAT)
        buf.seek(0)
        name = f"avatar_{uuid.uuid4().hex}.png"
        self.avatar.save(name, ContentFile(buf.read()), save=False)
        buf.close()
        super().save(update_fields=["avatar"])
