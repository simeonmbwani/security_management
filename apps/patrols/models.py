import uuid
from django.db import models
from django.conf import settings


class Checkpoint(models.Model):
    """A fixed point guards must visit during a patrol, e.g. 'Main Gate'."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey("accounts.Station", on_delete=models.CASCADE, related_name="checkpoints")
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["station", "order"]

    def __str__(self):
        return f"{self.station} - {self.name}"


class Patrol(models.Model):
    """One patrol round: Start Patrol -> visit checkpoints -> Finish Patrol."""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        OVERDUE = "overdue", "Overdue"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey("accounts.Station", on_delete=models.CASCADE, related_name="patrols")
    guard = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patrols")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.IN_PROGRESS)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Patrol by {self.guard} @ {self.started_at:%Y-%m-%d %H:%M}"


class PatrolCheckpointLog(models.Model):
    """Record of a guard visiting a specific checkpoint during a patrol."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patrol = models.ForeignKey(Patrol, on_delete=models.CASCADE, related_name="logs")
    checkpoint = models.ForeignKey(Checkpoint, on_delete=models.CASCADE, related_name="visit_logs")
    visited_at = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    comment = models.CharField(max_length=255, blank=True, help_text="e.g. 'Locked', 'Window open'")
    photo = models.ImageField(upload_to="patrol_photos/%Y/%m/", null=True, blank=True)
    is_flagged = models.BooleanField(default=False, help_text="Something needs attention here")

    class Meta:
        ordering = ["visited_at"]

    def __str__(self):
        return f"{self.checkpoint} @ {self.visited_at:%H:%M}"
