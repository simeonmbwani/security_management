import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    class Category(models.TextChoices):
        PATROL_START = "patrol_start", "Start Patrol Reminder"
        PATROL_OVERDUE = "patrol_overdue", "Patrol Overdue"
        LEAVE_APPROVED = "leave_approved", "Leave Approved"
        LEAVE_STATUS = "leave_status", "Leave Status Update"
        SHIFT_CHANGE = "shift_change", "Shift Change"
        HOLIDAY_COMPENSATION = "holiday_compensation", "Public Holiday Compensation"
        EXAM_DEPLOYMENT = "exam_deployment", "Exam Deployment"
        ESCORT_ASSIGNMENT = "escort_assignment", "Escort Assignment"
        INCIDENT_ALERT = "incident_alert", "Incident Alert"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    category = models.CharField(max_length=30, choices=Category.choices)
    title = models.CharField(max_length=150)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.category} -> {self.recipient}"
