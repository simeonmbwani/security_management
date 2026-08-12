import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string


class User(AbstractUser):
    """
    Custom user. Username is kept (for Django admin convenience) but the
    system logs guards in with their employee number via a custom
    authentication backend-friendly serializer (see serializers.py).
    """

    class Role(models.TextChoices):
        ADMINISTRATOR = "administrator", "Administrator"
        SUPERVISOR = "supervisor", "Security Supervisor"
        GUARD = "guard", "Security Guard"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.GUARD)
    employee_number = models.CharField(max_length=32, unique=True)
    phone = models.CharField(max_length=32, blank=True)
    is_active_employee = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.employee_number:
            base = (self.username or self.get_full_name() or 'user').replace(' ', '').lower()
            prefix = ''.join(ch for ch in base if ch.isalnum())[:8] or 'user'
            self.employee_number = f"{prefix}-{get_random_string(4, '0123456789')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.employee_number})"


class Station(models.Model):
    """A physical site/campus the system manages (supports multi-campus)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class GuardProfile(models.Model):
    """Extra HR/employment data for guards and supervisors."""

    class Rank(models.TextChoices):
        GUARD = "guard", "Security Guard"
        SENIOR_GUARD = "senior_guard", "Senior Security Guard"
        SUPERVISOR = "supervisor", "Security Supervisor"
        CHIEF_SUPERVISOR = "chief_supervisor", "Chief Supervisor"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="guard_profile")
    station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, related_name="guards")
    rank = models.CharField(max_length=30, choices=Rank.choices, default=Rank.GUARD)
    date_employed = models.DateField()
    national_id = models.CharField(max_length=32, blank=True)
    next_of_kin = models.CharField(max_length=150, blank=True)
    next_of_kin_phone = models.CharField(max_length=32, blank=True)
    photo = models.ImageField(upload_to="guard_photos/", null=True, blank=True)
    is_on_escort_duty = models.BooleanField(default=False)  # locked while on vehicle escort

    def __str__(self):
        return f"Profile: {self.user}"
