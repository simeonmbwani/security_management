from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Visitor
from .serializers import VisitorSerializer


class VisitorViewSet(viewsets.ModelViewSet):
    queryset = Visitor.objects.select_related("station", "recorded_by").all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["station"]
    search_fields = ["full_name", "national_id", "vehicle_registration", "host"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(user, 'role', '').lower()
        
        # Restrict regular guards to their assigned station's visitors
        if role == "guard":
            station = getattr(getattr(user, "guard_profile", None), "station", None)
            if station:
                return qs.filter(station=station)
            from apps.shifts.models import Shift
            shift = Shift.objects.filter(guard=user, date=timezone.localdate()).select_related("station").first()
            if shift:
                return qs.filter(station=shift.station)
            return qs.none()
            
        return qs

    @action(detail=True, methods=["post"])
    def sign_out(self, request, pk=None):
        visitor = self.get_object()
        visitor.time_out = timezone.now()
        visitor.save(update_fields=["time_out"])
        return Response(VisitorSerializer(visitor).data)