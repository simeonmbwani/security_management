from rest_framework import serializers
from .models import Checkpoint, Patrol, PatrolCheckpointLog


class CheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checkpoint
        fields = ["id", "station", "name", "order", "latitude", "longitude", "is_active"]


class PatrolCheckpointLogSerializer(serializers.ModelSerializer):
    checkpoint_name = serializers.CharField(source="checkpoint.name", read_only=True)

    class Meta:
        model = PatrolCheckpointLog
        fields = ["id", "patrol", "checkpoint", "checkpoint_name", "visited_at",
                  "latitude", "longitude", "comment", "photo", "is_flagged"]
        read_only_fields = ["visited_at"]


class PatrolSerializer(serializers.ModelSerializer):
    guard_name = serializers.CharField(source="guard.get_full_name", read_only=True)
    logs = PatrolCheckpointLogSerializer(many=True, read_only=True)
    checkpoints_visited = serializers.IntegerField(source="logs.count", read_only=True)

    class Meta:
        model = Patrol
        fields = ["id", "station", "guard", "guard_name", "started_at", "finished_at",
                  "status", "logs", "checkpoints_visited"]
        read_only_fields = ["station", "guard", "started_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        station = getattr(getattr(user, "guard_profile", None), "station", None)
        if station is None:
            raise serializers.ValidationError({"station": "Assign this guard to a station before starting a patrol."})
        validated_data["guard"] = user
        validated_data["station"] = station
        return super().create(validated_data)
