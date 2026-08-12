import uuid
from django.db import models
from django.conf import settings


class IncidentReport(models.Model):
    """Emergency-button style incident report with immediate supervisor alert."""

    class IncidentType(models.TextChoices):
        FIRE = "fire", "Fire"
        BREAK_IN = "break_in", "Break-in"
        VIOLENCE = "violence", "Violence"
        MEDICAL = "medical", "Medical"
        ELECTRIC_FAULT = "electric_fault", "Electric Fault"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey("accounts.Station", on_delete=models.CASCADE, related_name="incidents")
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="incidents_reported")
    incident_type = models.CharField(max_length=20, choices=IncidentType.choices)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="incidents_acknowledged",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_incident_type_display()} @ {self.station} - {self.created_at:%Y-%m-%d %H:%M}"


class IncidentMedia(models.Model):
    class MediaType(models.TextChoices):
        PHOTO = "photo", "Photo"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident = models.ForeignKey(IncidentReport, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    file = models.FileField(upload_to="incident_media/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
