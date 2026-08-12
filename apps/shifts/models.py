import uuid
from django.db import models
from django.conf import settings


class GuardPair(models.Model):
    """Two guards who rotate day/night duty together on the 4-day cycle."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey("accounts.Station", on_delete=models.CASCADE, related_name="pairs")
    name = models.CharField(max_length=50, help_text="e.g. Pair 1")
    guard_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pair_as_a"
    )
    guard_b = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pair_as_b"
    )
    rotation_order = models.PositiveIntegerField(help_text="Order this pair rotates in, 1 = first")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["station", "rotation_order"]
        unique_together = ("station", "rotation_order")

    def __str__(self):
        return f"{self.name} ({self.guard_a} + {self.guard_b})"


class DutyRosterCycle(models.Model):
    """
    Anchors the rotation: 'cycle_start_date' is day 1 of pair #1's block.
    The shift engine (services.py) uses this to compute who is on duty,
    and on which shift, for any given date.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.OneToOneField("accounts.Station", on_delete=models.CASCADE, related_name="roster_cycle")
    cycle_start_date = models.DateField()
    cycle_length_days = models.PositiveIntegerField(default=4)

    def __str__(self):
        return f"Roster cycle for {self.station} starting {self.cycle_start_date}"


class Shift(models.Model):
    """A single concrete shift assignment on a given date."""

    class ShiftType(models.TextChoices):
        DAY = "day", "Day"
        NIGHT = "night", "Night"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey("accounts.Station", on_delete=models.CASCADE, related_name="shifts")
    guard = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shifts")
    date = models.DateField()
    shift_type = models.CharField(max_length=10, choices=ShiftType.choices)
    pair = models.ForeignKey(GuardPair, on_delete=models.SET_NULL, null=True, related_name="shifts")
    is_override = models.BooleanField(default=False, help_text="Manually overridden, e.g. for exam duty")
    override_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("station", "guard", "date", "shift_type")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.guard} - {self.date} ({self.shift_type})"


class ShiftHandover(models.Model):
    """End-of-shift handover between outgoing and incoming guard."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    outgoing_shift = models.OneToOneField(Shift, on_delete=models.CASCADE, related_name="handover")
    incoming_guard = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="handovers_received"
    )
    occurrence_summary = models.TextField(blank=True)
    equipment_issued = models.TextField(blank=True)
    keys_handed_over = models.TextField(blank=True)
    pending_issues = models.TextField(blank=True)
    outgoing_signed = models.BooleanField(default=False)
    incoming_accepted = models.BooleanField(default=False)
    incoming_accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Handover {self.outgoing_shift} -> {self.incoming_guard}"


class Attendance(models.Model):
    """Clock-in / clock-out record tied to a shift."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift = models.OneToOneField(Shift, on_delete=models.CASCADE, related_name="attendance")
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    clock_in_gps = models.CharField(max_length=64, blank=True)
    clock_out_gps = models.CharField(max_length=64, blank=True)
    is_late = models.BooleanField(default=False)
    is_absent = models.BooleanField(default=False)

    def __str__(self):
        return f"Attendance {self.shift}"
