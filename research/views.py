import json
import os
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from pypdf import PdfReader
from openai import OpenAI

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
    if request.user.is_authenticated:
        return redirect("dashboard")

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
    projects = ResearchProject.objects.filter(owner=request.user, is_archived=False).order_by("-updated_at")

    stats = {
        "projects": projects.count(),
        "resources": Resource.objects.filter(project__owner=request.user, is_archived=False).count(),
        "summaries": ResearchSummary.objects.filter(project__owner=request.user, is_archived=False).count(),
        "tables": ComparisonTable.objects.filter(project__owner=request.user, is_archived=False).count(),
    }

    return render(request, "research/dashboard.html", {"projects": projects, "stats": stats})


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
    summaries = ResearchSummary.objects.filter(project=project, is_archived=False).order_by("-updated_at")
    tables = ComparisonTable.objects.filter(project=project, is_archived=False).order_by("-updated_at")

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
    project = get_object_or_404(ResearchProject, pk=pk, owner=request.user, is_archived=False)
    form = ResearchProjectForm(request.POST or None, instance=project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project updated.")
        return redirect("project_detail", pk=project.pk)

    return render(request, "research/form.html", {"form": form, "title": "Edit project"})


@login_required
@require_http_methods(["GET", "POST"])
def project_archive(request, pk):
    project = get_object_or_404(ResearchProject, pk=pk, owner=request.user, is_archived=False)
    if request.method == "POST":
        project.is_archived = True
        project.save(update_fields=["is_archived", "updated_at"])
        messages.success(request, "Project archived.")
        return redirect("dashboard")
    return render(
        request,
        "research/confirm_archive.html",
        {"title": "Archive project", "object_name": project.title, "cancel_url": reverse("project_detail", kwargs={"pk": project.pk})},
    )


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
    project = get_object_or_404(ResearchProject, pk=project_pk, owner=request.user, is_archived=False)
    form = ResourceForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        resource = form.save(commit=False)
        resource.project = project
        resource.save()

        if resource.file and resource.resource_type == "pdf":
            resource.extracted_text = extract_pdf_text(resource.file.path)
            resource.save()

        messages.success(request, "Resource added.")
        return redirect("project_detail", pk=project.pk)

    return render(request, "research/form.html", {"form": form, "title": "Add resource"})


@login_required
def resource_edit(request, pk):
    resource = get_object_or_404(Resource, pk=pk, project__owner=request.user, is_archived=False, project__is_archived=False)
    form = ResourceForm(request.POST or None, request.FILES or None, instance=resource)

    if request.method == "POST" and form.is_valid():
        resource = form.save()
        if resource.file and resource.resource_type == "pdf":
            resource.extracted_text = extract_pdf_text(resource.file.path)
            resource.save()
        messages.success(request, "Resource updated.")
        return redirect("project_detail", pk=resource.project.pk)

    return render(request, "research/form.html", {"form": form, "title": "Edit resource"})


@login_required
@require_http_methods(["GET", "POST"])
def resource_archive(request, pk):
    resource = get_object_or_404(Resource, pk=pk, project__owner=request.user, is_archived=False)
    if request.method == "POST":
        project_pk = resource.project.pk
        resource.is_archived = True
        resource.save(update_fields=["is_archived", "updated_at"])
        messages.success(request, "Resource archived.")
        return redirect("project_detail", pk=project_pk)
    return render(
        request,
        "research/confirm_archive.html",
        {"title": "Archive resource", "object_name": resource.title, "cancel_url": reverse("project_detail", kwargs={"pk": resource.project.pk})},
    )


@login_required
def summary_create(request, project_pk):
    project = get_object_or_404(ResearchProject, pk=project_pk, owner=request.user, is_archived=False)
    form = ResearchSummaryForm(request.POST or None)
    form.fields["resource"].queryset = Resource.objects.filter(project=project, is_archived=False)

    if request.method == "POST" and form.is_valid():
        summary = form.save(commit=False)
        summary.project = project
        summary.save()
        messages.success(request, "Summary saved.")
        return redirect("project_detail", pk=project.pk)

    return render(request, "research/form.html", {"form": form, "title": "Create summary"})


@login_required
def summary_edit(request, pk):
    summary = get_object_or_404(ResearchSummary, pk=pk, project__owner=request.user, is_archived=False)
    form = ResearchSummaryForm(request.POST or None, instance=summary)
    form.fields["resource"].queryset = Resource.objects.filter(project=summary.project, is_archived=False)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Summary updated.")
        return redirect("project_detail", pk=summary.project.pk)

    return render(request, "research/form.html", {"form": form, "title": "Edit summary"})


@login_required
@require_http_methods(["POST"])
def generate_ai_summary(request, resource_pk):
    resource = get_object_or_404(
        Resource,
        pk=resource_pk,
        project__owner=request.user,
        is_archived=False,
        project__is_archived=False,
    )

    source_text = (resource.extracted_text or resource.notes or resource.url or "").strip()
    source_text = source_text[:8000]

    generated_text = generate_ai_summary_text(resource_title=resource.title, source_text=source_text)

    citation_source = ""
    if resource.url:
        citation_source = resource.url
    elif resource.file:
        citation_source = resource.file.name
    else:
        citation_source = resource.title

    ResearchSummary.objects.create(
        project=resource.project,
        resource=resource,
        title=f"AI Summary: {resource.title}",
        summary_text=generated_text,
        citation_source=citation_source,
        citation_page="",
        citation_quote="",
        ai_generated=True,
    )

    messages.success(request, "AI summary generated.")
    return redirect("project_detail", pk=resource.project.pk)


def generate_ai_summary_text(*, resource_title: str, source_text: str) -> str:
    warning = "AI-generated content must be reviewed and verified before academic use."

    if not source_text:
        source_text = "No extracted text was available. Use your own notes and the original source to verify details."

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "").strip()

    if openai_key:
        client = OpenAI(api_key=openai_key)
        model = model or "gpt-4o-mini"
    elif openrouter_key:
        client = OpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1")
        model = model or "openai/gpt-4o-mini"
    else:
        return f"""## AI Research Summary (Simulated)

**Warning:** {warning}

### Plain English summary
This is a simulated AI summary (no API key configured). It gives a safe, demo-friendly structure you can replace with a real model output later.

### Key findings
- The resource appears relevant to your project, but claims must be verified in the original source.
- Pull out 2–3 direct quotes and record exact page numbers for academic use.

### Limitations
- No model was called, so this summary may be generic.
- PDF extraction may be incomplete (especially for scanned PDFs).

### Suggested citation points
- Cite the resource title/URL and add page numbers for any quoted claims.
- Add a short quote in your citation fields to support key findings.

### Responsible AI note
{warning}
"""

    prompt = f"""You are an assistant helping a university student write a research summary.
Return a structured summary with the following exact sections:

1) Plain English summary (3-6 bullet points)
2) Key findings (5-8 bullet points)
3) Limitations (3-6 bullet points)
4) Suggested citation points (3-6 bullet points, include what to cite and where to look for page numbers)
5) Responsible AI note (1-2 sentences, include the warning: "{warning}")

Be careful: do not invent page numbers, quotes, or sources. If details are missing, say what the user should verify.

Resource title: {resource_title}

Source text (may be partial):
{source_text}
"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You write accurate, cautious academic summaries."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = (resp.choices[0].message.content or "").strip()
        if not content:
            raise ValueError("Empty AI response")
        return content
    except Exception:
        return f"""## AI Research Summary (Fallback)

**Warning:** {warning}

### Plain English summary
- The AI service was unavailable or misconfigured, so this is a safe fallback.
- Use the resource itself to confirm all claims before academic use.

### Key findings
- Identify the main claim(s) and supporting evidence in the source.
- Extract 1–2 direct quotes and record page numbers.

### Limitations
- AI generation failed; this output is generic.
- PDF extraction may be incomplete.

### Suggested citation points
- Cite the original paper/link directly and add page numbers where you quote it.
- Record a short quote in `citation_quote`.

### Responsible AI note
{warning}
"""


def generate_ai_comparison_rows(*, project_title: str, resources: list[dict]) -> dict[int, dict]:
    """
    Returns a mapping of resource idx -> {criteria, score, notes}.
    Uses OpenAI/OpenRouter when configured; otherwise returns a safe fallback.
    """

    warning = "AI-generated comparisons must be reviewed and verified before academic use."

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "").strip()

    if openai_key:
        client = OpenAI(api_key=openai_key)
        model = model or "gpt-4o-mini"
    elif openrouter_key:
        client = OpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1")
        model = model or "openai/gpt-4o-mini"
    else:
        return {
            r["idx"]: {
                "criteria": f"{r.get('resource_type', 'source')} • topic/value: verify from notes/text",
                "score": 6,
                "notes": (
                    "Fallback comparison row (no API key configured).\n\n"
                    "Strengths: Easy to add to your project; provides a starting point for manual comparison.\n"
                    "Weaknesses: Generic until you verify details in the original source.\n"
                    "Citation/usefulness: Record exact quotes and page/section locations before academic use.\n\n"
                    f"Responsible AI: {warning}"
                ),
            }
            for r in resources
        }

    # Keep the payload small and demo-friendly.
    compact_resources = []
    for r in resources:
        extracted = (r.get("extracted_text") or "").strip()
        notes = (r.get("notes") or "").strip()
        compact_resources.append(
            {
                "idx": r["idx"],
                "title": (r.get("title") or "")[:200],
                "resource_type": r.get("resource_type") or "",
                "url": (r.get("url") or "")[:400],
                "notes": notes[:800],
                "extracted_text": extracted[:1200],
            }
        )

    prompt = f"""You are helping a university student compare research resources inside a project.

Project title: {project_title}

Given the resources below, create ONE comparison row per resource.

Return STRICT JSON only: a JSON array of objects with keys:
- idx (integer, must match input)
- criteria (string: method/topic/source type/key value; max 200 chars)
- score (integer 1-10)
- notes (string: include strengths, weaknesses, and citation/usefulness comments; include the warning: "{warning}")

Rules:
- Do NOT invent citations, page numbers, or quotes.
- If details are missing, say what to verify.
- Keep notes concise but helpful (3-7 bullet points is fine).

Input resources:
{json.dumps(compact_resources, ensure_ascii=False)}
"""

    def parse_model_json(text: str):
        """
        OpenRouter/model outputs can include Markdown fences or extra prose.
        Try multiple candidates until we can parse the JSON we asked for.
        """

        def extract_fenced_blocks(s: str) -> list[str]:
            return [m.group(1).strip() for m in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", s or "", re.IGNORECASE)]

        def iter_balanced_substrings(s: str, open_ch: str, close_ch: str):
            if not s:
                return
            n = len(s)
            for i in range(n):
                if s[i] != open_ch:
                    continue
                depth = 0
                for j in range(i, n):
                    ch = s[j]
                    if ch == open_ch:
                        depth += 1
                    elif ch == close_ch:
                        depth -= 1
                        if depth == 0:
                            yield s[i : j + 1].strip()
                            break

        raw = (text or "").strip()
        candidates: list[str] = []
        if raw:
            candidates.append(raw)
            candidates.extend(extract_fenced_blocks(raw))
            candidates.extend(iter_balanced_substrings(raw, "[", "]"))
            candidates.extend(iter_balanced_substrings(raw, "{", "}"))

        for cand in candidates:
            if not cand:
                continue
            try:
                parsed = json.loads(cand)
            except Exception:
                continue

            # Preferred: JSON array of row objects
            if isinstance(parsed, list):
                return parsed

            # Common fallback: JSON object wrapper like {"rows": [...]}
            if isinstance(parsed, dict):
                rows = parsed.get("rows") or parsed.get("data") or parsed.get("items")
                if isinstance(rows, list):
                    return rows

        raise ValueError("No parseable JSON found in model output")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You write accurate, cautious comparisons for academic work."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = (resp.choices[0].message.content or "").strip()
        parsed = parse_model_json(content)
        result: dict[int, dict] = {}
        if isinstance(parsed, list):
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                idx = item.get("idx", item.get("id"))
                if isinstance(idx, str):
                    idx = idx.strip()
                    if idx.isdigit():
                        idx = int(idx)
                elif isinstance(idx, float):
                    idx = int(idx)
                if not isinstance(idx, int):
                    continue
                result[idx] = {
                    "criteria": str(item.get("criteria", ""))[:200],
                    "score": item.get("score", 6),
                    "notes": str(item.get("notes", "")),
                }

        # If parsing gave nothing useful, fall back.
        if not result:
            raise ValueError("AI response JSON did not parse into rows")
        return result
    except Exception:
        return {
            r["idx"]: {
                "criteria": f"{r.get('resource_type', 'source')} • topic/value: verify from notes/text",
                "score": 6,
                "notes": (
                    "Fallback comparison row (AI call failed).\n\n"
                    "Strengths: Provides a structured starting point for comparing items.\n"
                    "Weaknesses: Generic until verified against the original source.\n"
                    "Citation/usefulness: Add exact quotes and page/section locations manually.\n\n"
                    f"Responsible AI: {warning}"
                ),
            }
            for r in resources
        }


@login_required
@require_http_methods(["POST"])
def generate_ai_comparison_table(request, project_pk):
    project = get_object_or_404(ResearchProject, pk=project_pk, owner=request.user, is_archived=False)
    resources_qs = Resource.objects.filter(project=project, is_archived=False).order_by("id")
    resources = list(resources_qs)

    if len(resources) < 2:
        messages.error(request, "Add at least two active resources before generating an AI comparison table.")
        return redirect("project_detail", pk=project.pk)

    payload = [
        {
            "idx": r.pk,
            "title": r.title,
            "resource_type": r.resource_type,
            "url": r.url,
            "notes": r.notes,
            "extracted_text": r.extracted_text,
        }
        for r in resources
    ]

    ai_rows = generate_ai_comparison_rows(project_title=project.title, resources=payload)

    table = ComparisonTable.objects.create(project=project, title=f"AI Comparison: {project.title}")

    for r in resources:
        row_data = ai_rows.get(r.pk) or {}
        criteria = (row_data.get("criteria") or f"{r.resource_type} • topic/value: verify").strip()[:200]
        notes = (row_data.get("notes") or "").strip()
        score_val = row_data.get("score", 6)
        try:
            score = int(score_val)
        except Exception:
            score = 6
        score = max(1, min(10, score))

        ComparisonRow.objects.create(
            table=table,
            name=(r.title or "Resource")[:200],
            criteria=criteria or "Topic/method/value: verify from source",
            score=score,
            notes=notes or "AI comparison notes were unavailable. Please compare manually and add citations.",
        )

    messages.success(request, "AI comparison table generated.")
    return redirect("comparison_table_detail", pk=table.pk)


@login_required
def comparison_table_create(request, project_pk):
    project = get_object_or_404(ResearchProject, pk=project_pk, owner=request.user, is_archived=False)
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
    table = get_object_or_404(ComparisonTable, pk=pk, project__owner=request.user, is_archived=False, project__is_archived=False)
    rows = ComparisonRow.objects.filter(table=table, is_archived=False).order_by("-updated_at")
    return render(request, "research/comparison_detail.html", {"table": table, "rows": rows})


@login_required
def comparison_row_create(request, table_pk):
    table = get_object_or_404(ComparisonTable, pk=table_pk, project__owner=request.user, is_archived=False)
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
    row = get_object_or_404(ComparisonRow, pk=pk, table__project__owner=request.user, is_archived=False, table__is_archived=False)
    form = ComparisonRowForm(request.POST or None, instance=row)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Comparison row updated.")
        return redirect("comparison_table_detail", pk=row.table.pk)

    return render(request, "research/form.html", {"form": form, "title": "Edit comparison row"})


@login_required
@require_http_methods(["GET", "POST"])
def summary_archive(request, pk):
    summary = get_object_or_404(ResearchSummary, pk=pk, project__owner=request.user, is_archived=False)
    if request.method == "POST":
        summary.is_archived = True
        summary.save(update_fields=["is_archived", "updated_at"])
        messages.success(request, "Summary archived.")
        return redirect("project_detail", pk=summary.project.pk)
    return render(
        request,
        "research/confirm_archive.html",
        {"title": "Archive summary", "object_name": summary.title, "cancel_url": reverse("project_detail", kwargs={"pk": summary.project.pk})},
    )


@login_required
def comparison_table_edit(request, pk):
    table = get_object_or_404(ComparisonTable, pk=pk, project__owner=request.user, is_archived=False)
    form = ComparisonTableForm(request.POST or None, instance=table)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Comparison table updated.")
        return redirect("comparison_table_detail", pk=table.pk)
    return render(request, "research/form.html", {"form": form, "title": "Edit comparison table"})


@login_required
@require_http_methods(["GET", "POST"])
def comparison_table_archive(request, pk):
    table = get_object_or_404(ComparisonTable, pk=pk, project__owner=request.user, is_archived=False)
    if request.method == "POST":
        table.is_archived = True
        table.save(update_fields=["is_archived", "updated_at"])
        messages.success(request, "Comparison table archived.")
        return redirect("project_detail", pk=table.project.pk)
    return render(
        request,
        "research/confirm_archive.html",
        {"title": "Archive comparison table", "object_name": table.title, "cancel_url": reverse("comparison_table_detail", kwargs={"pk": table.pk})},
    )


@login_required
@require_http_methods(["GET", "POST"])
def comparison_row_archive(request, pk):
    row = get_object_or_404(ComparisonRow, pk=pk, table__project__owner=request.user, is_archived=False)
    if request.method == "POST":
        row.is_archived = True
        row.save(update_fields=["is_archived", "updated_at"])
        messages.success(request, "Comparison row archived.")
        return redirect("comparison_table_detail", pk=row.table.pk)
    return render(
        request,
        "research/confirm_archive.html",
        {"title": "Archive comparison row", "object_name": row.name, "cancel_url": reverse("comparison_table_detail", kwargs={"pk": row.table.pk})},
    )

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
            | Q(citation_source__icontains=query)
            | Q(citation_page__icontains=query)
            | Q(citation_quote__icontains=query),
            is_archived=False,
        )

        rows = ComparisonRow.objects.filter(
            Q(table__project__owner=request.user),
            Q(name__icontains=query)
            | Q(criteria__icontains=query)
            | Q(notes__icontains=query),
            is_archived=False,
            table__is_archived=False,
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