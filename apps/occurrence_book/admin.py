from django.contrib import admin
from .models import OccurrenceBookEntry, OccurrenceBookPhoto


class PhotoInline(admin.TabularInline):
    model = OccurrenceBookPhoto
    extra = 0


@admin.register(OccurrenceBookEntry)
class OccurrenceBookEntryAdmin(admin.ModelAdmin):
    list_display = ("entry_number", "station", "guard", "shift", "created_at")
    list_filter = ("station", "shift")
    search_fields = ("entry_number", "occurrence")
    inlines = [PhotoInline]
