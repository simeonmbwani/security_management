"""
Report endpoints. Each returns either a JSON summary (for the dashboard) or,
when `?format=pdf` / `?format=excel` is passed, a downloadable file.

This module intentionally keeps the export helpers generic (`_export_pdf`,
`_export_excel`) so adding a new report is just: query the data, hand it to
the helper with column headers.
"""
import io
from datetime import timedelta
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsAdministrator

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl

from apps.occurrence_book.models import OccurrenceBookEntry
from apps.leave_management.models import LeaveBalance
from apps.patrols.models import Patrol
from apps.shifts.models import Attendance
from apps.incidents.models import IncidentReport
from apps.exam_management.models import ExamAssignment
from apps.escort_management.models import EscortMission
from apps.leave_management.models import PublicHolidayWorkLog


def _export_pdf(filename, title, headers, rows):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    table_data = [headers] + rows
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
    ]))
    elements.append(table)
    doc.build(elements)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
    return response


def _export_excel(filename, title, headers, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title[:31]
    ws.append(headers)
    for row in rows:
        ws.append(row)

    buffer = io.BytesIO()
    wb.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    return response


class BaseReportView(APIView):
    permission_classes = [IsAuthenticated]
    title = "Report"
    headers = []

    def scope(self, queryset, request, owner_field):
        """Keep a guard's 'My Reports' private while supervisors see their station."""
        user = request.user
        if user.role == "guard":
            return queryset.filter(**{owner_field: user})
        if user.role == "supervisor":
            station = getattr(getattr(user, "guard_profile", None), "station", None)
            if station is not None:
                return queryset.filter(station=station)
        return queryset

    def get_rows(self, request):
        raise NotImplementedError

    def get(self, request):
        rows = self.get_rows(request)
        fmt = request.query_params.get("format")
        filename = self.title.lower().replace(" ", "_")
        if fmt == "pdf":
            return _export_pdf(filename, self.title, self.headers, rows)
        if fmt == "excel":
            return _export_excel(filename, self.title, self.headers, rows)
        return Response({"title": self.title, "headers": self.headers, "rows": rows})


class DailyOBReportView(BaseReportView):
    title = "Daily Occurrence Book Report"
    headers = ["Entry #", "Station", "Guard", "Shift", "Occurrence", "Time"]

    def get_rows(self, request):
        date = request.query_params.get("date", timezone.localdate().isoformat())
        entries = self.scope(OccurrenceBookEntry.objects.filter(created_at__date=date), request, "guard").select_related("guard", "station")
        return [
            [e.entry_number, str(e.station), str(e.guard), e.shift, e.occurrence[:120], e.created_at.strftime("%H:%M")]
            for e in entries
        ]


class WeeklyOBReportView(BaseReportView):
    title = "Weekly Occurrence Book Report"
    headers = ["Entry #", "Station", "Guard", "Shift", "Occurrence", "Date"]

    def get_rows(self, request):
        end = timezone.localdate()
        start = end - timedelta(days=7)
        entries = self.scope(OccurrenceBookEntry.objects.filter(created_at__date__range=[start, end]), request, "guard").select_related("guard", "station")
        return [
            [e.entry_number, str(e.station), str(e.guard), e.shift, e.occurrence[:120], e.created_at.strftime("%Y-%m-%d")]
            for e in entries
        ]


class MonthlyIncidentsReportView(BaseReportView):
    title = "Monthly Incidents Report"
    headers = ["Type", "Station", "Reported By", "Status", "Date"]

    def get_rows(self, request):
        end = timezone.localdate()
        start = end - timedelta(days=30)
        incidents = self.scope(IncidentReport.objects.filter(created_at__date__range=[start, end]), request, "reported_by").select_related("reported_by", "station")
        return [
            [i.get_incident_type_display(), str(i.station), str(i.reported_by), i.status, i.created_at.strftime("%Y-%m-%d")]
            for i in incidents
        ]


class LeaveBalancesReportView(BaseReportView):
    title = "Leave Balances Report"
    headers = ["Guard", "Leave Type", "Available", "Used", "Expired"]

    def get_rows(self, request):
        balances = LeaveBalance.objects.select_related("guard")
        return [
            [str(b.guard), b.get_leave_type_display(), float(b.available_days), float(b.used_days), float(b.expired_days)]
            for b in balances
        ]


class AttendanceReportView(BaseReportView):
    title = "Attendance Report"
    headers = ["Guard", "Date", "Clock In", "Clock Out", "Late", "Absent"]

    def get_rows(self, request):
        records = Attendance.objects.select_related("shift", "shift__guard")
        if request.user.role == "guard":
            records = records.filter(shift__guard=request.user)
        elif request.user.role == "supervisor":
            station = getattr(getattr(request.user, "guard_profile", None), "station", None)
            if station is not None:
                records = records.filter(shift__station=station)
        rows = []
        for a in records:
            rows.append([
                str(a.shift.guard), a.shift.date.isoformat(),
                a.clock_in.strftime("%H:%M") if a.clock_in else "-",
                a.clock_out.strftime("%H:%M") if a.clock_out else "-",
                "Yes" if a.is_late else "No", "Yes" if a.is_absent else "No",
            ])
        return rows


class PatrolComplianceReportView(BaseReportView):
    title = "Patrol Compliance Report"
    headers = ["Guard", "Station", "Started", "Finished", "Status", "Checkpoints Visited"]

    def get_rows(self, request):
        patrols = self.scope(Patrol.objects.all(), request, "guard").select_related("guard", "station").prefetch_related("logs")
        return [
            [str(p.guard), str(p.station), p.started_at.strftime("%Y-%m-%d %H:%M"),
             p.finished_at.strftime("%Y-%m-%d %H:%M") if p.finished_at else "-", p.status, p.logs.count()]
            for p in patrols
        ]


class HolidayCompensationReportView(BaseReportView):
    title = "Holiday Compensation Report"
    headers = ["Guard", "Holiday", "Days Credited", "Date"]

    def get_rows(self, request):
        logs = PublicHolidayWorkLog.objects.select_related("guard", "holiday")
        return [[str(l.guard), l.holiday.name, float(l.days_credited), l.created_at.strftime("%Y-%m-%d")] for l in logs]


class ExamDutiesReportView(BaseReportView):
    title = "Exam Duties Report"
    headers = ["Guard", "Exam", "Venue", "Start", "End"]

    def get_rows(self, request):
        assignments = ExamAssignment.objects.select_related("guard", "exam")
        return [
            [str(a.guard), a.exam.name, a.exam.venue, a.exam.start_date.isoformat(), a.exam.end_date.isoformat()]
            for a in assignments
        ]


class EscortDutiesReportView(BaseReportView):
    title = "Escort Duties Report"
    headers = ["Guard", "Destination", "Departure", "Return", "Status"]

    def get_rows(self, request):
        missions = EscortMission.objects.select_related("escort_guard")
        return [
            [str(m.escort_guard), m.destination, m.departure.strftime("%Y-%m-%d %H:%M"),
             m.return_date.strftime("%Y-%m-%d %H:%M") if m.return_date else "-",
             "Active" if m.is_active else "Completed"]
            for m in missions
        ]


class AdminSummaryView(APIView):
    """Private aggregate data for the administrator-only mobile dashboard."""
    permission_classes = [IsAdministrator]

    def get(self, request):
        today = timezone.localdate()
        return Response({
            "active_patrols": Patrol.objects.filter(status=Patrol.Status.IN_PROGRESS).count(),
            "open_incidents": IncidentReport.objects.exclude(status=IncidentReport.Status.RESOLVED).count(),
            "today_ob_entries": OccurrenceBookEntry.objects.filter(created_at__date=today).count(),
            "attendance_records": Attendance.objects.filter(shift__date=today).count(),
        })