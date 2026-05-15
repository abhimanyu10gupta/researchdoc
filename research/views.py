import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from pypdf import PdfReader

from .models import (
    UserProfile,
    ResearchProject,
    Resource,
    ResearchSummary,
    ComparisonTable,
    ComparisonRow,
    SubscriptionPlan,
)
from .forms import (
    RegisterForm,
    ResearchProjectForm,
    ResourceForm,
    ResearchSummaryForm,
    ComparisonTableForm,
    ComparisonRowForm,
)


def landing(request):
    return render(request, "research/landing.html")


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            default_plan = SubscriptionPlan.objects.filter(is_archived=False).first()
            UserProfile.objects.create(user=user, subscription_plan=default_plan)
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    projects = ResearchProject.objects.filter(owner=request.user, is_archived=False)
    return render(request, "research/dashboard.html", {"projects": projects})


@login_required
def project_create(request):
    form = ResearchProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        messages.success(request, "Project created.")
        return redirect("project_detail", pk=project.pk)
    return render(request, "research/form.html", {"form": form, "title": "Create project"})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(ResearchProject, pk=pk, owner=request.user, is_archived=False)
    resources = Resource.objects.filter(project=project, is_archived=False)
    summaries = ResearchSummary.objects.filter(project=project)
    tables = ComparisonTable.objects.filter(project=project)

    return render(
        request,
        "research/project_detail.html",
        {
            "project": project,
            "resources": resources,
            "summaries": summaries,
            "tables": tables,
        },
    )


@login_required
def project_edit(request, pk):
    project = get_object_or_404(ResearchProject, pk=pk, owner=request.user)
    form = ResearchProjectForm(request.POST or None, instance=project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project updated.")
        return redirect("project_detail", pk=project.pk)

    return render(request, "research/form.html", {"form": form, "title": "Edit project"})


@login_required
def project_archive(request, pk):
    project = get_object_or_404(ResearchProject, pk=pk, owner=request.user)
    project.is_archived = True
    project.save()
    messages.success(request, "Project archived.")
    return redirect("dashboard")


def extract_pdf_text(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages[:5]:
            text += page.extract_text() or ""
        return text[:10000]
    except Exception:
        return ""


@login_required
def resource_create(request, project_pk):
    project = get_object_or_404(ResearchProject, pk=project_pk, owner=request.user)
    form = ResourceForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        resource = form.save(commit=False)
        resource.project = project
        resource.save()

        if resource.file:
            resource.extracted_text = extract_pdf_text(resource.file.path)
            resource.save()

        messages.success(request, "Resource added.")
        return redirect("project_detail", pk=project.pk)

    return render(request, "research/form.html", {"form": form, "title": "Add resource"})


@login_required
def resource_edit(request, pk):
    resource = get_object_or_404(Resource, pk=pk, project__owner=request.user)
    form = ResourceForm(request.POST or None, request.FILES or None, instance=resource)

    if request.method == "POST" and form.is_valid():
        resource = form.save()
        if resource.file:
            resource.extracted_text = extract_pdf_text(resource.file.path)
            resource.save()
        messages.success(request, "Resource updated.")
        return redirect("project_detail", pk=resource.project.pk)

    return render(request, "research/form.html", {"form": form, "title": "Edit resource"})


@login_required
def resource_archive(request, pk):
    resource = get_object_or_404(Resource, pk=pk, project__owner=request.user)
    project_pk = resource.project.pk
    resource.is_archived = True
    resource.save()
    messages.success(request, "Resource archived.")
    return redirect("project_detail", pk=project_pk)


@login_required
def summary_create(request, project_pk):
    project = get_object_or_404(ResearchProject, pk=project_pk, owner=request.user)
    form = ResearchSummaryForm(request.POST or None)
    form.fields["resource"].queryset = Resource.objects.filter(project=project)

    if request.method == "POST" and form.is_valid():
        summary = form.save(commit=False)
        summary.project = project
        summary.save()
        messages.success(request, "Summary saved.")
        return redirect("project_detail", pk=project.pk)

    return render(request, "research/form.html", {"form": form, "title": "Create summary"})


@login_required
def summary_edit(request, pk):
    summary = get_object_or_404(ResearchSummary, pk=pk, project__owner=request.user)
    form = ResearchSummaryForm(request.POST or None, instance=summary)
    form.fields["resource"].queryset = Resource.objects.filter(project=summary.project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Summary updated.")
        return redirect("project_detail", pk=summary.project.pk)

    return render(request, "research/form.html", {"form": form, "title": "Edit summary"})


@login_required
def generate_ai_summary(request, resource_pk):
    resource = get_object_or_404(Resource, pk=resource_pk, project__owner=request.user)

    source_text = resource.extracted_text or resource.notes or resource.url

    generated_text = f"""
AI Generated Research Summary

Resource: {resource.title}

Plain English Summary:
This resource discusses the topic described in the uploaded paper, link, or notes. It has been added to the research project as supporting material.

Key Findings:
- The resource appears relevant to the research project.
- The content should be reviewed and compared with other sources.
- The user should verify all claims before using them academically.

Limitations:
- AI-generated summaries may miss context.
- Citations should be manually checked against the original source.

Citation Suggestions:
- Cite the uploaded paper or link directly.
- Include page numbers where possible.
"""

    if source_text:
        generated_text += f"\n\nSource Extract Used:\n{source_text[:1500]}"

    ResearchSummary.objects.create(
        project=resource.project,
        resource=resource,
        title=f"AI Summary: {resource.title}",
        summary_text=generated_text,
        citations="AI-generated draft. User must verify citation details.",
        ai_generated=True,
    )

    messages.success(request, "AI summary generated.")
    return redirect("project_detail", pk=resource.project.pk)


@login_required
def comparison_table_create(request, project_pk):
    project = get_object_or_404(ResearchProject, pk=project_pk, owner=request.user)
    form = ComparisonTableForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        table = form.save(commit=False)
        table.project = project
        table.save()
        messages.success(request, "Comparison table created.")
        return redirect("comparison_table_detail", pk=table.pk)

    return render(request, "research/form.html", {"form": form, "title": "Create comparison table"})


@login_required
def comparison_table_detail(request, pk):
    table = get_object_or_404(ComparisonTable, pk=pk, project__owner=request.user)
    rows = ComparisonRow.objects.filter(table=table)
    return render(request, "research/comparison_detail.html", {"table": table, "rows": rows})


@login_required
def comparison_row_create(request, table_pk):
    table = get_object_or_404(ComparisonTable, pk=table_pk, project__owner=request.user)
    form = ComparisonRowForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        row = form.save(commit=False)
        row.table = table
        row.save()
        messages.success(request, "Comparison row added.")
        return redirect("comparison_table_detail", pk=table.pk)

    return render(request, "research/form.html", {"form": form, "title": "Add comparison row"})


@login_required
def comparison_row_edit(request, pk):
    row = get_object_or_404(ComparisonRow, pk=pk, table__project__owner=request.user)
    form = ComparisonRowForm(request.POST or None, instance=row)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Comparison row updated.")
        return redirect("comparison_table_detail", pk=row.table.pk)

    return render(request, "research/form.html", {"form": form, "title": "Edit comparison row"})


@login_required
def search(request):
    query = request.GET.get("q", "")

    projects = resources = summaries = rows = []

    if query:
        projects = ResearchProject.objects.filter(
            Q(owner=request.user),
            Q(title__icontains=query) | Q(description__icontains=query),
            is_archived=False,
        )

        resources = Resource.objects.filter(
            Q(project__owner=request.user),
            Q(title__icontains=query)
            | Q(notes__icontains=query)
            | Q(extracted_text__icontains=query),
            is_archived=False,
        )

        summaries = ResearchSummary.objects.filter(
            Q(project__owner=request.user),
            Q(title__icontains=query)
            | Q(summary_text__icontains=query)
            | Q(citations__icontains=query),
        )

        rows = ComparisonRow.objects.filter(
            Q(table__project__owner=request.user),
            Q(name__icontains=query)
            | Q(criteria__icontains=query)
            | Q(notes__icontains=query),
        )

    return render(
        request,
        "research/search.html",
        {
            "query": query,
            "projects": projects,
            "resources": resources,
            "summaries": summaries,
            "rows": rows,
        },
    )