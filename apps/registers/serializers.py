from rest_framework import serializers
from .models import KeyRegisterItem, EquipmentItem


class KeyRegisterItemSerializer(serializers.ModelSerializer):
    issued_to_name = serializers.CharField(source="issued_to.get_full_name", read_only=True)
    is_outstanding = serializers.BooleanField(read_only=True)

    class Meta:
        model = KeyRegisterItem
        fields = ["id", "station", "key_number", "description", "issued_to", "issued_to_name",
                  "issued_at", "returned_at", "is_outstanding"]
        read_only_fields = ["issued_at"]


class EquipmentItemSerializer(serializers.ModelSerializer):
    issued_to_name = serializers.CharField(source="issued_to.get_full_name", read_only=True)
    is_outstanding = serializers.BooleanField(read_only=True)

    class Meta:
        model = EquipmentItem
        fields = ["id", "station", "equipment_type", "serial_number", "issued_to", "issued_to_name",
                  "issued_at", "returned_at", "condition_out", "condition_in", "is_outstanding"]
        read_only_fields = ["issued_at"]
