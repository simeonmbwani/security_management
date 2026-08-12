from rest_framework import permissions


class IsAdministrator(permissions.BasePermission):
    """Full access — Administrator role only."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "administrator")


class IsSupervisorOrAdmin(permissions.BasePermission):
    """Supervisors and Administrators can approve, assign, and manage guards."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("administrator", "supervisor")
        )


class IsOwnerOrSupervisor(permissions.BasePermission):
    """
    Guards may view/edit their own records (e.g. their own OB entries, leave
    applications). Supervisors/Admins can view/edit everything.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in ("administrator", "supervisor"):
            return True
        if getattr(obj, "incoming_guard", None) == user:
            return True
        if getattr(getattr(obj, "outgoing_shift", None), "guard", None) == user:
            return True
        owner = (
            getattr(obj, "guard", None)
            or getattr(obj, "user", None)
            or getattr(obj, "reported_by", None)
        )
        return owner == user


class ReadOnlyOrSupervisor(permissions.BasePermission):
    """Anyone authenticated can read; only supervisors/admins can write."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("administrator", "supervisor")
        )
