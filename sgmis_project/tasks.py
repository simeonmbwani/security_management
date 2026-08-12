"""
Scheduled tasks. Register these with django-celery-beat (via the admin, or
a data migration) with these suggested schedules:

  * generate_tomorrow_roster        -> daily, e.g. 20:00
  * run_monthly_leave_accrual       -> monthly, 1st day, 00:05
  * flag_overdue_patrols            -> every 15 minutes
  * send_start_patrol_reminders     -> daily, per-shift start times (or every 30 min, checks each shift)
  * send_shift_change_reminders     -> daily, 30 minutes before shift change

This file lives at the project level (not inside one app) because it
coordinates several apps.
"""
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.conf import settings


@shared_task
def generate_tomorrow_roster():
    from apps.accounts.models import Station
    from apps.shifts import services as shift_services

    tomorrow = timezone.localdate() + timedelta(days=1)
    for station in Station.objects.filter(is_active=True):
        shift_services.generate_roster_for_date(station, tomorrow)


@shared_task
def run_monthly_leave_accrual():
    from apps.leave_management import services as leave_services
    leave_services.run_monthly_accrual()


@shared_task
def flag_overdue_patrols():
    from apps.patrols.models import Patrol
    from apps.notifications import services as notification_services

    overdue_minutes = settings.SGMIS_SETTINGS["PATROL_OVERDUE_MINUTES"]
    cutoff = timezone.now() - timedelta(minutes=overdue_minutes)
    overdue = Patrol.objects.filter(status=Patrol.Status.IN_PROGRESS, started_at__lt=cutoff)

    for patrol in overdue:
        patrol.status = Patrol.Status.OVERDUE
        patrol.save(update_fields=["status"])
        # Notify the guard and their supervisors.
        notification_services.notify(
            patrol.guard, "patrol_overdue", "Your patrol is overdue",
            f"Patrol started at {patrol.started_at:%H:%M} has not been finished.",
        )
        from apps.accounts.models import User
        supervisors = User.objects.filter(role__in=["supervisor", "administrator"])
        notification_services.notify_many(
            supervisors, "patrol_overdue", f"Overdue patrol: {patrol.guard}",
            f"Started at {patrol.started_at:%H:%M}, station {patrol.station}.",
        )


@shared_task
def send_start_patrol_reminders():
    """
    Reminds guards currently on shift who have not started a patrol in the
    last hour to start one. Intended to run every ~30-60 minutes.
    """
    from apps.shifts.models import Shift
    from apps.patrols.models import Patrol
    from apps.notifications import services as notification_services

    today = timezone.localdate()
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)

    active_shifts = Shift.objects.filter(date=today)
    for shift in active_shifts:
        recent_patrol = Patrol.objects.filter(guard=shift.guard, started_at__gte=one_hour_ago).exists()
        if not recent_patrol:
            notification_services.notify(
                shift.guard, "patrol_start", "Time to start your patrol",
                "It's been over an hour since your last patrol round.",
            )


@shared_task
def send_shift_change_reminders():
    """Reminds guards whose shift ends soon to prepare a handover."""
    from apps.shifts.models import Shift
    from apps.notifications import services as notification_services

    today = timezone.localdate()
    shifts_ending_today = Shift.objects.filter(date=today)
    for shift in shifts_ending_today:
        notification_services.notify(
            shift.guard, "shift_change", "Shift change coming up",
            "Please prepare your handover notes (occurrence summary, equipment, keys, pending issues).",
        )


@shared_task
def send_two_day_duty_change_reminders():
    """Daily job: notify guards about rostered or changed duties two days ahead."""
    from apps.shifts.models import Shift
    from apps.notifications import services as notification_services

    duty_date = timezone.localdate() + timedelta(days=2)
    for shift in Shift.objects.filter(date=duty_date).select_related("station", "guard"):
        detail = f"{shift.get_shift_type_display()} shift at {shift.station}."
        if shift.is_override and shift.override_reason:
            detail = f"Duty change: {shift.override_reason}. {detail}"
        notification_services.notify(
            shift.guard, "shift_change", f"Duty reminder for {duty_date:%d %b}", detail,
        )
