from django.contrib import admin
from .models import KeyRegisterItem, EquipmentItem


@admin.register(KeyRegisterItem)
class KeyRegisterItemAdmin(admin.ModelAdmin):
    list_display = ("key_number", "description", "issued_to", "issued_at", "returned_at")
    list_filter = ("station",)


@admin.register(EquipmentItem)
class EquipmentItemAdmin(admin.ModelAdmin):
    list_display = ("equipment_type", "issued_to", "condition_out", "condition_in", "returned_at")
    list_filter = ("station", "equipment_type", "condition_out")
