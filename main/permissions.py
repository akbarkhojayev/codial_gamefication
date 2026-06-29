from rest_framework.permissions import BasePermission


def is_admin_user(user):
    return bool(
        user
        and user.is_authenticated
        and (getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'admin')
    )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_admin_user(request.user)

class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and (is_admin_user(request.user) or request.user.role == 'teacher')
        )

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'

class IsAdminOrTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and (is_admin_user(request.user) or request.user.role == 'teacher')
        )
