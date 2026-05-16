from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LoginForm

urlpatterns = [
    path("", views.landing, name="landing"),
    path("register/", views.register, name="register"),

    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html", authentication_form=LoginForm),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path("projects/create/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("projects/<int:pk>/archive/", views.project_archive, name="project_archive"),

    path("projects/<int:project_pk>/resources/create/", views.resource_create, name="resource_create"),
    path("resources/<int:pk>/edit/", views.resource_edit, name="resource_edit"),
    path("resources/<int:pk>/archive/", views.resource_archive, name="resource_archive"),

    path("projects/<int:project_pk>/summaries/create/", views.summary_create, name="summary_create"),
    path("summaries/<int:pk>/edit/", views.summary_edit, name="summary_edit"),
    path("summaries/<int:pk>/archive/", views.summary_archive, name="summary_archive"),
    path("resources/<int:resource_pk>/generate-summary/", views.generate_ai_summary, name="generate_ai_summary"),

    path("projects/<int:project_pk>/comparison/create/", views.comparison_table_create, name="comparison_table_create"),
    path(
        "projects/<int:project_pk>/comparison/ai-generate/",
        views.generate_ai_comparison_table,
        name="generate_ai_comparison_table",
    ),
    path("comparison/<int:pk>/", views.comparison_table_detail, name="comparison_table_detail"),
    path("comparison/<int:pk>/edit/", views.comparison_table_edit, name="comparison_table_edit"),
    path("comparison/<int:pk>/archive/", views.comparison_table_archive, name="comparison_table_archive"),
    path("comparison/<int:table_pk>/rows/create/", views.comparison_row_create, name="comparison_row_create"),
    path("comparison/rows/<int:pk>/edit/", views.comparison_row_edit, name="comparison_row_edit"),
    path("comparison/rows/<int:pk>/archive/", views.comparison_row_archive, name="comparison_row_archive"),

    path("search/", views.search, name="search"),
]