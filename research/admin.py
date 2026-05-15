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
    list_display = ("name", "price", "is_archived")
    list_filter = ("is_archived",)
    search_fields = ("name",)
    actions = [archive_plans]
    list_per_page = 10


admin.site.register(UserProfile)
admin.site.register(ResearchProject)
admin.site.register(Resource)
admin.site.register(ResearchSummary)
admin.site.register(ComparisonTable)
admin.site.register(ComparisonRow)