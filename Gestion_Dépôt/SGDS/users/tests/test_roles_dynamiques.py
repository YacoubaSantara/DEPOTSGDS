"""
Tests du système RBAC dynamique (Role model + backend + vues).
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.urls import reverse

from SGDS.users.models import Role, UserProfile

User = get_user_model()


def _get_perm(codename):
    ct = ContentType.objects.get_for_model(UserProfile)
    return Permission.objects.get(codename=codename, content_type=ct)


def _make_user(username, role_code, actif=True):
    """Crée un User + UserProfile avec le rôle dont le code est role_code."""
    user = User.objects.create_user(username=username, password='test1234')
    role = Role.objects.get(code=role_code)
    profile = user.profile
    profile.role = role
    profile.actif = actif
    profile.save()
    return user


class RolesDynamiquesTests(TestCase):
    """Tests unitaires sur le modèle Role et le backend de permissions."""

    def test_cinq_roles_systeme_existent(self):
        """Les 5 rôles système doivent exister après migration."""
        codes = set(Role.objects.filter(systeme=True).values_list('code', flat=True))
        self.assertEqual(codes, {'SUPERADMIN', 'CHEF_DEPOT', 'OPERATEUR', 'COMPTABLE', 'LECTEUR'})

    def test_superadmin_a_toutes_les_permissions(self):
        """SUPERADMIN doit avoir au moins les 35 permissions métier."""
        sa = Role.objects.get(code='SUPERADMIN')
        self.assertGreaterEqual(sa.permissions.count(), 35)

    def test_role_systeme_ne_peut_pas_etre_supprime(self):
        """Un rôle système doit lever ValidationError à la suppression."""
        role = Role.objects.get(code='LECTEUR')
        with self.assertRaises(ValidationError):
            role.delete()

    def test_code_role_immutable(self):
        """Modifier le code d'un rôle existant doit lever ValueError."""
        role = Role.objects.get(code='OPERATEUR')
        role.code = 'NOUVEAU_CODE'
        with self.assertRaises(ValueError):
            role.save()

    def test_role_avec_utilisateur_ne_peut_pas_etre_supprime(self):
        """Un rôle personnalisé attribué à un utilisateur ne peut pas être supprimé."""
        role_custom = Role.objects.create(nom='Role Test', code='ROLE_TEST', systeme=False)
        user = _make_user('test_user_block', 'LECTEUR')
        user.profile.role = role_custom
        user.profile.save()
        with self.assertRaises(ValidationError):
            role_custom.delete()

    def test_role_sans_utilisateur_peut_etre_supprime(self):
        """Un rôle personnalisé sans utilisateurs peut être supprimé."""
        role_custom = Role.objects.create(nom='Role Vide', code='ROLE_VIDE', systeme=False)
        pk = role_custom.pk
        role_custom.delete()
        self.assertFalse(Role.objects.filter(pk=pk).exists())

    def test_backend_superadmin_a_toutes_perms(self):
        """has_perm retourne True pour SUPERADMIN quelle que soit la permission."""
        user = _make_user('sa_test', 'SUPERADMIN')
        self.assertTrue(user.has_perm('voir_mouvement'))
        self.assertTrue(user.has_perm('gerer_role'))
        self.assertTrue(user.has_perm('une_permission_inventee'))

    def test_backend_lecteur_a_permissions_limitees(self):
        """LECTEUR ne peut pas créer de mouvement."""
        user = _make_user('lecteur_test', 'LECTEUR')
        self.assertTrue(user.has_perm('voir_mouvement'))
        self.assertFalse(user.has_perm('ajouter_mouvement'))
        self.assertFalse(user.has_perm('gerer_role'))

    def test_backend_user_inactif_na_aucune_permission(self):
        """Un utilisateur inactif (actif=False) ne doit avoir aucune permission."""
        user = _make_user('inactif_test', 'SUPERADMIN', actif=False)
        self.assertFalse(user.has_perm('voir_mouvement'))
        self.assertFalse(user.has_perm('gerer_role'))

    def test_nb_utilisateurs_property(self):
        """Role.nb_utilisateurs doit compter les UserProfile associés."""
        role = Role.objects.get(code='COMPTABLE')
        count_before = role.nb_utilisateurs
        _make_user('comptable_test', 'COMPTABLE')
        role.refresh_from_db()
        self.assertEqual(role.nb_utilisateurs, count_before + 1)

    def test_creation_role_personnalise_avec_permissions(self):
        """On peut créer un rôle custom et lui assigner des permissions."""
        role = Role.objects.create(nom='Superviseur', code='SUPERVISEUR')
        perm = _get_perm('voir_mouvement')
        role.permissions.add(perm)
        user = _make_user('supervisor_test', 'SUPERVISEUR')
        user.profile.role = role
        user.profile.save()
        # Invalider le cache de permissions
        if hasattr(user, '_perm_cache_role'):
            del user._perm_cache_role
        self.assertTrue(user.has_perm('voir_mouvement'))
        self.assertFalse(user.has_perm('ajouter_mouvement'))


class VuesRolesTests(TestCase):
    """Tests d'intégration des vues RBAC (accès, création, modification)."""

    def setUp(self):
        self.client = Client()
        self.superadmin = _make_user('admin_vues', 'SUPERADMIN')
        self.lecteur = _make_user('lecteur_vues', 'LECTEUR')

    def test_liste_roles_accessible_superadmin(self):
        """La liste des rôles est accessible par un SUPERADMIN."""
        self.client.force_login(self.superadmin)
        resp = self.client.get(reverse('roles_liste'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('roles', resp.context)

    def test_liste_roles_interdit_lecteur(self):
        """Un LECTEUR ne peut pas accéder à la liste des rôles."""
        self.client.force_login(self.lecteur)
        resp = self.client.get(reverse('roles_liste'))
        self.assertIn(resp.status_code, [302, 403])

    def test_creer_role_get(self):
        """Le formulaire de création de rôle est accessible par SUPERADMIN."""
        self.client.force_login(self.superadmin)
        resp = self.client.get(reverse('roles_creer'))
        self.assertEqual(resp.status_code, 200)

    def test_creer_role_post(self):
        """La création d'un rôle via POST fonctionne et redirige."""
        self.client.force_login(self.superadmin)
        resp = self.client.post(reverse('roles_creer'), {
            'nom': 'Role Nouveau',
            'code': 'ROLE_NOUVEAU',
            'description': 'Un test',
            'couleur': 'blue',
            'permissions': [],
        }, follow=False)
        self.assertIn(resp.status_code, [302, 200])
        self.assertTrue(Role.objects.filter(code='ROLE_NOUVEAU').exists())

    def test_detail_role_accessible(self):
        """Le détail d'un rôle est accessible par SUPERADMIN."""
        role = Role.objects.get(code='CHEF_DEPOT')
        self.client.force_login(self.superadmin)
        resp = self.client.get(reverse('roles_detail', args=[role.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_supprimer_role_systeme_interdit(self):
        """La suppression d'un rôle système doit être refusée."""
        role = Role.objects.get(code='LECTEUR')
        self.client.force_login(self.superadmin)
        resp = self.client.post(reverse('roles_supprimer', args=[role.pk]))
        self.assertIn(resp.status_code, [302, 200])
        self.assertTrue(Role.objects.filter(code='LECTEUR').exists())

    def test_permissions_liste_accessible(self):
        """La liste des permissions est accessible par SUPERADMIN."""
        self.client.force_login(self.superadmin)
        resp = self.client.get(reverse('permissions_liste'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('groupes', resp.context)
