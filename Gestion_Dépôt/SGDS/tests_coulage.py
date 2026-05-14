"""
Tests unitaires — Module coulage (répartition, suivi évolution, frais passage).
Lance avec : python manage.py test SGDS.tests_coulage
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from SGDS.models import (
    Famille, Produit, Marketeur, Cuve, ParametreJaugeageCuve,
    JaugeageJour, MesureCuve, Mouvement,
    PeriodeComptable, StockOuverture, StockOuvertureCuve, ParametresCoulage,
)
from SGDS.services.coulage_repartition import calculer_repartition_coulage, figer_cloture_coulage
from SGDS.services.stock_ouverture import resoudre_stocks_ouverture

User = get_user_model()


# ─── Fixtures communes ────────────────────────────────────────

def _make_base():
    """Crée la structure minimale : famille, produits GO+SUPER, 2 marketeurs."""
    fam = Famille.objects.create(nom='Hydrocarbures', code='HC')
    go = Produit.objects.create(nom='Gasoil', code='GASOIL', famille=fam)
    sup = Produit.objects.create(nom='Super', code='SUPER', famille=fam)
    mkt1 = Marketeur.objects.create(raison_sociale='Marketeur Alpha', sigle='ALPHA')
    mkt2 = Marketeur.objects.create(raison_sociale='Marketeur Beta',  sigle='BETA')
    return go, sup, mkt1, mkt2


def _make_periode(mois=1, annee=2026):
    return PeriodeComptable.objects.create(mois=mois, annee=annee)


def _make_cuve(produit, numero='C01'):
    cuve = Cuve.objects.create(
        numero=numero, designation=numero, produit=produit,
        capacite_totale=Decimal('50000'),
    )
    ParametreJaugeageCuve.objects.create(
        cuve=cuve, hauteur_totale_temoin=5000, remplissage_maxi=50000,
        v_a=Decimal('10'), v_mn=Decimal('0'),
    )
    return cuve


def _entree(periode, mkt, produit, cuve, brut, perte=Decimal('0')):
    """Crée un Mouvement ENTREE. perte > 0 = gain, < 0 = perte."""
    return Mouvement.objects.create(
        type_mouvement='ENTREE',
        regime_douanier='ACQUITTE',
        produit=produit,
        marketeur=mkt,
        cuve=cuve,
        date_mouvement=periode.date_debut,
        volume_ambiant_recu=brut,
        perte_gain_reception=perte,
    )


def _sortie(periode, mkt, produit, cuve, volume):
    return Mouvement.objects.create(
        type_mouvement='SORTIE',
        regime_douanier='ACQUITTE',
        produit=produit,
        marketeur=mkt,
        cuve=cuve,
        date_mouvement=periode.date_debut,
        volume_ambiant_sortie=volume,
    )


# ─── Tests ────────────────────────────────────────────────────

class TestCoefficients(TestCase):

    def test_coefficient_zero_si_pas_de_mouvement(self):
        """Sans aucun mouvement les coefficients doivent être 0."""
        go, sup, *_ = _make_base()
        periode = _make_periode()
        rapport = calculer_repartition_coulage(periode)
        self.assertEqual(rapport['coefficients']['GO'],    Decimal('0'))
        self.assertEqual(rapport['coefficients']['SUPER'], Decimal('0'))

    def test_calcul_ligne_marketeur(self):
        """
        GO : brut=10000, perte_gain_reception=-100 → entree_nette=9900
        Sortie GO = 8000 L
        prix_unitaire = 4.7554
        montant = 8000 × 4.7554 = 38043.20
        """
        go, sup, mkt1, _ = _make_base()
        periode = _make_periode()
        cuve = _make_cuve(go, 'CG1')
        ParametresCoulage.objects.create(
            date_application=date(2026, 1, 1),
            prix_unitaire_passage=Decimal('4.7554'),
        )
        StockOuverture.objects.create(periode=periode, produit=go, volume_ambiant=Decimal('0'))

        _entree(periode, mkt1, go, cuve, Decimal('10000'), Decimal('-100'))
        _sortie(periode, mkt1, go, cuve, Decimal('8000'))

        rapport = calculer_repartition_coulage(periode, marketeurs=[mkt1])
        ligne = rapport['lignes'][0]

        self.assertEqual(ligne['entree_nette_go'], Decimal('9900.00'))
        self.assertEqual(ligne['sortie_go'],        Decimal('8000.00'))
        self.assertEqual(ligne['montant'],          Decimal('38043.20'))

    def test_coefficient_global_identique_pour_tous_marketeurs(self):
        """
        Le coefficient est global : tous les marketeurs reçoivent le même coef.
        """
        go, sup, mkt1, mkt2 = _make_base()
        periode = _make_periode()
        cuve = _make_cuve(go, 'CG2')
        ParametresCoulage.objects.create(
            date_application=date(2026, 1, 1),
            prix_unitaire_passage=Decimal('4.7554'),
        )
        StockOuverture.objects.create(periode=periode, produit=go, volume_ambiant=Decimal('0'))

        _entree(periode, mkt1, go, cuve, Decimal('5000'), Decimal('-50'))
        _entree(periode, mkt2, go, cuve, Decimal('5000'), Decimal('-50'))
        _sortie(periode, mkt1, go, cuve, Decimal('3000'))
        _sortie(periode, mkt2, go, cuve, Decimal('3000'))

        rapport = calculer_repartition_coulage(periode, marketeurs=[mkt1, mkt2])
        coefs = [l['coef_qp_coul_go'] for l in rapport['lignes']]
        self.assertEqual(coefs[0], coefs[1])
        self.assertEqual(coefs[0], rapport['coefficients']['GO'])


class TestFigerCloture(TestCase):

    def test_figer_cloture_idempotent(self):
        """Appeler figer_cloture_coulage() deux fois ne duplique pas les lignes."""
        go, sup, mkt1, _ = _make_base()
        periode = _make_periode()
        cuve = _make_cuve(go, 'CG3')
        ParametresCoulage.objects.create(
            date_application=date(2026, 1, 1),
            prix_unitaire_passage=Decimal('4.7554'),
        )
        StockOuverture.objects.create(periode=periode, produit=go, volume_ambiant=Decimal('0'))
        _entree(periode, mkt1, go, cuve, Decimal('5000'), Decimal('-50'))
        _sortie(periode, mkt1, go, cuve, Decimal('2000'))

        from SGDS.models import ClotureCoulageLigne
        figer_cloture_coulage(periode)
        count_apres_1 = ClotureCoulageLigne.objects.filter(cloture__periode=periode).count()
        figer_cloture_coulage(periode)
        count_apres_2 = ClotureCoulageLigne.objects.filter(cloture__periode=periode).count()

        self.assertGreater(count_apres_1, 0)
        self.assertEqual(count_apres_1, count_apres_2)  # idempotent : pas de doublon


class TestVerrouillage(TestCase):

    def test_verrouillage_periode_cloturee(self):
        """Un mouvement ne peut pas être créé dans une période clôturée."""
        go, sup, mkt1, _ = _make_base()
        periode = _make_periode()
        cuve = _make_cuve(go, 'CG4')

        periode.statut = 'CLOTUREE'
        periode.save()

        with self.assertRaises(ValidationError):
            Mouvement.objects.create(
                type_mouvement='ENTREE',
                produit=go,
                marketeur=mkt1,
                cuve=cuve,
                date_mouvement=periode.date_debut,
                volume_ambiant_recu=Decimal('1000'),
            )


class TestStockOuverture(TestCase):

    def test_resoudre_stocks_ouverture_depuis_jaugeage(self):
        """
        Le stock d'ouverture d'une période doit être le dernier volume jaugé
        de la période précédente.
        """
        from SGDS.services.periode_comptable import ouvrir_periode as _ouvrir

        go, sup, mkt1, _ = _make_base()
        cuve = _make_cuve(go, 'CG5')

        periode_precedente = _make_periode(mois=12, annee=2025)
        periode_courante   = _make_periode(mois=1,  annee=2026)

        # Ouvre décembre pour pouvoir créer le jaugeage
        if periode_precedente.statut != 'OUVERTE':
            periode_precedente.statut = 'OUVERTE'
            periode_precedente.save(update_fields=['statut'])

        # Crée un jaugeage fin décembre
        j = JaugeageJour(date_jaugeage=date(2025, 12, 31), operateur='Test')
        j.save()
        MesureCuve.objects.create(
            jaugeage=j,
            cuve=cuve,
            creux_mesure=Decimal('1000'),
        )

        result = resoudre_stocks_ouverture(periode_courante)

        so = StockOuverture.objects.filter(periode=periode_courante, produit=go).first()
        self.assertIsNotNone(so)
        self.assertTrue(result['jaugeage_source'] is not None)


# ═════════════════════════════════════════════════════════════
#  Suivi Évolution Journalier
# ═════════════════════════════════════════════════════════════

class TestSuiviEvolution(TestCase):

    def _make_setup(self):
        fam  = Famille.objects.create(nom='HC', code='HC')
        go   = Produit.objects.create(nom='Gasoil', code='GASOIL', famille=fam)
        cuve = Cuve.objects.create(
            numero='CG1', designation='Cuve GO 1', produit=go,
            capacite_totale=Decimal('50000'),
        )
        ParametreJaugeageCuve.objects.create(
            cuve=cuve, hauteur_totale_temoin=5000, remplissage_maxi=50000,
            v_a=Decimal('10'), v_mn=Decimal('0'),
        )
        periode = PeriodeComptable.objects.create(mois=1, annee=2026)
        StockOuvertureCuve.objects.create(
            periode=periode, cuve=cuve, volume_ambiant=Decimal('10000'),
        )
        return go, cuve, periode

    def test_stock_conserve_sans_mouvement(self):
        """Sans aucun mouvement le stock comptable reste égal au stock initial."""
        from SGDS.services.suivi_evolution import calculer_suivi_evolution
        go, cuve, periode = self._make_setup()
        rapport = calculer_suivi_evolution(periode, go)

        premier_jour = rapport['jours'][0]
        self.assertEqual(
            premier_jour['stock_comptable'][cuve.id],
            Decimal('10000'),
        )

    def test_stock_baisse_apres_sortie(self):
        """Une sortie réduit le stock comptable du lendemain."""
        from SGDS.services.suivi_evolution import calculer_suivi_evolution
        go, cuve, periode = self._make_setup()
        mkt = Marketeur.objects.create(raison_sociale='Alpha', sigle='ALP')
        Mouvement.objects.create(
            type_mouvement='SORTIE', regime_douanier='ACQUITTE',
            produit=go, marketeur=mkt, cuve=cuve,
            date_mouvement=periode.date_debut,
            volume_ambiant_sortie=Decimal('2000'),
        )
        rapport = calculer_suivi_evolution(periode, go)
        j0 = rapport['jours'][0]
        self.assertEqual(j0['stock_comptable'][cuve.id], Decimal('8000'))

    def test_jaugeage_remplace_stock_pour_lendemain(self):
        """Quand un jaugeage existe, le stock physique sert de base le lendemain.
        volume_ambiant_depot = v_a_saisi (car v_mn=0 et volume_additionnel=None→0).
        """
        from SGDS.services.suivi_evolution import calculer_suivi_evolution
        go, cuve, periode = self._make_setup()

        j = JaugeageJour(date_jaugeage=periode.date_debut, operateur='Test')
        j.save()
        MesureCuve.objects.create(
            jaugeage=j, cuve=cuve, creux_mesure=Decimal('500'),
            v_a_saisi=Decimal('9500'),
        )

        rapport = calculer_suivi_evolution(periode, go)
        j0 = rapport['jours'][0]
        j1 = rapport['jours'][1]

        self.assertEqual(j0['stock_physique'][cuve.id], Decimal('9500'))
        self.assertEqual(j1['stock_initial'][cuve.id],  Decimal('9500'))

    def test_pg_cumul_progression(self):
        """Le P/G cumulé s'accumule correctement sur plusieurs jaugeages."""
        from SGDS.services.suivi_evolution import calculer_suivi_evolution
        go, cuve, periode = self._make_setup()

        # Jaugeage J1 (2 jan) : phys=9800, compta=10000 → pg=-200
        j1 = JaugeageJour(date_jaugeage=date(2026, 1, 2), operateur='Test')
        j1.save()
        MesureCuve.objects.create(
            jaugeage=j1, cuve=cuve, creux_mesure=Decimal('100'),
            v_a_saisi=Decimal('9800'),
        )
        # Jaugeage J2 (5 jan) : phys=9600, compta=9800 → pg=-200, cumul=-400
        j2 = JaugeageJour(date_jaugeage=date(2026, 1, 5), operateur='Test')
        j2.save()
        MesureCuve.objects.create(
            jaugeage=j2, cuve=cuve, creux_mesure=Decimal('100'),
            v_a_saisi=Decimal('9600'),
        )

        rapport = calculer_suivi_evolution(periode, go)
        pg_final = rapport['totaux']['pg_total']
        self.assertEqual(pg_final, Decimal('-400'))


# ═════════════════════════════════════════════════════════════
#  Frais de Passage
# ═════════════════════════════════════════════════════════════

class TestFraisPassage(TestCase):

    def _make_setup(self):
        fam  = Famille.objects.create(nom='HC', code='HC')
        go   = Produit.objects.create(nom='Gasoil', code='GASOIL', famille=fam)
        cuve = Cuve.objects.create(
            numero='CG1', designation='Cuve GO 1', produit=go,
            capacite_totale=Decimal('50000'),
        )
        ParametreJaugeageCuve.objects.create(
            cuve=cuve, hauteur_totale_temoin=5000, remplissage_maxi=50000,
            v_a=Decimal('10'), v_mn=Decimal('0'),
        )
        mkt1 = Marketeur.objects.create(raison_sociale='Alpha', sigle='ALP')
        mkt2 = Marketeur.objects.create(raison_sociale='Beta',  sigle='BET')
        periode = PeriodeComptable.objects.create(mois=1, annee=2026)
        ParametresCoulage.objects.create(
            date_application=date(2026, 1, 1),
            prix_unitaire_passage=Decimal('4.7554'),
        )
        return go, cuve, mkt1, mkt2, periode

    def test_groupement_par_mode(self):
        """Les marketeurs sont regroupés par mode de règlement."""
        from SGDS.services.frais_passage import calculer_frais_passage
        go, cuve, mkt1, mkt2, periode = self._make_setup()

        Mouvement.objects.create(
            type_mouvement='SORTIE', regime_douanier='ACQUITTE',
            produit=go, marketeur=mkt1, cuve=cuve,
            date_mouvement=periode.date_debut,
            volume_ambiant_sortie=Decimal('1000'),
            mode_reglement='ESP-IMMEDIAT',
        )
        Mouvement.objects.create(
            type_mouvement='SORTIE', regime_douanier='ACQUITTE',
            produit=go, marketeur=mkt2, cuve=cuve,
            date_mouvement=periode.date_debut,
            volume_ambiant_sortie=Decimal('2000'),
            mode_reglement='VIREMENT',
        )

        rapport = calculer_frais_passage(periode)
        modes = [s['mode'] for s in rapport['modes']]
        self.assertIn('ESP-IMMEDIAT', modes)
        self.assertIn('VIREMENT', modes)
        self.assertEqual(len(rapport['modes']), 2)

    def test_exclusion_marketeur_sans_sortie(self):
        """Un marketeur sans sortie n'apparaît pas dans le rapport."""
        from SGDS.services.frais_passage import calculer_frais_passage
        go, cuve, mkt1, mkt2, periode = self._make_setup()

        Mouvement.objects.create(
            type_mouvement='SORTIE', regime_douanier='ACQUITTE',
            produit=go, marketeur=mkt1, cuve=cuve,
            date_mouvement=periode.date_debut,
            volume_ambiant_sortie=Decimal('1000'),
            mode_reglement='CHEQUE',
        )
        # mkt2 n'a pas de sortie

        rapport = calculer_frais_passage(periode)
        tous_mkt = [
            l['marketeur'].pk
            for s in rapport['modes'] for l in s['lignes']
        ]
        self.assertIn(mkt1.pk, tous_mkt)
        self.assertNotIn(mkt2.pk, tous_mkt)

    def test_sous_totaux_coherents(self):
        """Le sous-total d'un mode = somme des montants de ses lignes."""
        from SGDS.services.frais_passage import calculer_frais_passage
        go, cuve, mkt1, mkt2, periode = self._make_setup()

        for vol, mkt in [(Decimal('1000'), mkt1), (Decimal('2000'), mkt2)]:
            Mouvement.objects.create(
                type_mouvement='SORTIE', regime_douanier='ACQUITTE',
                produit=go, marketeur=mkt, cuve=cuve,
                date_mouvement=periode.date_debut,
                volume_ambiant_sortie=vol,
                mode_reglement='CREDIT',
            )

        rapport = calculer_frais_passage(periode)
        section = rapport['modes'][0]
        total_lignes = sum(l['montant'] for l in section['lignes'])
        self.assertEqual(section['sous_totaux']['montant'], total_lignes)

    def test_total_general_egal_somme_sous_totaux(self):
        """Le total général = somme de tous les sous-totaux par mode."""
        from SGDS.services.frais_passage import calculer_frais_passage
        go, cuve, mkt1, mkt2, periode = self._make_setup()

        Mouvement.objects.create(
            type_mouvement='SORTIE', regime_douanier='ACQUITTE',
            produit=go, marketeur=mkt1, cuve=cuve,
            date_mouvement=periode.date_debut,
            volume_ambiant_sortie=Decimal('1000'),
            mode_reglement='ESP-IMMEDIAT',
        )
        Mouvement.objects.create(
            type_mouvement='SORTIE', regime_douanier='ACQUITTE',
            produit=go, marketeur=mkt2, cuve=cuve,
            date_mouvement=periode.date_debut,
            volume_ambiant_sortie=Decimal('2000'),
            mode_reglement='VIREMENT',
        )

        rapport = calculer_frais_passage(periode)
        somme_st = sum(s['sous_totaux']['montant'] for s in rapport['modes'])
        self.assertEqual(rapport['total_general']['montant'], somme_st)
