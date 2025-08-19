from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class CanCreateSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            raise PermissionDenied("User is not authenticated.")

        if user.role.name != "superadmin":
            raise PermissionDenied("Only super admin users can access this route.")

        return True

