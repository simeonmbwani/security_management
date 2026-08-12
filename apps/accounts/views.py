from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from core.permissions import IsAdministrator, IsSupervisorOrAdmin
from .models import Station, GuardProfile
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    PublicUserRegistrationSerializer,
    StationSerializer,
    GuardProfileSerializer,
    EmployeeNumberTokenObtainPairSerializer,
)

User = get_user_model()


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [IsAdministrator]


class UserViewSet(viewsets.ModelViewSet):
    """
    Administrators manage all users. Supervisors can list guards at their
    station. Guards can only view/update their own record via /me/.
    """
    queryset = User.objects.select_related("guard_profile", "guard_profile__station").all()

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == "register":
            return [permissions.AllowAny()]
        if self.action in ("create", "destroy"):
            return [IsAdministrator()]
        if self.action in ("update", "partial_update", "list"):
            return [IsSupervisorOrAdmin()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        if request.method == "GET":
            return Response(UserSerializer(request.user).data)
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Profile pictures are stored on the guard profile, not the user row.
        # Accepting this here keeps the mobile profile editor to one endpoint.
        photo = request.FILES.get("photo")
        if photo:
            profile, _ = GuardProfile.objects.get_or_create(
                user=request.user, defaults={"date_employed": request.user.date_joined.date()}
            )
            profile.photo = photo
            profile.save(update_fields=["photo"])
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def register(self, request):
        serializer = PublicUserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class EmployeeNumberTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmployeeNumberTokenObtainPairSerializer


class GuardProfileViewSet(viewsets.ModelViewSet):
    queryset = GuardProfile.objects.select_related("user", "station").all()
    serializer_class = GuardProfileSerializer
    permission_classes = [IsSupervisorOrAdmin]
    filterset_fields = ["station", "rank", "is_on_escort_duty"]
