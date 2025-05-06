from rest_framework import permissions


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow users to edit their own profile.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the user itself
        return obj == request.user


class IsRater(permissions.BasePermission):
    """
    Custom permission to only allow users to edit their own ratings.
    """
    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the rater
        return obj.rater == request.user


class IsTeacher(permissions.BasePermission):
    """
    Custom permission to only allow teachers to access.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'


class IsTechnician(permissions.BasePermission):
    """
    Custom permission to only allow technicians to access.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'technician'


class IsStudent(permissions.BasePermission):
    """
    Custom permission to only allow students to access.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'