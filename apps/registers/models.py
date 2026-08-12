import uuid
from django.db import models
from django.conf import settings


class KeyRegisterItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey("accounts.Station", on_delete=models.CASCADE, related_name="key_register")
    key_number = models.CharField(max_length=32)
    description = models.CharField(max_length=150, blank=True, help_text="e.g. 'Computer Lab'")
    issued_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="keys_issued")
    issued_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_outstanding(self):
        return self.returned_at is None

    def __str__(self):
        return f"Key {self.key_number} - {self.issued_to}"


class EquipmentItem(models.Model):
    class EquipmentType(models.TextChoices):
        TORCH = "torch", "Torch"
        RADIO = "radio", "Radio"
        HANDCUFFS = "handcuffs", "Handcuffs"
        BATON = "baton", "Baton"
        REFLECTOR = "reflector", "Reflector"
        OTHER = "other", "Other"

    class Condition(models.TextChoices):
        GOOD = "good", "Good"
        DAMAGED = "damaged", "Damaged"
        LOST = "lost", "Lost"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey("accounts.Station", on_delete=models.CASCADE, related_name="equipment_register")
    equipment_type = models.CharField(max_length=20, choices=EquipmentType.choices)
    serial_number = models.CharField(max_length=64, blank=True)
    issued_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="equipment_issued")
    issued_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    condition_out = models.CharField(max_length=10, choices=Condition.choices, default=Condition.GOOD)
    condition_in = models.CharField(max_length=10, choices=Condition.choices, blank=True)

    @property
    def is_outstanding(self):
        return self.returned_at is None

    def __str__(self):
        return f"{self.get_equipment_type_display()} - {self.issued_to}"
