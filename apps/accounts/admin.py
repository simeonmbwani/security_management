from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Station, GuardProfile


@admin.register(User)
class SGMISUserAdmin(UserAdmin):
    list_display = ("employee_number", "username", "first_name", "last_name", "role", "is_active_employee")
    list_filter = ("role", "is_active_employee")
    search_fields = ("employee_number", "username", "first_name", "last_name", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("SGMIS", {"fields": ("role", "employee_number", "phone", "is_active_employee")}),
    )


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "is_active")


@admin.register(GuardProfile)
class GuardProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "station", "rank", "date_employed", "is_on_escort_duty")
    list_filter = ("station", "rank", "is_on_escort_duty")
