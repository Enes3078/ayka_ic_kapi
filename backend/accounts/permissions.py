from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    """Sadece admin rolüne sahip kullanıcılar erişebilir."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsManagerRole(permissions.BasePermission):
    """Sadece manager rolüne sahip kullanıcılar erişebilir."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'manager'
        )


class IsAdminOrManager(permissions.BasePermission):
    """Admin veya Manager rolündeki kullanıcılar erişebilir."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('admin', 'manager')
        )
