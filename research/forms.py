from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    ResearchProject,
    Resource,
    ResearchSummary,
    ComparisonTable,
    ComparisonRow,
)


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class ResearchProjectForm(forms.ModelForm):
    class Meta:
        model = ResearchProject
        fields = ["title", "description"]


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ["title", "resource_type", "file", "url", "notes"]


class ResearchSummaryForm(forms.ModelForm):
    class Meta:
        model = ResearchSummary
        fields = ["title", "resource", "summary_text", "citations"]


class ComparisonTableForm(forms.ModelForm):
    class Meta:
        model = ComparisonTable
        fields = ["title"]


class ComparisonRowForm(forms.ModelForm):
    class Meta:
        model = ComparisonRow
        fields = ["name", "criteria", "score", "notes"]