import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.accounts.models import Station, GuardProfile
from apps.shifts.models import GuardPair, DutyRosterCycle
from apps.patrols.models import Checkpoint
from apps.leave_management.models import PublicHoliday

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with a demo station, an admin, a supervisor, 6 guards, pairs, checkpoints and holidays."

    @transaction.atomic
    def handle(self, *args, **options):
        station, _ = Station.objects.get_or_create(name="Main Campus", defaults={"address": "1 Example Road"})

        if not User.objects.filter(employee_number="ADMIN001").exists():
            admin = User.objects.create_superuser(
                username="admin", email="admin@example.com", password="ChangeMe123!",
                employee_number="ADMIN001", role=User.Role.ADMINISTRATOR,
                first_name="System", last_name="Administrator",
            )
            GuardProfile.objects.create(user=admin, station=station, rank="chief_supervisor",
                                         date_employed=datetime.date(2020, 1, 1))
            self.stdout.write(self.style.SUCCESS("Created admin (username=admin, password=ChangeMe123!)"))

        if not User.objects.filter(employee_number="SUP001").exists():
            supervisor = User.objects.create_user(
                username="supervisor1", password="ChangeMe123!", employee_number="SUP001",
                role=User.Role.SUPERVISOR, first_name="Sarah", last_name="Supervisor",
            )
            GuardProfile.objects.create(user=supervisor, station=station, rank="supervisor",
                                         date_employed=datetime.date(2021, 1, 1))
            self.stdout.write(self.style.SUCCESS("Created supervisor (username=supervisor1, password=ChangeMe123!)"))

        guard_letters = ["A", "B", "C", "D", "E", "F"]
        guards = []
        for i, letter in enumerate(guard_letters, start=1):
            emp_no = f"GRD00{i}"
            if not User.objects.filter(employee_number=emp_no).exists():
                guard = User.objects.create_user(
                    username=f"guard{letter.lower()}", password="ChangeMe123!", employee_number=emp_no,
                    role=User.Role.GUARD, first_name=f"Guard", last_name=letter,
                )
                GuardProfile.objects.create(user=guard, station=station, rank="guard",
                                             date_employed=datetime.date(2022, 1, 1))
            else:
                guard = User.objects.get(employee_number=emp_no)
            guards.append(guard)

        self.stdout.write(self.style.SUCCESS(f"Guards ready: {[g.employee_number for g in guards]}"))

        pair_defs = [("Pair 1", guards[0], guards[1], 1), ("Pair 2", guards[2], guards[3], 2), ("Pair 3", guards[4], guards[5], 3)]
        for name, a, b, order in pair_defs:
            GuardPair.objects.get_or_create(
                station=station, rotation_order=order,
                defaults={"name": name, "guard_a": a, "guard_b": b},
            )

        DutyRosterCycle.objects.get_or_create(
            station=station, defaults={"cycle_start_date": datetime.date.today(), "cycle_length_days": 4}
        )

        checkpoint_names = ["Main Gate", "Administration", "Hostel", "Library", "Examination Room", "Perimeter Fence"]
        for order, name in enumerate(checkpoint_names, start=1):
            Checkpoint.objects.get_or_create(station=station, name=name, defaults={"order": order})

        holidays = [("Heroes Day", datetime.date(datetime.date.today().year, 8, 11)),
                    ("Independence Day", datetime.date(datetime.date.today().year, 4, 18))]
        for name, date in holidays:
            PublicHoliday.objects.get_or_create(name=name, date=date)

        self.stdout.write(self.style.SUCCESS(
            "Demo data ready. Login at /api/auth/login/ or /admin/ with admin / ChangeMe123! "
            "(please change this password immediately)."
        ))
