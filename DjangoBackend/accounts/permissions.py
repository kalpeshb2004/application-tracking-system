from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allows only logged-in, active users whose role is 'admin'."""

    message = "Admin only"

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.is_active and user.role == "admin"
        )