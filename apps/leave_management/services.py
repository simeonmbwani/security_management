"""
Leave Engine
============
Implements the accrual rules from the SGMIS plan:

  * Casual leave:    +1 day / month, capped at 12 days, expires after 12
                     months if unused.
  * Vacation leave:   +2.5 days / month, capped at 90 days (accrual pauses
                     once the cap is hit, resumes once leave is taken).
  * Compensation:    +2 days whenever a guard is rostered to work a public
                     holiday (not money — banked leave days).

`run_monthly_accrual()` is intended to be triggered by Celery beat on the
1st of each month. `credit_public_holiday_work()` is triggered by a signal
(see signals.py) whenever a Shift lands on a PublicHoliday date.
"""
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import LeaveBalance, LeaveAccrualLog, LeaveType, PublicHoliday, PublicHolidayWorkLog


def _settings():
    return settings.SGMIS_SETTINGS


@transaction.atomic
def accrue_casual_leave(guard, as_of_month):
    cfg = _settings()
    balance, _ = LeaveBalance.objects.get_or_create(guard=guard, leave_type=LeaveType.CASUAL)

    if balance.last_accrued_month == as_of_month:
        return balance  # already ran for this month

    # Expire anything older than the expiry window before adding new days.
    expiry_cutoff = as_of_month - relativedelta(months=cfg["CASUAL_LEAVE_EXPIRY_MONTHS"])
    if balance.last_accrued_month and balance.last_accrued_month <= expiry_cutoff:
        expired = balance.available_days
        if expired > 0:
            balance.expired_days += expired
            balance.available_days = Decimal("0")
            LeaveAccrualLog.objects.create(balance=balance, amount=-expired, reason="Casual leave expired (12 months unused)")

    increment = Decimal(str(cfg["CASUAL_LEAVE_PER_MONTH"]))
    new_total = min(balance.available_days + increment, Decimal(str(cfg["CASUAL_LEAVE_MAX"])))
    actually_added = new_total - balance.available_days
    balance.available_days = new_total
    balance.last_accrued_month = as_of_month
    balance.save()

    if actually_added > 0:
        LeaveAccrualLog.objects.create(balance=balance, amount=actually_added, reason=f"Monthly casual accrual {as_of_month}")
    return balance


@transaction.atomic
def accrue_vacation_leave(guard, as_of_month):
    cfg = _settings()
    balance, _ = LeaveBalance.objects.get_or_create(guard=guard, leave_type=LeaveType.VACATION)

    if balance.last_accrued_month == as_of_month:
        return balance

    increment = Decimal(str(cfg["VACATION_LEAVE_PER_MONTH"]))
    cap = Decimal(str(cfg["VACATION_LEAVE_MAX"]))
    if balance.available_days >= cap:
        # Accrual pauses at the cap until leave is taken.
        balance.last_accrued_month = as_of_month
        balance.save(update_fields=["last_accrued_month"])
        return balance

    new_total = min(balance.available_days + increment, cap)
    actually_added = new_total - balance.available_days
    balance.available_days = new_total
    balance.last_accrued_month = as_of_month
    balance.save()

    if actually_added > 0:
        LeaveAccrualLog.objects.create(balance=balance, amount=actually_added, reason=f"Monthly vacation accrual {as_of_month}")
    return balance


def run_monthly_accrual():
    """Run casual + vacation accrual for every active guard. Call from Celery beat, monthly."""
    from apps.accounts.models import User

    as_of_month = timezone.localdate().replace(day=1)
    guards = User.objects.filter(role="guard", is_active_employee=True)
    for guard in guards:
        accrue_casual_leave(guard, as_of_month)
        accrue_vacation_leave(guard, as_of_month)


@transaction.atomic
def credit_public_holiday_work(guard, holiday: PublicHoliday):
    """Credit 2 compensation days if not already credited for this holiday."""
    cfg = _settings()
    if PublicHolidayWorkLog.objects.filter(guard=guard, holiday=holiday).exists():
        return None

    days = Decimal(str(cfg["HOLIDAY_COMPENSATION_DAYS"]))
    PublicHolidayWorkLog.objects.create(guard=guard, holiday=holiday, days_credited=days)

    balance, _ = LeaveBalance.objects.get_or_create(guard=guard, leave_type=LeaveType.COMPENSATION)
    balance.available_days += days
    balance.save(update_fields=["available_days"])
    LeaveAccrualLog.objects.create(balance=balance, amount=days, reason=f"Worked public holiday: {holiday.name}")
    return balance


@transaction.atomic
def approve_leave_application(application, reviewer, comment=""):
    """Deduct the approved days from the guard's balance."""
    # 1. Safely get or create the balance record if it doesn't exist yet (removed 'total_days')
    LeaveBalance.objects.get_or_create(
        guard=application.guard,
        leave_type=application.leave_type,
        defaults={
            'available_days': Decimal("10.0"),
            'used_days': Decimal("0"),
            'expired_days': Decimal("0")
        }
    )

    # 2. Lock the row for update to prevent race conditions during concurrent approvals
    balance = LeaveBalance.objects.select_for_update().get(
        guard=application.guard, 
        leave_type=application.leave_type
    )

    days = Decimal(application.days_requested)
    if balance.available_days < days:
        raise ValueError(
            f"Insufficient {application.get_leave_type_display()} balance: "
            f"{balance.available_days} available, {days} requested."
        )
        
    balance.available_days -= days
    balance.used_days += days
    balance.save(update_fields=["available_days", "used_days"])

    application.status = application.Status.APPROVED
    application.reviewed_by = reviewer
    application.review_comment = comment
    application.save(update_fields=["status", "reviewed_by", "review_comment", "updated_at"])
    
    LeaveAccrualLog.objects.create(balance=balance, amount=-days, reason=f"Leave approved: {application.id}")
    return application