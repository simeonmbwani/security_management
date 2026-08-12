from rest_framework import serializers
from .models import EscortMission


class EscortMissionSerializer(serializers.ModelSerializer):
    escort_guard_name = serializers.CharField(source="escort_guard.get_full_name", read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = EscortMission
        fields = [
            "id", "destination", "driver_name", "vehicle_registration", "escort_guard",
            "escort_guard_name", "departure", "return_date", "mileage_out", "mileage_in",
            "fuel_litres", "remarks", "created_by", "created_at", "is_active",
        ]
        # Make escort_guard optional in the incoming JSON payload so it can be auto-assigned
        extra_kwargs = {"escort_guard": {"required": False}}
        read_only_fields = ["created_by", "created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["created_by"] = user
        
        # If 'escort_guard' wasn't sent in the request (e.g. guard creating their own), default to the logged-in user
        if "escort_guard" not in validated_data:
            validated_data["escort_guard"] = user
            
        return super().create(validated_data)