from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import KeyRegisterItem, EquipmentItem
from .serializers import KeyRegisterItemSerializer, EquipmentItemSerializer


class KeyRegisterViewSet(viewsets.ModelViewSet):
    queryset = KeyRegisterItem.objects.select_related("issued_to", "station").all()
    serializer_class = KeyRegisterItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["station", "issued_to"]

    @action(detail=True, methods=["post"])
    def return_key(self, request, pk=None):
        item = self.get_object()
        item.returned_at = timezone.now()
        item.save(update_fields=["returned_at"])
        return Response(KeyRegisterItemSerializer(item).data)

    @action(detail=False, methods=["get"])
    def outstanding(self, request):
        items = self.get_queryset().filter(returned_at__isnull=True)
        return Response(KeyRegisterItemSerializer(items, many=True).data)


class EquipmentRegisterViewSet(viewsets.ModelViewSet):
    queryset = EquipmentItem.objects.select_related("issued_to", "station").all()
    serializer_class = EquipmentItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["station", "issued_to", "equipment_type"]

    @action(detail=True, methods=["post"])
    def return_item(self, request, pk=None):
        item = self.get_object()
        item.returned_at = timezone.now()
        item.condition_in = request.data.get("condition_in", EquipmentItem.Condition.GOOD)
        item.save(update_fields=["returned_at", "condition_in"])
        return Response(EquipmentItemSerializer(item).data)

    @action(detail=False, methods=["get"])
    def outstanding(self, request):
        items = self.get_queryset().filter(returned_at__isnull=True)
        return Response(EquipmentItemSerializer(items, many=True).data)
