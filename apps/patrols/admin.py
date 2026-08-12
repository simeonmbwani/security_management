from django.contrib import admin
from .models import Checkpoint, Patrol, PatrolCheckpointLog


class LogInline(admin.TabularInline):
    model = PatrolCheckpointLog
    extra = 0


@admin.register(Checkpoint)
class CheckpointAdmin(admin.ModelAdmin):
    list_display = ("name", "station", "order", "is_active")
    list_filter = ("station",)


@admin.register(Patrol)
class PatrolAdmin(admin.ModelAdmin):
    list_display = ("guard", "station", "started_at", "finished_at", "status")
    list_filter = ("station", "status")
    inlines = [LogInline]
