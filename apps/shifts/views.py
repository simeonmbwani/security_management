from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.permissions import IsSupervisorOrAdmin, IsOwnerOrSupervisor, ReadOnlyOrSupervisor
from apps.accounts.models import Station
from .models import ShiftHandover, Shift
from .serializers import ShiftHandoverSerializer
from .services import generate_roster_for_date
from .models import GuardPair, DutyRosterCycle, Shift, ShiftHandover, Attendance
from .serializers import (
    GuardPairSerializer, DutyRosterCycleSerializer, ShiftSerializer,
    ShiftHandoverSerializer, AttendanceSerializer, GenerateRosterSerializer,
)
from . import services


class GuardPairViewSet(viewsets.ModelViewSet):
    queryset = GuardPair.objects.select_related("guard_a", "guard_b", "station").all()
    serializer_class = GuardPairSerializer
    permission_classes = [IsSupervisorOrAdmin]
    filterset_fields = ["station", "is_active"]


class DutyRosterCycleViewSet(viewsets.ModelViewSet):
    queryset = DutyRosterCycle.objects.all()
    serializer_class = DutyRosterCycleSerializer
    permission_classes = [IsSupervisorOrAdmin]


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.select_related("guard", "station", "pair").all()
    serializer_class = ShiftSerializer
    permission_classes = [ReadOnlyOrSupervisor]
    filterset_fields = ["station", "guard", "date", "shift_type", "is_override"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == "guard":
            return qs.filter(guard=self.request.user)
        return qs

    @action(detail=False, methods=["get"])
    def today(self, request):
        """Return the logged-in guard's shift for today (used by mobile Dashboard)."""
        today = timezone.localdate()
        shift = Shift.objects.filter(guard=request.user, date=today).first()
        if not shift:
            return Response({"detail": "No shift scheduled for today."}, status=404)
        return Response(ShiftSerializer(shift).data)

    @action(detail=False, methods=["post"], permission_classes=[IsSupervisorOrAdmin])
    def generate(self, request):
        """Bulk-generate the automatic roster for a date range at a station."""
        serializer = GenerateRosterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        station = Station.objects.get(id=serializer.validated_data["station"])
        shifts = services.generate_roster_range(
            station, serializer.validated_data["start_date"], serializer.validated_data["end_date"]
        )
        return Response(ShiftSerializer(shifts, many=True).data, status=status.HTTP_201_CREATED)


class ShiftHandoverViewSet(viewsets.ModelViewSet):
    queryset = ShiftHandover.objects.select_related("outgoing_shift", "incoming_guard").all()
    serializer_class = ShiftHandoverSerializer

    def create(self, request, *args, **kwargs):
        user = request.user
        today = timezone.localdate()
        
        # Ensure roster rows exist for today if user has a guard profile station
        if hasattr(user, 'guard_profile') and user.guard_profile.station:
            generate_roster_for_date(user.guard_profile.station, today)

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related("shift").all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsOwnerOrSupervisor]

    @action(detail=False, methods=["post"])
    def clock_in(self, request):
        shift_id = request.data.get("shift")
        gps = request.data.get("gps", "")
        attendance, _ = Attendance.objects.get_or_create(shift_id=shift_id)
        attendance.clock_in = timezone.now()
        attendance.clock_in_gps = gps
        attendance.save()
        return Response(AttendanceSerializer(attendance).data)

    @action(detail=False, methods=["post"])
    def clock_out(self, request):
        shift_id = request.data.get("shift")
        gps = request.data.get("gps", "")
        attendance, _ = Attendance.objects.get_or_create(shift_id=shift_id)
        attendance.clock_out = timezone.now()
        attendance.clock_out_gps = gps
        attendance.save()
        return Response(AttendanceSerializer(attendance).data)
