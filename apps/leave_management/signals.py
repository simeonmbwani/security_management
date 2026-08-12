"""
Auto-credit holiday compensation whenever a guard's Shift lands on a
PublicHoliday date. Imported from AppConfig.ready(), by which point the
`shifts` app model registry is guaranteed to be loaded, so it's safe to
connect the signal directly.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps as django_apps

from .models import PublicHoliday
from . import services

Shift = django_apps.get_model("shifts", "Shift")


@receiver(post_save, sender=Shift, dispatch_uid="credit_holiday_on_shift_save")
def credit_holiday_on_shift(sender, instance, created, **kwargs):
    if not created:
        return
    holiday = PublicHoliday.objects.filter(date=instance.date).first()
    if holiday:
        services.credit_public_holiday_work(instance.guard, holiday)
