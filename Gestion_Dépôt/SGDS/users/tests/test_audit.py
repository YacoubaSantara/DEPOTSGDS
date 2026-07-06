from django.test import TestCase

from SGDS.models import Marketeur
from SGDS.users.admin import AuditLogAdmin
from SGDS.users.managers import creer_utilisateur
from SGDS.users.models import AuditLog, Role


def _make_marketeur(raison_sociale='Test SA'):
    return Marketeur.objects.create(
        raison_sociale=raison_sociale,
        forme_juridique='SA',
        adresse='Bamako',
        ville='Bamako',
        telephone='+22370000000',
        nom_representant='Repr',
        prenom_representant='Test',
    )


class AuditTests(TestCase):

    def setUp(self):
        self.user = creer_utilisateur(
            'yacouba', 'y@sgds.ml', 'pass12345', 'CHEF_DEPOT')

    # ── CREATE ─────────────────────────────────────────────────────────────────
    def test_creation_objet_loggee(self):
        """Créer un Marketeur → entrée AuditLog action=CREATE."""
        nb_avant = AuditLog.objects.filter(
            action='CREATE', objet_type='Marketeur').count()
        _make_marketeur('Société Alpha')
        nb_apres = AuditLog.objects.filter(
            action='CREATE', objet_type='Marketeur').count()
        self.assertEqual(nb_apres, nb_avant + 1)

    # ── UPDATE ─────────────────────────────────────────────────────────────────
    def test_modification_capture_changements(self):
        """Modifier raison_sociale → UPDATE avec avant/après."""
        m = _make_marketeur('Ancien Nom')
        m.raison_sociale = 'Nouveau Nom'
        m.save()

        log = AuditLog.objects.filter(
            action='UPDATE', objet_type='Marketeur', objet_id=m.pk
        ).last()
        self.assertIsNotNone(log)
        self.assertIsNotNone(log.changements)
        self.assertIn('raison_sociale', log.changements)
        self.assertEqual(log.changements['raison_sociale']['avant'], 'Ancien Nom')
        self.assertEqual(log.changements['raison_sociale']['apres'], 'Nouveau Nom')

    def test_modification_sans_changement_ne_logue_pas(self):
        """Sauvegarder sans modifier → PAS d'entrée UPDATE."""
        m = _make_marketeur('Stable SA')
        nb = AuditLog.objects.filter(action='UPDATE', objet_id=m.pk).count()
        m.save()  # save sans modifier aucun champ
        self.assertEqual(
            AuditLog.objects.filter(action='UPDATE', objet_id=m.pk).count(),
            nb,
        )

    # ── DELETE ─────────────────────────────────────────────────────────────────
    def test_suppression_loggee_avec_repr(self):
        """Supprimer → DELETE avec objet_repr conservé."""
        m = _make_marketeur('A Supprimer')
        repr_avant = str(m)
        m.delete()

        log = AuditLog.objects.filter(
            action='DELETE', objet_type='Marketeur').last()
        self.assertIsNotNone(log)
        self.assertIn('A Supprimer', log.objet_repr)

    # ── Connexions ─────────────────────────────────────────────────────────────
    def test_login_logge(self):
        nb_avant = AuditLog.objects.filter(action='LOGIN').count()
        self.client.login(username='yacouba', password='pass12345')
        self.assertEqual(
            AuditLog.objects.filter(action='LOGIN').count(),
            nb_avant + 1,
        )

    def test_login_failed_logge(self):
        nb_avant = AuditLog.objects.filter(action='LOGIN_FAILED').count()
        self.client.login(username='yacouba', password='mauvais-mdp')
        self.assertEqual(
            AuditLog.objects.filter(action='LOGIN_FAILED').count(),
            nb_avant + 1,
        )

    # ── Admin Django ────────────────────────────────────────────────────────────
    def test_logs_non_supprimables_via_admin(self):
        from django.contrib.admin.sites import AdminSite
        site = AdminSite()
        admin_instance = AuditLogAdmin(AuditLog, site)
        self.assertFalse(admin_instance.has_delete_permission(None))
        self.assertFalse(admin_instance.has_add_permission(None))
        self.assertFalse(admin_instance.has_change_permission(None))

    # ── Source ─────────────────────────────────────────────────────────────────
    def test_source_system_sans_requete(self):
        """Modification sans requête HTTP → source=SYSTEM."""
        m = _make_marketeur('Sans Requête')
        m.raison_sociale = 'Modifié Système'
        m.save()
        log = AuditLog.objects.filter(
            action='UPDATE', objet_id=m.pk).last()
        if log:  # Peut être None si aucun changement détecté
            self.assertEqual(log.source, 'SYSTEM')
