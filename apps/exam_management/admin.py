from django.contrib import admin
from .models import Exam, ExamAssignment


class AssignmentInline(admin.TabularInline):
    model = ExamAssignment
    extra = 0


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "venue", "station", "start_date", "end_date")
    inlines = [AssignmentInline]
