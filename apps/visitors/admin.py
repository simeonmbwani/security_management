from django.contrib import admin
from .models import Visitor


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "station", "purpose", "time_in", "time_out")
    list_filter = ("station",)
    search_fields = ("full_name", "national_id")
