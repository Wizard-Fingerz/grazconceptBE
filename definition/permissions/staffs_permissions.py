from rest_framework import permissions

class CanCreateStaffs(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        required_permissions = ['create staffs']

        if user.role is not None and (
            user.role.permissions.filter(name__in=required_permissions).exists()
            or any(perm.name in required_permissions for perm in user.extra_permissions.all())
        ):
            return True

        return False
    
class CanUpdateStaffs(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        required_permissions = ['update staffs']

        if user.role is not None and (
            user.role.permissions.filter(name__in=required_permissions).exists()
            or any(perm.name in required_permissions for perm in user.extra_permissions.all())
        ):
            return True

        return False

class CanDeleteStaffs(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        required_permissions = ['delete staffs']

        if user.role is not None and (
            user.role.permissions.filter(name__in=required_permissions).exists()
            or any(perm.name in required_permissions for perm in user.extra_permissions.all())
        ):
            return True

        return False
    
class CanViewStaffs(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        required_permissions = ['view staffs']

        if user.role is not None and (
            user.role.permissions.filter(name__in=required_permissions).exists()
            or any(perm.name in required_permissions for perm in user.extra_permissions.all())
        ):
            return True

        return False
    
class CanResetStaffPassword(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        required_permissions = ['can reset staff password']

        if user.role is not None and (
            user.role.permissions.filter(name__in=required_permissions).exists()
            or any(perm.name in required_permissions for perm in user.extra_permissions.all())
        ):
            return True

        return False