from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from accounts.models import User


def tenant_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.TENANT:
            raise PermissionDenied('Only Tenant accounts can access this page.')
        return view_func(request, *args, **kwargs)
    return wrapper


def owner_or_hotel_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in (User.Role.OWNER, User.Role.HOTEL):
            raise PermissionDenied('Only Property Owner and Hotel/Homestay Owner accounts can access this page.')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in User.INTERNAL_ROLES:
            raise PermissionDenied('Only Admin and Super Admin accounts can access this page.')
        return view_func(request, *args, **kwargs)
    return wrapper


def super_admin_required(view_func):
    """Stricter than admin_required — for the two things a regular Admin
    shouldn't be able to do: manage other admin accounts, or change
    platform-wide Settings (Feature 13's deliberately simple RBAC)."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.SUPER_ADMIN:
            raise PermissionDenied('Only Super Admin accounts can access this page.')
        return view_func(request, *args, **kwargs)
    return wrapper
