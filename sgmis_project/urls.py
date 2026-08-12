from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from apps.accounts.views import EmployeeNumberTokenObtainPairView, UserViewSet

schema_view = get_schema_view(
    openapi.Info(
        title="SGMIS API",
        default_version="v1",
        description="Security Guard Management Information System API",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth
    path("api/auth/login/", EmployeeNumberTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/register/", UserViewSet.as_view({"post": "register"}), name="user-register"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),

    # App modules
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/ob/", include("apps.occurrence_book.urls")),
    path("api/patrols/", include("apps.patrols.urls")),
    path("api/shifts/", include("apps.shifts.urls")),
    path("api/leave/", include("apps.leave_management.urls")),
    path("api/exams/", include("apps.exam_management.urls")),
    path("api/escorts/", include("apps.escort_management.urls")),
    path("api/incidents/", include("apps.incidents.urls")),
    path("api/visitors/", include("apps.visitors.urls")),
    path("api/registers/", include("apps.registers.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/reports/", include("apps.reports.urls")),

    # API docs
    path("api/docs/", schema_view.with_ui("swagger", cache_timeout=0), name="api-docs"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
