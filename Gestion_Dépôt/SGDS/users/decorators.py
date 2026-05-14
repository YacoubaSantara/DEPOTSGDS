from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .permissions import (
    _has_role, is_superadmin, is_chef_depot,
    can_write, can_manage_users, can_view_audit, can_export, can_manage_roles,
)


# ── Décorateurs function-based views ───────────────────────────────────────────
def role_required(*codes):
    """
    Restreint une vue Django à certains codes de rôle.
    Redirige vers login si non authentifié, 403 si rôle insuffisant.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Veuillez vous connecter.")
                return redirect('connexion')
            if not _has_role(request.user, *codes):
                messages.error(request, "Accès refusé : rôle insuffisant.")
                return HttpResponseForbidden(
                    "Vous n'avez pas les droits pour accéder à cette ressource."
                )
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def superadmin_required(view_func):
    return role_required('SUPERADMIN')(view_func)


def chef_depot_required(view_func):
    return role_required('SUPERADMIN', 'CHEF_DEPOT')(view_func)


def can_write_required(view_func):
    return role_required('SUPERADMIN', 'CHEF_DEPOT', 'OPERATEUR')(view_func)


# ── Mixins class-based views ───────────────────────────────────────────────────
class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_superadmin(self.request.user)


class ChefDepotRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_chef_depot(self.request.user)


class CanWriteMixin(UserPassesTestMixin):
    def test_func(self):
        return can_write(self.request.user)


class CanManageUsersMixin(UserPassesTestMixin):
    def test_func(self):
        return can_manage_users(self.request.user)


class CanManageRolesMixin(UserPassesTestMixin):
    def test_func(self):
        return can_manage_roles(self.request.user)


class CanViewAuditMixin(UserPassesTestMixin):
    def test_func(self):
        return can_view_audit(self.request.user)


class CanExportMixin(UserPassesTestMixin):
    def test_func(self):
        return can_export(self.request.user)
