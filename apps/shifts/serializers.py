from django.utils import timezone
from rest_framework import serializers
from .models import GuardPair, DutyRosterCycle, Shift, ShiftHandover, Attendance


class GuardPairSerializer(serializers.ModelSerializer):
    guard_a_name = serializers.CharField(source="guard_a.get_full_name", read_only=True)
    guard_b_name = serializers.CharField(source="guard_b.get_full_name", read_only=True)

    class Meta:
        model = GuardPair
        fields = ["id", "station", "name", "guard_a", "guard_a_name", "guard_b", "guard_b_name",
                  "rotation_order", "is_active"]


class DutyRosterCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyRosterCycle
        fields = ["id", "station", "cycle_start_date", "cycle_length_days"]


class ShiftSerializer(serializers.ModelSerializer):
    guard_name = serializers.CharField(source="guard.get_full_name", read_only=True)

    class Meta:
        model = Shift
        fields = ["id", "station", "guard", "guard_name", "date", "shift_type", "pair",
                  "is_override", "override_reason", "created_at"]
        read_only_fields = ["created_at"]

class ShiftHandoverSerializer(serializers.ModelSerializer):
    outgoing_shift_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = ShiftHandover
        fields = [
            "id", "outgoing_shift", "outgoing_shift_id", "incoming_guard",
            "occurrence_summary", "equipment_issued", "keys_handed_over",
            "pending_issues", "outgoing_signed", "incoming_accepted",
            "incoming_accepted_at", "created_at"
        ]
        read_only_fields = ["outgoing_shift", "incoming_guard", "incoming_accepted_at", "created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        today = timezone.localdate()
        yesterday = today - timezone.timedelta(days=1)
        
        explicit_shift_id = validated_data.pop("outgoing_shift_id", None)

        # 1. Resolve outgoing shift (either explicit ID or look up today's/yesterday's shift)
        if explicit_shift_id:
            try:
                outgoing_shift = Shift.objects.get(id=explicit_shift_id)
            except Shift.DoesNotExist:
                raise serializers.ValidationError({"detail": "Invalid shift ID provided."})
        else:
            outgoing_shift = (
                Shift.objects.filter(guard=user, date__gte=yesterday, date__lte=today)
                .order_by("-date", "-created_at")
                .first()
            )

        if outgoing_shift is None:
            raise serializers.ValidationError({
                "detail": "No active or scheduled shift found for your user. Please check today's roster."
            })

        # 2. STRICT 12-HOUR DURATION VALIDATION
        now = timezone.now()
        elapsed_hours = (now - outgoing_shift.created_at).total_seconds() / 3600.0

        # Enforce strict 12-hour window (allowing a tight buffer between 11.5 and 12.5 hours)
        if elapsed_hours < 11.5 or elapsed_hours > 12.5:
            raise serializers.ValidationError({
                "detail": f"Handover rejected. Shifts must be strictly 12 hours duration. Current elapsed time: {elapsed_hours:.1f} hours."
            })

        # 3. Check duplicate submission
        if hasattr(outgoing_shift, "handover"):
            raise serializers.ValidationError({
                "detail": "A handover record has already been submitted for this shift."
            })

        # 4. Resolve incoming guard
        incoming_shift = (
            Shift.objects.filter(station=outgoing_shift.station, date__gte=outgoing_shift.date)
            .exclude(guard=user)
            .order_by("date", "created_at")
            .first()
        )

        if incoming_shift is None:
            # Fallback to any active guard at the station if no future shift is rostered yet
            User = outgoing_shift.guard.__class__
            incoming_guard = User.objects.filter(
                guard_profile__station=outgoing_shift.station, role="guard"
            ).exclude(id=user.id).first()
            if incoming_guard is None:
                raise serializers.ValidationError({
                    "detail": "No incoming guard is registered or scheduled for this station."
                })
        else:
            incoming_guard = incoming_shift.guard

        validated_data["outgoing_shift"] = outgoing_shift
        validated_data["incoming_guard"] = incoming_guard
        validated_data["outgoing_signed"] = True
        return super().create(validated_data)


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ["id", "shift", "clock_in", "clock_out", "clock_in_gps", "clock_out_gps",
                  "is_late", "is_absent"]


class GenerateRosterSerializer(serializers.Serializer):
    station = serializers.UUIDField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()