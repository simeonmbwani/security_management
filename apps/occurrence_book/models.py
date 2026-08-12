import uuid
from django.db import models
from django.conf import settings


class OccurrenceBookEntry(models.Model):
    """Digital replacement for the paper Occurrence Book (OB)."""

    class Shift(models.TextChoices):
        DAY = "day", "Day"
        NIGHT = "night", "Night"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry_number = models.CharField(max_length=20, unique=True, editable=False)
    station = models.ForeignKey("accounts.Station", on_delete=models.CASCADE, related_name="ob_entries")
    guard = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ob_entries")
    shift = models.CharField(max_length=10, choices=Shift.choices)
    occurrence = models.TextField(help_text="Incident / occurrence description")
    check_record = models.TextField(blank=True, help_text="Patrol observations e.g. 'Computer Lab locked'")
    location = models.CharField(max_length=150, blank=True)
    signature = models.CharField(max_length=150, blank=True, help_text="Typed/digital signature of the guard")
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ob_reviewed", limit_choices_to={"role__in": ["supervisor", "administrator"]},
    )
    supervisor_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Occurrence Book Entry"
        verbose_name_plural = "Occurrence Book Entries"

    def save(self, *args, **kwargs):
        if not self.entry_number:
            self.entry_number = self._generate_entry_number()
        super().save(*args, **kwargs)

    def _generate_entry_number(self):
        last = OccurrenceBookEntry.objects.order_by("-created_at").first()
        next_seq = 1
        if last and last.entry_number.isdigit():
            next_seq = int(last.entry_number) + 1
        elif OccurrenceBookEntry.objects.count():
            next_seq = OccurrenceBookEntry.objects.count() + 1
        return f"{next_seq:06d}"

    def __str__(self):
        return f"OB {self.entry_number} - {self.station}"


class OccurrenceBookPhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry = models.ForeignKey(OccurrenceBookEntry, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="ob_photos/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
