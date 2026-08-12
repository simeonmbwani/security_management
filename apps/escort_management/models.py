import uuid
from django.db import models
from django.conf import settings


class EscortMission(models.Model):
    """
    Vehicle escort mission. While `return_date` is null the escort guard's
    status is "On Escort Duty" and the shift engine will not roster them
    for normal station duty (see shifts.services.guard_unavailable).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destination = models.CharField(max_length=150, help_text="e.g. Harare")
    driver_name = models.CharField(max_length=150)
    vehicle_registration = models.CharField(max_length=32)
    escort_guard = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="escort_missions")
    departure = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)
    mileage_out = models.PositiveIntegerField(null=True, blank=True)
    mileage_in = models.PositiveIntegerField(null=True, blank=True)
    fuel_litres = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="escorts_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_active(self):
        return self.return_date is None

    def __str__(self):
        return f"Escort to {self.destination} - {self.escort_guard}"
