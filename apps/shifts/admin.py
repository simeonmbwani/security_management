from django.contrib import admin
from .models import GuardPair, DutyRosterCycle, Shift, ShiftHandover, Attendance


@admin.register(GuardPair)
class GuardPairAdmin(admin.ModelAdmin):
    list_display = ("name", "station", "guard_a", "guard_b", "rotation_order", "is_active")
    list_filter = ("station", "is_active")


@admin.register(DutyRosterCycle)
class DutyRosterCycleAdmin(admin.ModelAdmin):
    list_display = ("station", "cycle_start_date", "cycle_length_days")


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("date", "station", "guard", "shift_type", "is_override")
    list_filter = ("station", "shift_type", "is_override")
    search_fields = ("guard__employee_number", "guard__first_name", "guard__last_name")


@admin.register(ShiftHandover)
class ShiftHandoverAdmin(admin.ModelAdmin):
    list_display = ("outgoing_shift", "incoming_guard", "incoming_accepted")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("shift", "clock_in", "clock_out", "is_late", "is_absent")
