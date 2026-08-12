"""
Exam Deployment Engine
======================
Rules from the SGMIS plan:

  * A guard already rostered for normal duty on the exam's venue that day
    cannot also be picked as an exam-venue escort/supervisor for that venue
    (the system blocks the double-booking).
  * Chosen supervisors work day-shift only, for the exam's full run
    (typically 5 consecutive days).
  * Meanwhile, the campus's normal roster keeps running: shifts.services
    reassigns the remaining pool so 1 day guard + 1 night guard are still
    covered every day, without breaking the underlying 4-day cycle.
"""
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.shifts import services as shift_services
from apps.shifts.models import Shift
from .models import Exam, ExamAssignment


def guard_already_on_venue_duty(guard, exam: Exam):
    """
    True if this guard's normal roster already has them posted at the exam
    venue's station for the exam period — i.e. they are the "home guard"
    and shouldn't double as the independent exam supervisor.
    """
    return Shift.objects.filter(
        station=exam.station, guard=guard,
        date__gte=exam.start_date, date__lte=exam.end_date,
    ).exists()


@transaction.atomic
def assign_exam_supervisor(exam: Exam, guard, assigned_by):
    if guard_already_on_venue_duty(guard, exam):
        raise ValidationError(
            f"{guard} is already rostered for normal duty at this venue during the exam "
            f"period and cannot also be the independent exam supervisor."
        )

    assignment, created = ExamAssignment.objects.get_or_create(
        exam=exam, guard=guard, defaults={"assigned_by": assigned_by}
    )
    if not created:
        return assignment

    # Re-run the roster for each exam day, excluding this guard from the
    # normal pairing pool so the campus still gets 1 day + 1 night guard.
    excluded_ids = {a.guard_id for a in exam.assignments.all()}
    current = exam.start_date
    while current <= exam.end_date:
        shift_services.apply_exam_override(exam.station, current, excluded_ids)
        current += timedelta(days=1)

    return assignment


def unassign_exam_supervisor(exam: Exam, guard):
    ExamAssignment.objects.filter(exam=exam, guard=guard).delete()
    excluded_ids = {a.guard_id for a in exam.assignments.all()}
    current = exam.start_date
    while current <= exam.end_date:
        shift_services.apply_exam_override(exam.station, current, excluded_ids)
        current += timedelta(days=1)
