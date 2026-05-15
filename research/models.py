from django.db import models
from django.contrib.auth.models import User


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("admin", "Admin"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.user.username} profile"


class ResearchProject(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Resource(models.Model):
    RESOURCE_TYPES = [
        ("pdf", "PDF"),
        ("link", "Link"),
        ("note", "Note"),
    ]

    project = models.ForeignKey(ResearchProject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    file = models.FileField(upload_to="papers/", blank=True, null=True)
    url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    extracted_text = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ResearchSummary(models.Model):
    project = models.ForeignKey(ResearchProject, on_delete=models.CASCADE)
    resource = models.ForeignKey(
        Resource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    summary_text = models.TextField()
    citations = models.TextField(blank=True)
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ComparisonTable(models.Model):
    project = models.ForeignKey(ResearchProject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class ComparisonRow(models.Model):
    table = models.ForeignKey(ComparisonTable, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    criteria = models.CharField(max_length=200)
    score = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name