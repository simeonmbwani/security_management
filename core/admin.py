from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "model_name", "object_id", "actor", "created_at")
    list_filter = ("model_name", "action")
    search_fields = ("object_id", "model_name")
    readonly_fields = [f.name for f in AuditLog._meta.fields]
