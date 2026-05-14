"""
Backend qui fait fonctionner user.has_perm('codename') en lisant
UserProfile.role.permissions au lieu des Groups Django natifs.
"""
from django.contrib.auth.backends import ModelBackend


class RoleBasedPermissionBackend(ModelBackend):

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj or user_obj.is_anonymous:
            return set()

        profil = getattr(user_obj, 'profile', None)
        if not profil or not profil.actif or not profil.role:
            return set()

        if not hasattr(user_obj, '_perm_cache_role'):
            perms = profil.role.permissions.values_list(
                'content_type__app_label', 'codename'
            )
            user_obj._perm_cache_role = {
                f"{app}.{code}" for app, code in perms
            }
            # Aussi sans préfixe app_label (syntaxe courte `has_perm('codename')`)
            user_obj._perm_cache_role |= {code for _, code in perms}
        return user_obj._perm_cache_role

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_active:
            return False
        # SUPERADMIN raccourci : toutes les permissions (sauf si profil inactif)
        profil = getattr(user_obj, 'profile', None)
        if profil and profil.actif and profil.role and profil.role.code == 'SUPERADMIN':
            return True
        return perm in self.get_all_permissions(user_obj, obj)
