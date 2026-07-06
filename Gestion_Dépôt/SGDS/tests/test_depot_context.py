"""
Tests de la résolution du dépôt actif : DepotContextMiddleware,
UserProfile.depots_selectionnables() et changer_depot_actif.

Lancement :
    python manage.py test SGDS.tests.test_depot_context
"""
from django.test import RequestFactory, TestCase

from SGDS.models import Depot
from SGDS.users.managers import creer_utilisateur
from SGDS.users.middleware import DepotContextMiddleware


def _make_depot(code, nom=None):
    return Depot.objects.get_or_create(
        code=code, defaults={'nom': nom or f'Dépôt {code}'}
    )[0]


class _FakeSession(dict):
    """dict avec l'API minimale utilisée par le middleware et la vue."""


class DepotContextMiddlewareTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = DepotContextMiddleware(lambda r: None)
        self.d1 = _make_depot('D1', 'Alpha')
        self.d2 = _make_depot('D2', 'Bravo')

    def _resoudre(self, user, session=None):
        request = self.factory.get('/')
        request.user = user
        request.session = _FakeSession(session or {})
        request.depots_selectionnables = []
        depot = self.middleware._resoudre(request)
        return depot, request

    def test_superadmin_session_tous_donne_vue_consolidee(self):
        sa = creer_utilisateur('sa_depot', 'sa_d@x.ml', 'pass12345', 'SUPERADMIN')
        depot, request = self._resoudre(sa, {'depot_actif_id': 'TOUS'})
        self.assertIsNone(depot)
        # Tous les dépôts ACTIF (y compris ceux créés par les migrations)
        self.assertEqual(
            len(request.depots_selectionnables),
            Depot.objects.filter(statut='ACTIF').count(),
        )

    def test_superadmin_sans_session_prend_premier_actif(self):
        sa = creer_utilisateur('sa_depot2', 'sa_d2@x.ml', 'pass12345', 'SUPERADMIN')
        depot, request = self._resoudre(sa)
        self.assertEqual(depot, self.d1)  # 'Alpha' < 'Bravo'
        self.assertEqual(request.session['depot_actif_id'], str(self.d1.pk))

    def test_role_mono_depot_est_fixe(self):
        chef = creer_utilisateur('chef_depot', 'chef_d@x.ml', 'pass12345', 'CHEF_DEPOT')
        chef.profile.depots.add(self.d2)
        # Une session pointant ailleurs ne doit pas primer sur le dépôt fixe
        depot, _ = self._resoudre(chef, {'depot_actif_id': str(self.d1.pk)})
        self.assertEqual(depot, self.d2)

    def test_role_multi_depots_respecte_la_session(self):
        ope = creer_utilisateur('ope_depot', 'ope_d@x.ml', 'pass12345', 'OPERATEUR')
        ope.profile.depots.add(self.d1, self.d2)
        depot, _ = self._resoudre(ope, {'depot_actif_id': str(self.d2.pk)})
        self.assertEqual(depot, self.d2)

    def test_role_multi_depots_session_invalide_retombe_sur_premier(self):
        ope = creer_utilisateur('ope_depot2', 'ope_d2@x.ml', 'pass12345', 'OPERATEUR')
        ope.profile.depots.add(self.d1, self.d2)
        depot, request = self._resoudre(ope, {'depot_actif_id': '999999'})
        self.assertEqual(depot, self.d1)
        self.assertEqual(request.session['depot_actif_id'], str(self.d1.pk))

    def test_role_tous_non_superadmin_ignore(self):
        ope = creer_utilisateur('ope_depot3', 'ope_d3@x.ml', 'pass12345', 'OPERATEUR')
        ope.profile.depots.add(self.d1, self.d2)
        depot, _ = self._resoudre(ope, {'depot_actif_id': 'TOUS'})
        self.assertEqual(depot, self.d1)

    def test_marketeur_jamais_restreint(self):
        mkt = creer_utilisateur('mkt_depot', 'mkt_d@x.ml', 'pass12345', 'MARKETEUR')
        depot, request = self._resoudre(mkt)
        self.assertIsNone(depot)
        self.assertEqual(request.depots_selectionnables, [])

    def test_role_sans_depot_assigne_donne_none(self):
        cpt = creer_utilisateur('cpt_depot', 'cpt_d@x.ml', 'pass12345', 'COMPTABLE')
        depot, _ = self._resoudre(cpt)
        self.assertIsNone(depot)


class ChangerDepotActifTests(TestCase):

    def setUp(self):
        self.d1 = _make_depot('D1', 'Alpha')
        self.d2 = _make_depot('D2', 'Bravo')

    def test_refuse_depot_non_assigne(self):
        chef = creer_utilisateur('chef_switch', 'chef_s@x.ml', 'pass12345', 'CHEF_DEPOT')
        chef.profile.depots.add(self.d1)
        self.client.force_login(chef)
        self.client.post('/administration/parametres/depot-actif/',
                         {'depot_id': str(self.d2.pk)})
        self.assertNotEqual(
            self.client.session.get('depot_actif_id'), str(self.d2.pk))

    def test_accepte_depot_assigne(self):
        chef = creer_utilisateur('chef_switch2', 'chef_s2@x.ml', 'pass12345', 'CHEF_DEPOT')
        chef.profile.depots.add(self.d1, self.d2)
        self.client.force_login(chef)
        self.client.post('/administration/parametres/depot-actif/',
                         {'depot_id': str(self.d2.pk)})
        self.assertEqual(
            self.client.session.get('depot_actif_id'), str(self.d2.pk))

    def test_tous_refuse_aux_non_superadmin(self):
        chef = creer_utilisateur('chef_switch3', 'chef_s3@x.ml', 'pass12345', 'CHEF_DEPOT')
        chef.profile.depots.add(self.d1)
        self.client.force_login(chef)
        self.client.post('/administration/parametres/depot-actif/',
                         {'depot_id': 'TOUS'})
        self.assertNotEqual(self.client.session.get('depot_actif_id'), 'TOUS')

    def test_tous_accepte_pour_superadmin(self):
        sa = creer_utilisateur('sa_switch', 'sa_s@x.ml', 'pass12345', 'SUPERADMIN')
        self.client.force_login(sa)
        self.client.post('/administration/parametres/depot-actif/',
                         {'depot_id': 'TOUS'})
        self.assertEqual(self.client.session.get('depot_actif_id'), 'TOUS')
