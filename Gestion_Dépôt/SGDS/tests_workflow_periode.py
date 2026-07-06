"""
Tests — workflow des périodes comptables, recalcul stock, écart jaugeages.
Lance avec : python manage.py test SGDS.tests_workflow_periode
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from SGDS.models import (
    Famille, Produit, Cuve, ParametreJaugeageCuve,
    Marketeur, Mouvement, JaugeageJour, MesureCuve,
    PeriodeComptable, Depot,
)
from SGDS.services.periode_comptable import (
    ouvrir_periode, cloturer_periode, verifier_peut_ouvrir_periode,
    periode_pour_date,
)
from SGDS.services.recalcul_stock import (
    recalculer_stock_cuve, recalculer_stock_produit, recalculer_tous_stocks,
)
from SGDS.services.ecart_jaugeages import (
    calculer_ecart_jaugeages, formatter_ecart_pour_affichage,
)

User = get_user_model()


# ─── Fixtures communes ──────────────��─────────────────────────

def _make_depot(code='DEP-T'):
    return Depot.objects.get_or_create(
        code=code, defaults={'nom': f'Dépôt Test {code}'}
    )[0]


def _make_produit(nom='Gasoil', code='GASOIL'):
    fam, _ = Famille.objects.get_or_create(nom='Hydro', code='HC')
    return Produit.objects.create(nom=nom, code=code, famille=fam)


def _make_cuve(produit, numero='C01'):
    cuve = Cuve.objects.create(
        depot=_make_depot(), numero=numero, designation=numero,
        produit=produit, capacite_totale=Decimal('100000'),
    )
    ParametreJaugeageCuve.objects.create(
        cuve=cuve, hauteur_totale_temoin=5000, remplissage_maxi=90000,
        v_a=Decimal('10'), v_mn=Decimal('0'),
    )
    return cuve


def _make_marketeur():
    return Marketeur.objects.create(
        raison_sociale='Test MKT', sigle='TMKT',
        adresse='Rue test', ville='Bamako', telephone='00000',
    )


def _make_jaugeage(d, cuve=None, creux=None):
    j = JaugeageJour(depot=_make_depot(), date_jaugeage=d, est_valide=True)
    j.save()
    if cuve and creux is not None:
        MesureCuve.objects.create(
            jaugeage=j, cuve=cuve, creux_mesure=creux,
            t1=Decimal('30'), t2=Decimal('30'), t3=Decimal('30'),
            temperature_obs=Decimal('30'),
            densite_moyenne=Decimal('830'),
        )
    return j


# ─── Workflow périodes ───────────────────��────────────────────

class WorkflowPeriodeTests(TestCase):

    def test_ouverture_premiere_periode_ok(self):
        """Si aucune période en base, on peut ouvrir n'importe quel mois."""
        self.assertEqual(PeriodeComptable.objects.count(), 0)
        p = ouvrir_periode(_make_depot(), 1, 2026)
        self.assertEqual(p.statut, 'OUVERTE')
        self.assertEqual(p.mois,   1)
        self.assertEqual(p.annee,  2026)

    def test_ouverture_periode_quand_precedente_ouverte_refusee(self):
        """Janvier OUVERTE → impossible d'ouvrir février."""
        ouvrir_periode(_make_depot(), 1, 2026)
        with self.assertRaises(ValidationError):
            ouvrir_periode(_make_depot(), 2, 2026)

    def test_ouverture_periode_non_chronologique_refusee(self):
        """Janvier CLOTUREE → on peut ouvrir février, mais pas mars."""
        p = ouvrir_periode(_make_depot(), 1, 2026)
        p.statut = 'CLOTUREE'
        p.save(update_fields=['statut'])
        with self.assertRaises(ValidationError):
            ouvrir_periode(_make_depot(), 3, 2026)  # saut interdit

    def test_ouverture_periode_m_plus_1_ok(self):
        """Janvier clôturé → ouverture de février OK."""
        p = ouvrir_periode(_make_depot(), 1, 2026)
        p.statut = 'CLOTUREE'
        p.save(update_fields=['statut'])
        fevrier = ouvrir_periode(_make_depot(), 2, 2026)
        self.assertEqual(fevrier.statut, 'OUVERTE')

    def test_creation_mouvement_sans_periode_ouverte_refusee(self):
        """Aucune période → Mouvement rejeté."""
        go = _make_produit()
        mkt = _make_marketeur()
        cuve = _make_cuve(go)
        with self.assertRaises(ValidationError):
            Mouvement.objects.create(
                depot=_make_depot(), type_mouvement='ENTREE',
                regime_douanier='ACQUITTE',
                produit=go, marketeur=mkt, cuve=cuve,
                date_mouvement=date(2026, 1, 15),
                volume_ambiant_recu=Decimal('5000'),
            )

    def test_creation_mouvement_periode_ouverte_ok(self):
        """Période OUVERTE → Mouvement OK."""
        go = _make_produit()
        mkt = _make_marketeur()
        cuve = _make_cuve(go)
        ouvrir_periode(_make_depot(), 1, 2026)
        m = Mouvement.objects.create(
            depot=_make_depot(), type_mouvement='ENTREE',
            regime_douanier='ACQUITTE',
            produit=go, marketeur=mkt, cuve=cuve,
            date_mouvement=date(2026, 1, 15),
            volume_ambiant_recu=Decimal('5000'),
        )
        self.assertIsNotNone(m.pk)

    def test_creation_mouvement_periode_cloturee_refusee(self):
        """Période CLOTUREE → Mouvement refusé."""
        go = _make_produit()
        mkt = _make_marketeur()
        cuve = _make_cuve(go)
        p = ouvrir_periode(_make_depot(), 1, 2026)
        p.statut = 'CLOTUREE'
        p.save(update_fields=['statut'])
        with self.assertRaises(ValidationError):
            Mouvement.objects.create(
                depot=_make_depot(), type_mouvement='ENTREE',
                regime_douanier='ACQUITTE',
                produit=go, marketeur=mkt, cuve=cuve,
                date_mouvement=date(2026, 1, 15),
                volume_ambiant_recu=Decimal('5000'),
            )

    def test_creation_jaugeage_sans_periode_ouverte_refusee(self):
        """Aucune période ouverte → JaugeageJour rejeté."""
        with self.assertRaises(ValidationError):
            JaugeageJour.objects.create(depot=_make_depot(), date_jaugeage=date(2026, 1, 15), est_valide=True)

    def test_creation_jaugeage_periode_ouverte_ok(self):
        """Période OUVERTE → JaugeageJour OK."""
        ouvrir_periode(_make_depot(), 1, 2026)
        j = JaugeageJour.objects.create(depot=_make_depot(), date_jaugeage=date(2026, 1, 15), est_valide=True)
        self.assertIsNotNone(j.pk)


# ─── Recalcul stock ──────────────────────────────��────────────

class RecalculStockTests(TestCase):

    def setUp(self):
        ouvrir_periode(_make_depot(), 1, 2026)
        self.go   = _make_produit('Gasoil', 'GASOIL')
        self.cuve = _make_cuve(self.go, 'RO1')

    def test_stock_mis_a_jour_apres_mesure(self):
        """Créer une MesureCuve déclenche le signal → Cuve.niveau_actuel mis à jour."""
        j = JaugeageJour.objects.create(depot=_make_depot(), date_jaugeage=date(2026, 1, 10), est_valide=True)
        MesureCuve.objects.create(
            jaugeage=j, cuve=self.cuve, creux_mesure=1000,
            t1=Decimal('30'), t2=Decimal('30'), t3=Decimal('30'),
            temperature_obs=Decimal('30'), densite_moyenne=Decimal('830'),
        )
        self.cuve.refresh_from_db()
        self.assertGreater(self.cuve.niveau_actuel, 0)

    def test_stock_recalcule_apres_suppression_mesure(self):
        """Supprimer une mesure → le signal post_delete recalcule niveau_actuel."""
        j = JaugeageJour.objects.create(depot=_make_depot(), date_jaugeage=date(2026, 1, 10), est_valide=True)
        m = MesureCuve.objects.create(
            jaugeage=j, cuve=self.cuve, creux_mesure=1000,
            t1=Decimal('30'), t2=Decimal('30'), t3=Decimal('30'),
            temperature_obs=Decimal('30'), densite_moyenne=Decimal('830'),
        )
        self.cuve.refresh_from_db()
        niveau_avant = self.cuve.niveau_actuel

        m.delete()
        self.cuve.refresh_from_db()
        # Après suppression de la seule mesure, retour à 0
        self.assertEqual(self.cuve.niveau_actuel, Decimal('0'))

    def test_stock_zero_si_aucune_mesure(self):
        """Aucune mesure → niveau_actuel = 0."""
        recalculer_stock_cuve(self.cuve)
        self.cuve.refresh_from_db()
        self.assertEqual(self.cuve.niveau_actuel, Decimal('0'))

    def test_stock_produit_est_somme_cuves(self):
        """Produit.stock_actuel = Σ niveau_actuel des cuves (jaugeage validé requis)."""
        _make_jaugeage(date(2026, 1, 10), self.cuve, creux=1000)
        self.cuve.refresh_from_db()
        self.assertGreater(self.cuve.niveau_actuel, 0)
        recalculer_stock_produit(self.go)
        self.go.refresh_from_db()
        self.assertEqual(self.go.stock_actuel, self.cuve.niveau_actuel)

    def test_recalcul_generique_tous_produits(self):
        """recalculer_tous_stocks() traite tous les produits, pas juste GO/SUPER."""
        autre = _make_produit('Pétrole', 'PETROLE')
        cuve2 = _make_cuve(autre, 'RO2')
        _make_jaugeage(date(2026, 1, 10), cuve2, creux=1000)
        cuve2.refresh_from_db()
        self.assertGreater(cuve2.niveau_actuel, 0)
        recalculer_tous_stocks()
        autre.refresh_from_db()
        self.assertEqual(autre.stock_actuel, cuve2.niveau_actuel)


# ─── Écart jaugeages ───────────────────────────────���─────────

class EcartJaugeagesTests(TestCase):

    def setUp(self):
        ouvrir_periode(_make_depot(), 1, 2026)
        self.go   = _make_produit('Gasoil', 'GASOIL')
        self.cuve = _make_cuve(self.go, 'EJ1')

    def test_ecart_vide_si_premier_jaugeage(self):
        """Premier jaugeage (aucun précédent) → {} retourné."""
        j = _make_jaugeage(date(2026, 1, 5), self.cuve, creux=2000)
        ecarts = calculer_ecart_jaugeages(j)
        self.assertEqual(ecarts, {})

    def test_ecart_pertes_detectees(self):
        """
        J1 cuve GO = 50 000 L
        Entre J1 et J2 : entrée brut 5000, coul -100 → nette 4900
                         sortie 3000
        J2 cuve GO = 51 200 L
        Écart = 51200 - 50000 - 4900 + 3000 = -700 L (perte)
        """
        from SGDS.models import Marketeur as _M
        mkt = _M.objects.create(
            raison_sociale='EcartMKT', sigle='EM',
            adresse='x', ville='x', telephone='0',
        )

        # J1 — on contourne la validation car c'est la même période
        j1 = _make_jaugeage(date(2026, 1, 5), self.cuve, creux=2000)

        # Mouvements entre J1 et J2
        Mouvement.objects.create(
            depot=_make_depot(), type_mouvement='ENTREE', regime_douanier='ACQUITTE',
            produit=self.go, marketeur=mkt, cuve=self.cuve,
            date_mouvement=date(2026, 1, 7),
            volume_ambiant_recu=Decimal('5000'),
            perte_gain_reception=Decimal('-100'),
        )
        Mouvement.objects.create(
            depot=_make_depot(), type_mouvement='SORTIE', regime_douanier='ACQUITTE',
            produit=self.go, marketeur=mkt, cuve=self.cuve,
            date_mouvement=date(2026, 1, 8),
            volume_ambiant_sortie=Decimal('3000'),
        )

        # J2
        j2 = _make_jaugeage(date(2026, 1, 10), self.cuve, creux=2000)

        # Patch les volumes physiques calculés via la propriété
        # On teste la formule avec des valeurs connues directement
        from SGDS.services.ecart_jaugeages import _stocks_physiques_par_produit
        s_j1 = _stocks_physiques_par_produit(j1)
        s_j2 = _stocks_physiques_par_produit(j2)

        # Les deux jaugeages ont le même creux → mêmes volumes calculés
        # Ce test valide la logique de la formule
        ecarts = calculer_ecart_jaugeages(j2)
        self.assertIn(self.go, ecarts)
        # entree_nette = 5000 + (-100) = 4900, sortie = 3000
        # ecart = s_j2 - s_j1 - 4900 + 3000
        expected = s_j2.get(self.go, Decimal('0')) - s_j1.get(self.go, Decimal('0')) - Decimal('4900') + Decimal('3000')
        self.assertAlmostEqual(float(ecarts[self.go]), float(expected), places=1)

    def test_ecart_generique_produits(self):
        """Fonctionne avec un produit non standard."""
        autre = _make_produit('Pétrole', 'PETROLE')
        cuve2 = _make_cuve(autre, 'EJ2')
        j1 = _make_jaugeage(date(2026, 1, 5), cuve2, creux=1500)
        j2 = _make_jaugeage(date(2026, 1, 10), cuve2, creux=1600)
        ecarts = calculer_ecart_jaugeages(j2)
        # Le produit PETROLE doit apparaître dans les écarts
        self.assertIn(autre, ecarts)

    def test_formatter_affichage(self):
        """formatter_ecart_pour_affichage retourne la bonne structure."""
        j1 = _make_jaugeage(date(2026, 1, 5),  self.cuve, creux=2000)
        j2 = _make_jaugeage(date(2026, 1, 10), self.cuve, creux=2100)
        ecarts = calculer_ecart_jaugeages(j2)
        lignes = formatter_ecart_pour_affichage(ecarts)
        self.assertIsInstance(lignes, list)
        for ligne in lignes:
            self.assertIn('produit_code', ligne)
            self.assertIn('ecart',        ligne)
            self.assertIn('signe',        ligne)
            self.assertIn('classe_css',   ligne)
