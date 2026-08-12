from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.permissions import IsSupervisorOrAdmin, IsOwnerOrSupervisor
from .models import LeaveBalance, LeaveAccrualLog, PublicHoliday, PublicHolidayWorkLog, LeaveApplication
from .serializers import (
    LeaveBalanceSerializer, LeaveAccrualLogSerializer, PublicHolidaySerializer,
    PublicHolidayWorkLogSerializer, LeaveApplicationSerializer,
)
from . import services


class LeaveBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """Balances are maintained by the accrual engine, not edited directly."""
    queryset = LeaveBalance.objects.select_related("guard").all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsOwnerOrSupervisor]
    filterset_fields = ["guard", "leave_type"]

    @action(detail=False, methods=["get"])
    def mine(self, request):
        balances = LeaveBalance.objects.filter(guard=request.user)
        return Response(LeaveBalanceSerializer(balances, many=True).data)


class LeaveAccrualLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeaveAccrualLog.objects.select_related("balance").all()
    serializer_class = LeaveAccrualLogSerializer
    permission_classes = [IsSupervisorOrAdmin]
    filterset_fields = ["balance"]


class PublicHolidayViewSet(viewsets.ModelViewSet):
    queryset = PublicHoliday.objects.all()
    serializer_class = PublicHolidaySerializer
    permission_classes = [IsSupervisorOrAdmin]


class PublicHolidayWorkLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PublicHolidayWorkLog.objects.select_related("guard", "holiday").all()
    serializer_class = PublicHolidayWorkLogSerializer
    permission_classes = [IsSupervisorOrAdmin]


class LeaveApplicationViewSet(viewsets.ModelViewSet):
    queryset = LeaveApplication.objects.select_related("guard", "reviewed_by").all()
    serializer_class = LeaveApplicationSerializer
    permission_classes = [IsOwnerOrSupervisor]
    filterset_fields = ["guard", "leave_type", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self.request.user, 'role', '') == "guard":
            return qs.filter(guard=self.request.user)
        return qs

    @action(detail=True, methods=["post"], permission_classes=[IsSupervisorOrAdmin])
    def approve(self, request, pk=None):
        application = self.get_object()
        try:
            services.approve_leave_application(application, request.user, request.data.get("comment", ""))
        except Exception as exc:
            error_message = str(exc) if str(exc) else "Leave balance does not exist or insufficient balance."
            return Response({"detail": error_message}, status=400)
        return Response(LeaveApplicationSerializer(application).data)

    @action(detail=True, methods=["post"], permission_classes=[IsSupervisorOrAdmin])
    def reject(self, request, pk=None):
        application = self.get_object()
        application.status = application.Status.REJECTED
        application.reviewed_by = request.user
        application.review_comment = request.data.get("comment", "")
        application.save(update_fields=["status", "reviewed_by", "review_comment", "updated_at"])
        return Response(LeaveApplicationSerializer(application).data)

    @action(detail=True, methods=["post"], permission_classes=[IsSupervisorOrAdmin])
    def request_changes(self, request, pk=None):
        application = self.get_object()
        application.status = application.Status.CHANGES_REQUESTED
        application.reviewed_by = request.user
        application.review_comment = request.data.get("comment", "")
        application.save(update_fields=["status", "reviewed_by", "review_comment", "updated_at"])
        return Response(LeaveApplicationSerializer(application).data)