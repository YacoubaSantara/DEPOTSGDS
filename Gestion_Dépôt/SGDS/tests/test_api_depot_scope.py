"""
Tests du scoping dépôt de l'API mobile et du cache quote-part coulage.

Lancement :
    python manage.py test SGDS.tests.test_api_depot_scope
"""
from datetime import date
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from SGDS.models import (
    ClotureCoulageLigne, ClotureCoulageMensuel, Depot, Famille, Marketeur,
    Mouvement, PeriodeComptable, Produit,
)
from SGDS.services.coulage_repartition import quote_part_marketeur
from SGDS.users.managers import creer_utilisateur


def _make_depot(code, nom):
    return Depot.objects.get_or_create(code=code, defaults={'nom': nom})[0]


class _BaseAPI(TestCase):

    def setUp(self):
        cache.clear()
        self.depot_a = _make_depot('DA', 'Alpha')
        self.depot_b = _make_depot('DB', 'Bravo')
        fam = Famille.objects.get_or_create(code='HC', defaults={'nom': 'Hydro'})[0]
        self.go = Produit.objects.get_or_create(
            code='GO-API', defaults={'nom': 'Gasoil API', 'famille': fam})[0]
        self.mkt = Marketeur.objects.create(
            raison_sociale='Marketeur API', sigle='MAPI',
            adresse='x', ville='x', telephone='0',
        )
        self.user = creer_utilisateur('mkt_api', 'mkt_api@x.ml', 'pass12345', 'MARKETEUR')
        self.user.role = 'MARKETEUR'          # rôle légataire (is_marketeur_role)
        self.user.marketeur = self.mkt
        self.user.save()

        # Même mois ouvert dans les deux dépôts
        self.periode_a = PeriodeComptable.objects.create(
            depot=self.depot_a, mois=1, annee=2026)
        self.periode_b = PeriodeComptable.objects.create(
            depot=self.depot_b, mois=1, annee=2026)

        # Une entrée de 1000 L au dépôt A, une de 400 L au dépôt B
        Mouvement.objects.create(
            depot=self.depot_a, type_mouvement='ENTREE', regime_douanier='ACQUITTE',
            produit=self.go, marketeur=self.mkt,
            date_mouvement=date(2026, 1, 10),
            volume_ambiant_recu=Decimal('1000'),
        )
        Mouvement.objects.create(
            depot=self.depot_b, type_mouvement='ENTREE', regime_douanier='ACQUITTE',
            produit=self.go, marketeur=self.mkt,
            date_mouvement=date(2026, 1, 12),
            volume_ambiant_recu=Decimal('400'),
        )

        self.client_api = APIClient()
        self.client_api.force_authenticate(user=self.user)


class ScopingDepotAPITests(_BaseAPI):

    def test_stock_ouverture_scope_au_depot_de_la_periode(self):
        """L'état d'une période ne compte que les mouvements de SON dépôt."""
        resp = self.client_api.get('/api/v1/etats/stock-ouverture/',
                                   {'periode_id': self.periode_a.pk})
        self.assertEqual(resp.status_code, 200)
        lignes = resp.data['lignes'] if 'lignes' in resp.data else resp.data.get('produits', [])
        entrees = sum(Decimal(str(l['entrees'])) for l in lignes)
        self.assertEqual(entrees, Decimal('1000'))  # pas 1400 (dépôt B exclu)

    def test_recap_scope_au_depot_de_la_periode(self):
        resp = self.client_api.get('/api/v1/etats/recap/',
                                   {'periode_id': self.periode_b.pk})
        self.assertEqual(resp.status_code, 200)
        total = sum(
            Decimal(str(p['volume_entree_ambiant'])) for p in resp.data['par_produit']
        )
        self.assertEqual(total, Decimal('400'))

    def test_periodes_libellent_le_depot_si_plusieurs(self):
        resp = self.client_api.get('/api/v1/etats/periodes/')
        self.assertEqual(resp.status_code, 200)
        noms = [p['nom'] for p in resp.data]
        self.assertTrue(any('Alpha' in n for n in noms))
        self.assertTrue(any('Bravo' in n for n in noms))
        depot_ids = {p['depot_id'] for p in resp.data}
        self.assertIn(self.depot_a.pk, depot_ids)

    def test_dashboard_consolide_les_deux_depots(self):
        """Le stock dashboard = somme des périodes en cours des deux dépôts."""
        resp = self.client_api.get('/api/v1/dashboard/')
        self.assertEqual(resp.status_code, 200)
        ligne_go = next(
            (s for s in resp.data['stocks'] if s['produit_id'] == self.go.pk), None)
        self.assertIsNotNone(ligne_go)
        self.assertEqual(Decimal(str(ligne_go['stock_ambiant'])), Decimal('1400'))


class QuotePartCacheTests(_BaseAPI):

    def test_cloture_figee_prime_sur_le_calcul(self):
        """Si une clôture figée existe, la quote-part vient des lignes figées."""
        cloture = ClotureCoulageMensuel.objects.create(periode=self.periode_a)
        ClotureCoulageLigne.objects.create(
            cloture=cloture, marketeur=self.mkt, produit=self.go,
            qp_coul=Decimal('-123.45'),
        )
        qp = quote_part_marketeur(self.periode_a, self.mkt)
        self.assertEqual(qp[self.go.pk]['qp_coul'], Decimal('-123.45'))

    def test_calcul_live_memoise(self):
        """Sans clôture, le calcul est mis en cache (2e appel sans recalcul)."""
        from unittest.mock import patch

        qp1 = quote_part_marketeur(self.periode_b, self.mkt)
        with patch(
            'SGDS.services.coulage_repartition.calculer_repartition_coulage'
        ) as mock_calc:
            qp2 = quote_part_marketeur(self.periode_b, self.mkt)
            mock_calc.assert_not_called()
        self.assertEqual(qp1, qp2)
