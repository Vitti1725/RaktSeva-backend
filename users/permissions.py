from rest_framework.permissions import BasePermission

class IsDonorUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'donor'
        )

class IsHospitalUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'hospital'
        )

class IsHospitalOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.role == 'hospital' or request.user.is_superuser)
        )

class IsActiveDonor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'donor' and
            hasattr(request.user, 'donor')
        )

class IsActiveHospital(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'hospital' and
            hasattr(request.user, 'hospital')
        )