"""
Helpers de permissions. Basés sur user.has_perm() Django (backend RoleBasedPermissionBackend).
"""


def _user_actif(user):
    if not user or not user.is_authenticated:
        return False
    profil = getattr(user, 'profile', None)
    return bool(profil and profil.actif and profil.role)


def has_perm(user, codename):
    if not _user_actif(user):
        return False
    return user.has_perm(codename)


def _has_role(user, *codes):
    """Conservé pour compatibilité avec les décorateurs existants."""
    if not _user_actif(user):
        return False
    return user.profile.role.code in codes


def is_superadmin(user):
    return _has_role(user, 'SUPERADMIN')


def is_chef_depot(user):
    return _has_role(user, 'SUPERADMIN', 'CHEF_DEPOT')


def can_write(user):
    return has_perm(user, 'ajouter_mouvement') or has_perm(user, 'ajouter_jaugeage')


def can_close_period(user):
    return has_perm(user, 'cloturer_periode')


def can_validate_jaugeage(user):
    return has_perm(user, 'valider_jaugeage')


def can_delete_mouvement(user):
    return has_perm(user, 'supprimer_mouvement')


def can_manage_users(user):
    return has_perm(user, 'gerer_utilisateur')


def can_manage_roles(user):
    return has_perm(user, 'gerer_role')


def can_view_audit(user):
    return has_perm(user, 'voir_audit')


def can_export(user):
    if not _user_actif(user):
        return False
    return user.profile.role.permissions.filter(
        codename__startswith='exporter_'
    ).exists()
