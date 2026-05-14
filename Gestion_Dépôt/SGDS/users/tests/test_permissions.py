from django.test import TestCase

from SGDS.users.managers import creer_utilisateur
from SGDS.users.models import Role
from SGDS.users.permissions import (
    can_close_period, can_export, can_manage_users, can_view_audit,
    can_write, is_chef_depot, is_superadmin,
)


class PermissionsTests(TestCase):

    def setUp(self):
        self.superadmin = creer_utilisateur(
            'superadmin', 'sa@sgds.ml', 'pass12345', Role.SUPERADMIN)
        self.chef = creer_utilisateur(
            'chef', 'chef@sgds.ml', 'pass12345', Role.CHEF_DEPOT)
        self.operateur = creer_utilisateur(
            'ope', 'ope@sgds.ml', 'pass12345', Role.OPERATEUR)
        self.comptable = creer_utilisateur(
            'cpt', 'cpt@sgds.ml', 'pass12345', Role.COMPTABLE)
        self.lecteur = creer_utilisateur(
            'lec', 'lec@sgds.ml', 'pass12345', Role.LECTEUR)

    # ── SUPERADMIN ─────────────────────────────────────────────────────────────
    def test_superadmin_a_tous_les_droits(self):
        u = self.superadmin
        self.assertTrue(is_superadmin(u))
        self.assertTrue(is_chef_depot(u))
        self.assertTrue(can_write(u))
        self.assertTrue(can_close_period(u))
        self.assertTrue(can_manage_users(u))
        self.assertTrue(can_view_audit(u))
        self.assertTrue(can_export(u))

    def test_superadmin_is_staff_et_is_superuser(self):
        self.assertTrue(self.superadmin.is_staff)
        self.assertTrue(self.superadmin.is_superuser)

    # ── CHEF_DEPOT ─────────────────────────────────────────────────────────────
    def test_chef_depot_peut_cloturer(self):
        u = self.chef
        self.assertFalse(is_superadmin(u))
        self.assertTrue(is_chef_depot(u))
        self.assertTrue(can_write(u))
        self.assertTrue(can_close_period(u))
        self.assertFalse(can_manage_users(u))
        self.assertTrue(can_view_audit(u))
        self.assertTrue(can_export(u))
        self.assertTrue(self.chef.is_staff)

    # ── OPERATEUR ──────────────────────────────────────────────────────────────
    def test_operateur_peut_ecrire_mais_pas_cloturer(self):
        u = self.operateur
        self.assertTrue(can_write(u))
        self.assertFalse(can_close_period(u))
        self.assertFalse(can_manage_users(u))
        self.assertFalse(can_view_audit(u))
        self.assertFalse(can_export(u))
        self.assertFalse(self.operateur.is_staff)

    # ── COMPTABLE ──────────────────────────────────────────────────────────────
    def test_comptable_peut_exporter_pas_ecrire(self):
        u = self.comptable
        self.assertFalse(can_write(u))
        self.assertFalse(can_close_period(u))
        self.assertTrue(can_export(u))
        self.assertFalse(can_manage_users(u))

    # ── LECTEUR ────────────────────────────────────────────────────────────────
    def test_lecteur_ne_peut_rien(self):
        u = self.lecteur
        self.assertFalse(can_write(u))
        self.assertFalse(can_close_period(u))
        self.assertFalse(can_manage_users(u))
        self.assertFalse(can_export(u))
        self.assertFalse(can_view_audit(u))

    # ── Profil désactivé ───────────────────────────────────────────────────────
    def test_profil_inactif_perd_toutes_permissions(self):
        """Même un SUPERADMIN désactivé n'a plus aucun droit."""
        self.superadmin.profile.actif = False
        self.superadmin.profile.save()
        self.assertFalse(is_superadmin(self.superadmin))
        self.assertFalse(can_write(self.superadmin))
        self.assertFalse(can_manage_users(self.superadmin))

    # ── Vues web ───────────────────────────────────────────────────────────────
    def test_vue_liste_refusee_non_superadmin(self):
        self.client.force_login(self.chef)
        resp = self.client.get('/utilisateurs/')
        self.assertIn(resp.status_code, (302, 403))

    def test_vue_liste_autorisee_superadmin(self):
        self.client.force_login(self.superadmin)
        resp = self.client.get('/utilisateurs/')
        self.assertEqual(resp.status_code, 200)

    def test_vue_audit_refusee_operateur(self):
        self.client.force_login(self.operateur)
        resp = self.client.get('/audit/')
        self.assertIn(resp.status_code, (302, 403))

    def test_vue_audit_autorisee_chef_depot(self):
        self.client.force_login(self.chef)
        resp = self.client.get('/audit/')
        self.assertEqual(resp.status_code, 200)

    def test_vue_mon_profil_accessible_a_tous(self):
        self.client.force_login(self.lecteur)
        resp = self.client.get('/mon-profil/')
        self.assertEqual(resp.status_code, 200)
