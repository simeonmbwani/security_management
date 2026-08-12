import uuid
from django.db import models
from django.conf import settings


class LeaveType(models.TextChoices):
    CASUAL = "casual", "Casual Leave"
    VACATION = "vacation", "Vacation Leave"
    COMPENSATION = "compensation", "Compensation Leave (Public Holiday)"


class LeaveBalance(models.Model):
    """
    Running balance per guard per leave type. Casual and Vacation balances
    are maintained automatically by the accrual engine (services.py), run
    monthly via Celery beat. Compensation balance is topped up whenever a
    guard works a public holiday (see PublicHolidayWorkLog below).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guard = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leave_balances")
    leave_type = models.CharField(max_length=20, choices=LeaveType.choices)
    available_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    expired_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    last_accrued_month = models.DateField(null=True, blank=True, help_text="First of the month last accrual ran")

    class Meta:
        unique_together = ("guard", "leave_type")

    def __str__(self):
        return f"{self.guard} - {self.get_leave_type_display()}: {self.available_days} days"


class LeaveAccrualLog(models.Model):
    """Audit trail of every automatic accrual/expiry transaction."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    balance = models.ForeignKey(LeaveBalance, on_delete=models.CASCADE, related_name="accrual_logs")
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class PublicHoliday(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    date = models.DateField(unique=True)

    def __str__(self):
        return f"{self.name} ({self.date})"


class PublicHolidayWorkLog(models.Model):
    """Created automatically when a guard has a Shift on a PublicHoliday date."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guard = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="holiday_work_logs")
    holiday = models.ForeignKey(PublicHoliday, on_delete=models.CASCADE, related_name="work_logs")
    days_credited = models.DecimalField(max_digits=4, decimal_places=2, default=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("guard", "holiday")


class LeaveApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CHANGES_REQUESTED = "changes_requested", "Changes Requested"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guard = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leave_applications")
    leave_type = models.CharField(max_length=20, choices=LeaveType.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="leave_reviews",
    )
    review_comment = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def days_requested(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.guard} - {self.leave_type} ({self.start_date} to {self.end_date})"
