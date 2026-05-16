from django.contrib import admin
from .models import (
    SubscriptionPlan,
    UserProfile,
    ResearchProject,
    Resource,
    ResearchSummary,
    ComparisonTable,
    ComparisonRow,
)


@admin.action(description="Archive selected subscription plans")
def archive_plans(modeladmin, request, queryset):
    queryset.update(is_archived=True)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "is_archived", "created_at", "updated_at")
    list_filter = ("is_archived",)
    search_fields = ("name", "description")
    actions = [archive_plans]
    list_per_page = 10

    def has_delete_permission(self, request, obj=None):
        # Prefer archive instead of hard-delete for subscription plans.
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "subscription_plan")
    search_fields = ("user__username", "user__email")
    list_filter = ("role", "subscription_plan")
    list_per_page = 25


@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "is_archived", "created_at", "updated_at")
    search_fields = ("title", "description", "owner__username", "owner__email")
    list_filter = ("status", "is_archived", "created_at")
    list_per_page = 25


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "resource_type", "is_archived", "created_at", "updated_at")
    search_fields = ("title", "url", "notes", "extracted_text", "project__title", "project__owner__username")
    list_filter = ("resource_type", "is_archived", "created_at")
    list_per_page = 25


@admin.register(ResearchSummary)
class ResearchSummaryAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "resource", "ai_generated", "is_archived", "created_at", "updated_at")
    search_fields = (
        "title",
        "summary_text",
        "citation_source",
        "citation_page",
        "citation_quote",
        "project__title",
        "project__owner__username",
    )
    list_filter = ("ai_generated", "is_archived", "created_at")
    list_per_page = 25


@admin.register(ComparisonTable)
class ComparisonTableAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "is_archived", "created_at", "updated_at")
    search_fields = ("title", "project__title", "project__owner__username")
    list_filter = ("is_archived", "created_at")
    list_per_page = 25


@admin.register(ComparisonRow)
class ComparisonRowAdmin(admin.ModelAdmin):
    list_display = ("name", "table", "score", "is_archived", "created_at", "updated_at")
    search_fields = ("name", "criteria", "notes", "table__title", "table__project__title", "table__project__owner__username")
    list_filter = ("is_archived", "created_at")
    list_per_page = 25