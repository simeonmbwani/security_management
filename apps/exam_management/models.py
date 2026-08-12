import uuid
from django.db import models
from django.conf import settings


class Exam(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey("accounts.Station", on_delete=models.CASCADE, related_name="exams")
    name = models.CharField(max_length=150)
    venue = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="exams_created")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} @ {self.venue} ({self.start_date} - {self.end_date})"


class ExamAssignment(models.Model):
    """
    A guard assigned to supervise a specific exam venue for its duration.
    Business rule: a guard whose normal duty pairing already has them
    scheduled at that venue's "home" post cannot be double-booked for
    supervision there (system blocks it - see serializers.validate()).
    Supervision is day-shift only, for the exam's full run.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="assignments")
    guard = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exam_assignments")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="exam_assignments_made"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    ordering = ["-id"]
    class Meta:
        unique_together = ("exam", "guard")

    def __str__(self):
        return f"{self.guard} -> {self.exam}"
