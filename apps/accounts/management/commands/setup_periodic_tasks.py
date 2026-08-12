from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule


class Command(BaseCommand):
    help = "Registers the SGMIS automated jobs (roster generation, leave accrual, patrol monitoring) with Celery Beat."

    def handle(self, *args, **options):
        # Every 15 minutes: flag overdue patrols
        every_15, _ = IntervalSchedule.objects.get_or_create(every=15, period=IntervalSchedule.MINUTES)
        PeriodicTask.objects.update_or_create(
            name="Flag overdue patrols",
            defaults={"interval": every_15, "task": "sgmis_project.tasks.flag_overdue_patrols"},
        )

        # Every 30 minutes: patrol start reminders
        every_30, _ = IntervalSchedule.objects.get_or_create(every=30, period=IntervalSchedule.MINUTES)
        PeriodicTask.objects.update_or_create(
            name="Send start patrol reminders",
            defaults={"interval": every_30, "task": "sgmis_project.tasks.send_start_patrol_reminders"},
        )

        # Daily 20:00: generate tomorrow's roster
        daily_2000, _ = CrontabSchedule.objects.get_or_create(minute=0, hour=20, day_of_week="*", day_of_month="*", month_of_year="*")
        PeriodicTask.objects.update_or_create(
            name="Generate tomorrow's roster",
            defaults={"crontab": daily_2000, "task": "sgmis_project.tasks.generate_tomorrow_roster"},
        )

        # Daily 17:30: shift change reminders
        daily_1730, _ = CrontabSchedule.objects.get_or_create(minute=30, hour=17, day_of_week="*", day_of_month="*", month_of_year="*")
        PeriodicTask.objects.update_or_create(
            name="Send shift change reminders",
            defaults={"crontab": daily_1730, "task": "sgmis_project.tasks.send_shift_change_reminders"},
        )

        # Monthly, 1st @ 00:05: leave accrual
        monthly, _ = CrontabSchedule.objects.get_or_create(minute=5, hour=0, day_of_week="*", day_of_month=1, month_of_year="*")
        PeriodicTask.objects.update_or_create(
            name="Run monthly leave accrual",
            defaults={"crontab": monthly, "task": "sgmis_project.tasks.run_monthly_leave_accrual"},
        )

        self.stdout.write(self.style.SUCCESS("Periodic tasks registered."))
