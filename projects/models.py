from django.conf import settings
from django.db import models
from django.urls import reverse

from constants import MAX_LENGTH_RROJECT, MAX_STATUS_LENGTH, STATUS_CHOICES, STATUS_OPEN


class HTTPSURLField(models.URLField):
    def formfield(self, **kwargs):
        return super().formfield(assume_scheme="https", **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, "django.db.models.URLField", args, kwargs


class Project(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_RROJECT)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    github_url = HTTPSURLField(blank=True)
    status = models.CharField(max_length=MAX_STATUS_LENGTH,
                              choices=STATUS_CHOICES,
                              default=STATUS_OPEN
                              )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("projects:project_detail", args=[self.pk])
