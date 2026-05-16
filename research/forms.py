from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    ResearchProject,
    Resource,
    ResearchSummary,
    ComparisonTable,
    ComparisonRow,
)


class BootstrapModelForm(forms.ModelForm):
    """
    Lightweight Bootstrap 5 styling for Django forms without extra packages.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
                continue
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault("class", "form-control")
            else:
                widget.attrs.setdefault("class", "form-control")
            if field.required:
                widget.attrs.setdefault("required", "required")


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.setdefault("class", "form-control")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class LoginForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ResearchProjectForm(BootstrapModelForm):
    class Meta:
        model = ResearchProject
        fields = ["title", "description", "status"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class ResourceForm(BootstrapModelForm):
    class Meta:
        model = Resource
        fields = ["title", "resource_type", "file", "url", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
            "url": forms.URLInput(attrs={"placeholder": "https://…"}),
        }

    def clean(self):
        cleaned = super().clean()
        rtype = cleaned.get("resource_type")
        file = cleaned.get("file")
        url = cleaned.get("url")
        notes = cleaned.get("notes")

        if rtype == "pdf" and not file:
            self.add_error("file", "Please upload a PDF file for PDF resources.")
        if rtype == "link" and not url:
            self.add_error("url", "Please provide a URL for link resources.")
        if rtype == "note" and not (notes or "").strip():
            self.add_error("notes", "Please add some notes for note resources.")

        return cleaned


class ResearchSummaryForm(BootstrapModelForm):
    class Meta:
        model = ResearchSummary
        fields = [
            "title",
            "resource",
            "summary_text",
            "citation_source",
            "citation_page",
            "citation_quote",
        ]
        widgets = {
            "summary_text": forms.Textarea(attrs={"rows": 8}),
            "citation_quote": forms.Textarea(attrs={"rows": 3}),
        }


class ComparisonTableForm(BootstrapModelForm):
    class Meta:
        model = ComparisonTable
        fields = ["title"]


class ComparisonRowForm(BootstrapModelForm):
    class Meta:
        model = ComparisonRow
        fields = ["name", "criteria", "score", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }