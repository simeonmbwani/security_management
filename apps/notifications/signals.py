"""
Wires up automatic notifications across modules. Kept centralized here
(rather than scattered post_save signals in every app) so notification
behaviour is easy to audit and change in one place.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps as django_apps

from . import services

IncidentReport = django_apps.get_model("incidents", "IncidentReport")
LeaveApplication = django_apps.get_model("leave_management", "LeaveApplication")
ExamAssignment = django_apps.get_model("exam_management", "ExamAssignment")
EscortMission = django_apps.get_model("escort_management", "EscortMission")


@receiver(post_save, sender=IncidentReport, dispatch_uid="notify_on_incident")
def notify_on_incident(sender, instance, created, **kwargs):
    if not created:
        return
    from apps.accounts.models import User
    supervisors = User.objects.filter(role__in=["supervisor", "administrator"])
    services.notify_many(
        supervisors, "incident_alert",
        f"{instance.get_incident_type_display()} reported at {instance.station}",
        instance.description,
    )


@receiver(post_save, sender=LeaveApplication, dispatch_uid="notify_on_leave_status")
def notify_on_leave_status(sender, instance, created, **kwargs):
    if created:
        from apps.accounts.models import User
        recipients = User.objects.filter(role="administrator")
        services.notify_many(
            recipients, "leave_status", "New leave application",
            f"{instance.guard} requested {instance.leave_type} leave from {instance.start_date} to {instance.end_date}.",
        )
        return
    if instance.status == "approved":
        services.notify(instance.guard, "leave_approved", "Your leave was approved",
                         f"{instance.leave_type} leave from {instance.start_date} to {instance.end_date}.")
    elif instance.status in ("rejected", "changes_requested"):
        services.notify(instance.guard, "leave_status", f"Leave application {instance.status}",
                         instance.review_comment)


@receiver(post_save, sender=ExamAssignment, dispatch_uid="notify_on_exam_assignment")
def notify_on_exam_assignment(sender, instance, created, **kwargs):
    if created:
        services.notify(instance.guard, "exam_deployment", f"Exam supervision: {instance.exam.name}",
                         f"Venue: {instance.exam.venue}, {instance.exam.start_date} to {instance.exam.end_date}")


@receiver(post_save, sender=EscortMission, dispatch_uid="notify_on_escort_assignment")
def notify_on_escort_assignment(sender, instance, created, **kwargs):
    if created:
        services.notify(instance.escort_guard, "escort_assignment", f"Escort duty: {instance.destination}",
                         f"Departure: {instance.departure}")
