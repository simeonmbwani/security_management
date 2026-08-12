"""
Shift Engine
============
Implements the automatic duty roster described in the SGMIS plan:

  * Guards are grouped into pairs (Pair 1 = A+B, Pair 2 = C+D, ...).
  * Each pair works a block of `cycle_length_days` (default 4) consecutive
    days together: guard_a on Day shift, guard_b on Night shift.
  * After the block, the next pair (by rotation_order) takes over.
  * Once every pair has had a block, the cycle repeats from Pair 1.

The engine also cooperates with other modules without hard-importing them
(to avoid circular imports), using `django.apps.apps.get_model`:
  * Guards on approved leave for a date are skipped.
  * Guards on an active vehicle escort mission are skipped ("On Escort Duty").
  * Guards assigned to exam supervision for a date are excluded from the
    normal rotation for that date (see exam_management.services for how
    exam duty itself is assigned).

When a guard must be skipped, the engine pulls the next available guard
(round-robin over all active guards at the station) as a substitute, so the
4-day cycle for everyone else is never broken.
"""
from datetime import timedelta
from django.apps import apps
from django.db import transaction
from django.conf import settings


def _get_model(app_label, model_name):
    return apps.get_model(app_label, model_name)


def get_active_pairs(station):
    GuardPair = _get_model("shifts", "GuardPair")
    return list(GuardPair.objects.filter(station=station, is_active=True).order_by("rotation_order"))


def guard_unavailable(guard, date):
    """True if guard is on leave, on escort duty, or otherwise blocked for `date`."""
    LeaveApplication = _get_model("leave_management", "LeaveApplication")
    EscortMission = _get_model("escort_management", "EscortMission")

    on_leave = LeaveApplication.objects.filter(
        guard=guard, status="approved", start_date__lte=date, end_date__gte=date
    ).exists()
    on_escort = EscortMission.objects.filter(
        escort_guard=guard, departure__date__lte=date, return_date__isnull=True
    ).exists()
    return on_leave or on_escort


def pair_on_duty_for_date(station, date):
    """Return the GuardPair scheduled for `date` under the rotation, or None."""
    DutyRosterCycle = _get_model("shifts", "DutyRosterCycle")
    try:
        cycle = DutyRosterCycle.objects.get(station=station)
    except DutyRosterCycle.DoesNotExist:
        return None

    pairs = get_active_pairs(station)
    if not pairs:
        return None

    offset_days = (date - cycle.cycle_start_date).days
    if offset_days < 0:
        return None

    cycle_length = cycle.cycle_length_days or settings.SGMIS_SETTINGS["SHIFT_CYCLE_DAYS"]
    block_index = offset_days // cycle_length
    pair_index = block_index % len(pairs)
    return pairs[pair_index]


def _pick_substitute(station, date, exclude_ids):
    """Round-robin pick of any active guard at the station not already excluded/unavailable."""
    User = _get_model("accounts", "User")
    GuardProfile = _get_model("accounts", "GuardProfile")
    candidates = User.objects.filter(
        guard_profile__station=station, is_active_employee=True, role="guard"
    ).exclude(id__in=exclude_ids)
    for candidate in candidates.order_by("employee_number"):
        if not guard_unavailable(candidate, date):
            return candidate
    return None


@transaction.atomic
def generate_roster_for_date(station, date):
    """
    Idempotently create today's Shift rows for a station. Safe to call
    repeatedly (e.g. from a daily Celery beat task) — existing shifts for
    the date are left untouched.
    """
    Shift = _get_model("shifts", "Shift")

    if Shift.objects.filter(station=station, date=date).exists():
        return list(Shift.objects.filter(station=station, date=date))

    pair = pair_on_duty_for_date(station, date)
    if pair is None:
        return []

    created = []
    assignments = [(pair.guard_a, Shift.ShiftType.DAY), (pair.guard_b, Shift.ShiftType.NIGHT)]
    excluded_ids = {pair.guard_a_id, pair.guard_b_id}

    for guard, shift_type in assignments:
        actual_guard = guard
        is_override = False
        reason = ""
        if guard_unavailable(guard, date):
            substitute = _pick_substitute(station, date, excluded_ids)
            if substitute:
                actual_guard = substitute
                excluded_ids.add(substitute.id)
                is_override = True
                reason = f"Substitute for {guard} (on leave/escort)"

        shift = Shift.objects.create(
            station=station, guard=actual_guard, date=date, shift_type=shift_type,
            pair=pair, is_override=is_override, override_reason=reason,
        )
        created.append(shift)

    return created


def generate_roster_range(station, start_date, end_date):
    """Generate shifts for every date in [start_date, end_date] inclusive."""
    results = []
    current = start_date
    while current <= end_date:
        results.extend(generate_roster_for_date(station, current))
        current += timedelta(days=1)
    return results


def apply_exam_override(station, date, excluded_guard_ids):
    """
    Called by exam_management when guards are pulled onto exam supervision.
    Regenerates that date's non-exam shifts using the remaining pool, without
    disturbing the underlying 4-day cycle for future dates.
    """
    Shift = _get_model("shifts", "Shift")
    Shift.objects.filter(station=station, date=date).delete()

    pair = pair_on_duty_for_date(station, date)
    if pair is None:
        return []

    created = []
    assignments = [(pair.guard_a, Shift.ShiftType.DAY), (pair.guard_b, Shift.ShiftType.NIGHT)]
    excluded_ids = set(excluded_guard_ids) | {pair.guard_a_id, pair.guard_b_id}

    for guard, shift_type in assignments:
        actual_guard = guard
        is_override = False
        reason = ""
        if guard.id in excluded_guard_ids or guard_unavailable(guard, date):
            substitute = _pick_substitute(station, date, excluded_ids)
            if substitute:
                actual_guard = substitute
                excluded_ids.add(substitute.id)
                is_override = True
                reason = "Reassigned due to exam deployment"

        shift = Shift.objects.create(
            station=station, guard=actual_guard, date=date, shift_type=shift_type,
            pair=pair, is_override=is_override, override_reason=reason,
        )
        created.append(shift)

    return created
