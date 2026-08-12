from django.contrib import admin
from .models import IncidentReport, IncidentMedia


class MediaInline(admin.TabularInline):
    model = IncidentMedia
    extra = 0


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ("incident_type", "station", "reported_by", "status", "created_at")
    list_filter = ("station", "incident_type", "status")
    inlines = [MediaInline]
