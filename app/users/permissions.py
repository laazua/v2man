"""Custom permission classes for the v2man API."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUser(BasePermission):
    """Allow access only to staff users."""

    def has_permission(self, request, view) -> bool:
        """Check if the requesting user is a staff member."""
        return bool(request.user and request.user.is_staff)


class IsAdminOrReadOnly(BasePermission):
    """Allow read access to anyone; write access only to staff."""

    def has_permission(self, request, view) -> bool:
        """Check permissions based on request method and staff status."""
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsOwnerOrAdmin(BasePermission):
    """Allow access if the user is the owner or a staff member."""

    def has_object_permission(self, request, view, obj) -> bool:
        """Check object-level permission for ownership or admin status."""
        if request.user.is_staff:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'id'):
            return obj == request.user
        return False
