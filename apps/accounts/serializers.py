from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError as DRFValidationError
from .models import GuardProfile, Station

User = get_user_model()


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ["id", "name", "address", "is_active"]


class GuardProfileSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source="station.name", read_only=True)

    class Meta:
        model = GuardProfile
        fields = [
            "id", "user", "station", "station_name", "rank", "date_employed",
            "national_id", "next_of_kin", "next_of_kin_phone", "photo",
            "is_on_escort_duty",
        ]
        read_only_fields = ["is_on_escort_duty"]


class UserSerializer(serializers.ModelSerializer):
    guard_profile = GuardProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "employee_number", "first_name", "last_name",
            "email", "phone", "role", "is_staff", "is_superuser", 
            "is_active_employee", "guard_profile",
        ]
        read_only_fields = [
            "id", "employee_number", "role", "is_staff", "is_superuser", 
            "is_active_employee", "guard_profile"
        ]
class PublicUserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    station = serializers.PrimaryKeyRelatedField(queryset=Station.objects.all(), write_only=True, required=False, allow_null=True)
    rank = serializers.ChoiceField(choices=GuardProfile.Rank.choices, write_only=True, required=False)
    date_employed = serializers.DateField(write_only=True, required=False)
    guard_profile = GuardProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "employee_number", "first_name", "last_name",
            "email", "phone", "role", "password", "password_confirm", "station",
            "rank", "date_employed", "guard_profile",
        ]
        read_only_fields = ["id", "employee_number", "guard_profile"]
        extra_kwargs = {"role": {"required": False}}

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        password_confirm = validated_data.pop("password_confirm")
        station = validated_data.pop("station", None)
        rank = validated_data.pop("rank", GuardProfile.Rank.GUARD)
        date_employed = validated_data.pop("date_employed", None)
        password = validated_data.pop("password")
        role = validated_data.pop("role", User.Role.GUARD)

        user = User(**validated_data, role=role)
        user.set_password(password)
        user.save()

        GuardProfile.objects.create(
            user=user,
            station=station,
            rank=rank,
            date_employed=date_employed or user.date_joined.date(),
        )
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    station = serializers.PrimaryKeyRelatedField(queryset=Station.objects.all(), write_only=True, required=False)
    rank = serializers.ChoiceField(choices=GuardProfile.Rank.choices, write_only=True, required=False)
    date_employed = serializers.DateField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id", "username", "employee_number", "first_name", "last_name",
            "email", "phone", "role", "password", "station", "rank", "date_employed",
        ]

    def create(self, validated_data):
        station = validated_data.pop("station", None)
        rank = validated_data.pop("rank", GuardProfile.Rank.GUARD)
        date_employed = validated_data.pop("date_employed", None)
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        GuardProfile.objects.create(
            user=user, station=station, rank=rank,
            date_employed=date_employed or user.date_joined.date(),
        )
        return user


class EmployeeNumberTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username_or_employee = attrs.get("username")
        password = attrs.get("password")

        if username_or_employee and password:
            user = authenticate(
                request=self.context.get("request"),
                username=username_or_employee,
                password=password,
            )
            if user is None:
                try:
                    owner = User.objects.get(employee_number=username_or_employee)
                except User.DoesNotExist:
                    owner = None

                if owner is not None:
                    user = authenticate(
                        request=self.context.get("request"),
                        username=owner.username,
                        password=password,
                    )

            if user is None or not user.is_active:
                raise DRFValidationError({"detail": "No active account found with the given credentials."})

            validated = super().validate({"username": user.username, "password": password})
            return validated

        return super().validate(attrs)
