"""Thin helper to create in-app notifications. Swap `send_push`/`send_sms`
stubs for a real provider (Firebase, Africa's Talking, etc.) in production."""
from .models import Notification


def notify(recipient, category, title, body=""):
    return Notification.objects.create(recipient=recipient, category=category, title=title, body=body)


def notify_many(recipients, category, title, body=""):
    return [notify(r, category, title, body) for r in recipients]


def send_push(notification):
    """Stub — wire up FCM/APNs here."""
    pass


def send_sms(notification):
    """Stub — wire up an SMS gateway here."""
    pass
