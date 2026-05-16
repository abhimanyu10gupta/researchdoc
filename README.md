# ResearchDoc (Django)

ResearchDoc is a university Web Information Systems project: a Django + Bootstrap 5 app for managing research projects, resources (PDF/link/note), summaries with structured citations, comparison tables, and search — with an optional GenAI summary generator.

## Setup (uv)

Create a virtual environment and install dependencies:

```bash
cd researchdoc
uv sync
```

Run migrations:

```bash
uv run python manage.py migrate
```

Start the dev server:

```bash
uv run python manage.py runserver
```

## Demo data

Seed demo data (safe to run multiple times):

```bash
uv run python manage.py seed_demo
```

Demo accounts:
- **Normal user**: `demo_user` / `DemoPass123!`
- **Second user**: `other_user` / `DemoPass123!`
- **Admin/staff**: `admin` / `AdminPass123!`

## Key features (rubric-aligned)

- **Landing page**: marketing-style landing with login/register CTAs
- **Auth**: register, login, logout
- **Roles**
  - Normal users manage only their own projects/resources/summaries/comparisons
  - Staff/admin can manage subscription plans in Django admin
- **Subscription plans**: create/list/edit/archive in admin (pagination enabled)
- **Research projects**: create/edit/archive + dashboard
- **Resources**: create/edit/archive for PDFs/links/notes
  - PDF extraction via `pypdf` (first few pages; safe fallback on failure)
- **Summaries**: create/edit/archive with structured citation fields
- **Comparison tables**: create/edit/archive and editable rows (archive per row)
- **Search**: basic search across projects, resources, summaries, and comparison rows (grouped results)
- **GenAI summary generation**: optional (uses API key if present; otherwise simulated demo output)
- **Responsible AI warning**: shown on AI-generated summaries

## Models (overview)

All user-owned data is linked back to a project owned by a user:

- `SubscriptionPlan`: admin-managed plans (`is_archived` instead of hard-delete)
- `UserProfile`: per-user role and subscription plan
- `ResearchProject`: owned by user; `status`; archived via `is_archived`
- `Resource`: belongs to a project; PDF/link/note; stores `extracted_text`
- `ResearchSummary`: belongs to a project (optionally linked to a resource); structured citation fields
- `ComparisonTable`: belongs to a project
- `ComparisonRow`: belongs to a table

## Security / ownership checks

All “detail/edit/archive” endpoints query through ownership relationships (e.g. `project__owner=request.user`).  
If a user guesses another user’s URL, they receive a **404** (not “permission denied”), preventing data leakage.

Key pattern used throughout:
- Project: `get_object_or_404(ResearchProject, owner=request.user, …)`
- Resource: `get_object_or_404(Resource, project__owner=request.user, …)`
- Summary: `get_object_or_404(ResearchSummary, project__owner=request.user, …)`
- Comparison table/row: `… table__project__owner=request.user …`

Archived items (`is_archived=True`) are hidden from dashboard/search and treated as non-existent in most views.

## GenAI usage (declaration)

ResearchDoc can generate a draft research summary for a resource.

- **Environment variables**
  - `OPENAI_API_KEY` (preferred) or `OPENROUTER_API_KEY`
  - `AI_MODEL` (optional)
- **No key? No crash**: the app creates a clearly-marked **simulated** summary so demos work offline.
- **Responsible AI**: AI-generated summaries display a warning:  
  **“AI-generated content must be reviewed and verified before academic use.”**

## Deployment prep (Render-friendly)

`config/settings.py` supports these env vars:

- `DEBUG`: `true/false`
- `SECRET_KEY`: set in production
- `ALLOWED_HOSTS`: comma-separated (e.g. `your-app.onrender.com`)
- `CSRF_TRUSTED_ORIGINS`: comma-separated (e.g. `https://your-app.onrender.com`)

Static/media:
- `STATIC_ROOT` is set to `staticfiles/`
- In production, run:

```bash
uv run python manage.py collectstatic --noinput
```

## Admin

Create a superuser manually (optional if you use `seed_demo`):

```bash
uv run python manage.py createsuperuser
```

Then open `/admin/` and manage:
- Subscription plans (archive action + pagination)
- Users / profiles
- Projects / resources / summaries / comparison tables/rows

