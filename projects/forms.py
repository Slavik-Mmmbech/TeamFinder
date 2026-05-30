from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if url and not url.startswith("https://github.com/"):
            raise forms.ValidationError(
                "GitHub URL должен быть вида https://github.com/username"
            )
        return url
