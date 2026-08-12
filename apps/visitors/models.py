import uuid
from django.db import models
from django.conf import settings


class Visitor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey("accounts.Station", on_delete=models.CASCADE, related_name="visitors")
    full_name = models.CharField(max_length=150)
    national_id = models.CharField(max_length=32, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    purpose = models.CharField(max_length=255)
    vehicle_registration = models.CharField(max_length=32, blank=True)
    host = models.CharField(max_length=150, blank=True, help_text="Person/department being visited")
    photo = models.ImageField(upload_to="visitor_photos/%Y/%m/", null=True, blank=True)
    time_in = models.DateTimeField(auto_now_add=True)
    time_out = models.DateTimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="visitors_recorded")

    class Meta:
        ordering = ["-time_in"]

    def __str__(self):
        return f"{self.full_name} - {self.purpose}"