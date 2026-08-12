from django.contrib import admin
from .models import EscortMission


@admin.register(EscortMission)
class EscortMissionAdmin(admin.ModelAdmin):
    list_display = ("destination", "escort_guard", "departure", "return_date")
    list_filter = ("escort_guard",)
