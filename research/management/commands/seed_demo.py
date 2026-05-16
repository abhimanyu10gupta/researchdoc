from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from research.models import (
    ComparisonRow,
    ComparisonTable,
    ResearchProject,
    ResearchSummary,
    Resource,
    SubscriptionPlan,
    UserProfile,
)


class Command(BaseCommand):
    help = "Seed demo data for ResearchDoc (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data…")

        free, _ = SubscriptionPlan.objects.get_or_create(
            name="Free",
            defaults={"price": 0, "description": "Starter plan for students."},
        )
        pro, _ = SubscriptionPlan.objects.get_or_create(
            name="Pro",
            defaults={"price": 9.99, "description": "For serious research workflows."},
        )
        ent, _ = SubscriptionPlan.objects.get_or_create(
            name="Enterprise",
            defaults={"price": 49.99, "description": "For teams and advanced needs."},
        )
        SubscriptionPlan.objects.filter(name__in=["Free", "Pro", "Enterprise"]).update(is_archived=False)

        User = get_user_model()

        demo_user = self._get_or_create_user(User, "demo_user", "DemoPass123!", is_staff=False, is_superuser=False)
        other_user = self._get_or_create_user(User, "other_user", "DemoPass123!", is_staff=False, is_superuser=False)
        admin_user = self._get_or_create_user(User, "admin", "AdminPass123!", is_staff=True, is_superuser=True)

        self._ensure_profile(demo_user, role="user", plan=free)
        self._ensure_profile(other_user, role="user", plan=free)
        self._ensure_profile(admin_user, role="admin", plan=ent)

        project, _ = ResearchProject.objects.get_or_create(
            owner=demo_user,
            title="Sample Research Project",
            defaults={
                "description": "A demo project seeded for marking: resources, summaries, comparisons, and search.",
                "status": "active",
            },
        )
        if project.is_archived:
            project.is_archived = False
            project.save(update_fields=["is_archived", "updated_at"])

        resource, _ = Resource.objects.get_or_create(
            project=project,
            title="Example SaaS Vendor Website",
            defaults={
                "resource_type": "link",
                "url": "https://example.com",
                "notes": "Vendor homepage. Capture pricing, features, and security claims; verify against docs.",
                "extracted_text": "",
            },
        )
        if resource.is_archived:
            resource.is_archived = False
            resource.save(update_fields=["is_archived", "updated_at"])

        summary, created = ResearchSummary.objects.get_or_create(
            project=project,
            title="Sample Summary (with citation fields)",
            defaults={
                "resource": resource,
                "summary_text": (
                    "This is seeded demo content. Replace with your own summary after reading the source.\n\n"
                    "Key idea: keep citations structured (source, page/location, quote) for academic integrity."
                ),
                "citation_source": resource.url,
                "citation_page": "N/A (web)",
                "citation_quote": "Add an exact quote here after verifying the source.",
                "ai_generated": False,
            },
        )
        if not created and summary.is_archived:
            summary.is_archived = False
            summary.save(update_fields=["is_archived", "updated_at"])

        table, _ = ComparisonTable.objects.get_or_create(
            project=project,
            title="SaaS Comparison Table (Demo)",
        )
        if table.is_archived:
            table.is_archived = False
            table.save(update_fields=["is_archived", "updated_at"])

        self._get_or_create_row(table, "Vendor A", "Security", 8, "Good SSO and audit logs (verify in docs).")
        self._get_or_create_row(table, "Vendor B", "Pricing", 6, "Cheaper entry tier but fewer features.")
        self._get_or_create_row(table, "Vendor C", "Usability", 7, "Clean UI; check mobile experience.")

        # A second user's project to help demonstrate ownership/404 checks.
        other_project, _ = ResearchProject.objects.get_or_create(
            owner=other_user,
            title="Other User Private Project",
            defaults={"description": "This should not be accessible by demo_user.", "status": "active"},
        )
        if other_project.is_archived:
            other_project.is_archived = False
            other_project.save(update_fields=["is_archived", "updated_at"])

        self.stdout.write(self.style.SUCCESS("Demo data ready."))

    def _get_or_create_user(self, User, username, password, *, is_staff, is_superuser):
        user, created = User.objects.get_or_create(username=username, defaults={"is_staff": is_staff, "is_superuser": is_superuser})
        if not created:
            changed = False
            if user.is_staff != is_staff:
                user.is_staff = is_staff
                changed = True
            if user.is_superuser != is_superuser:
                user.is_superuser = is_superuser
                changed = True
            if changed:
                user.save(update_fields=["is_staff", "is_superuser"])

        user.set_password(password)
        user.save(update_fields=["password"])
        return user

    def _ensure_profile(self, user, *, role, plan):
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role": role, "subscription_plan": plan})
        updates = []
        if profile.role != role:
            profile.role = role
            updates.append("role")
        if profile.subscription_plan_id != plan.id:
            profile.subscription_plan = plan
            updates.append("subscription_plan")
        if updates:
            profile.save(update_fields=updates)

    def _get_or_create_row(self, table, name, criteria, score, notes):
        row, _ = ComparisonRow.objects.get_or_create(
            table=table,
            name=name,
            defaults={"criteria": criteria, "score": score, "notes": notes},
        )
        if row.is_archived:
            row.is_archived = False
            row.save(update_fields=["is_archived", "updated_at"])
        return row

