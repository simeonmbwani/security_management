from django.contrib import admin
from .models import LeaveBalance, LeaveAccrualLog, PublicHoliday, PublicHolidayWorkLog, LeaveApplication


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ("guard", "leave_type", "available_days", "used_days", "expired_days")
    list_filter = ("leave_type",)


@admin.register(LeaveAccrualLog)
class LeaveAccrualLogAdmin(admin.ModelAdmin):
    list_display = ("balance", "amount", "reason", "created_at")


@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ("name", "date")


@admin.register(PublicHolidayWorkLog)
class PublicHolidayWorkLogAdmin(admin.ModelAdmin):
    list_display = ("guard", "holiday", "days_credited")


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ("guard", "leave_type", "start_date", "end_date", "status")
    list_filter = ("leave_type", "status")
