from django.urls import path
from . import views

urlpatterns = [
    path("admin-summary/", views.AdminSummaryView.as_view(), name="report-admin-summary"),
    path("daily-ob/", views.DailyOBReportView.as_view(), name="report-daily-ob"),
    path("weekly-ob/", views.WeeklyOBReportView.as_view(), name="report-weekly-ob"),
    path("monthly-incidents/", views.MonthlyIncidentsReportView.as_view(), name="report-monthly-incidents"),
    path("leave-balances/", views.LeaveBalancesReportView.as_view(), name="report-leave-balances"),
    path("attendance/", views.AttendanceReportView.as_view(), name="report-attendance"),
    path("patrol-compliance/", views.PatrolComplianceReportView.as_view(), name="report-patrol-compliance"),
    path("holiday-compensation/", views.HolidayCompensationReportView.as_view(), name="report-holiday-compensation"),
    path("exam-duties/", views.ExamDutiesReportView.as_view(), name="report-exam-duties"),
    path("escort-duties/", views.EscortDutiesReportView.as_view(), name="report-escort-duties"),
]
