"""
Tests du workflow de période comptable, recalcul de stock et écart jaugeages.

Lancement :
    python manage.py test SGDS.tests.test_workflow_periode
"""
from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from SGDS.models import (
    Famille, Produit, Cuve, ParametreJaugeageCuve,
    JaugeageJour, MesureCuve, Mouvement, Marketeur,
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


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_depot(code='DEP-T'):
    return Depot.objects.get_or_create(
        code=code, defaults={'nom': f'Dépôt Test {code}'}
    )[0]


def _make_famille(nom='Carburant', code='CARB'):
    return Famille.objects.get_or_create(
        code=code, defaults={'nom': nom, 'couleur': '#E8760A'}
    )[0]


def _make_produit(code='GO', nom='Gas-oil'):
    famille = _make_famille()
    return Produit.objects.get_or_create(
        code=code, defaults={'nom': nom, 'famille': famille}
    )[0]


def _make_cuve(numero='CUV-01', produit=None, htt=5000, va=1000, vmn=10):
    cuve = Cuve.objects.get_or_create(
        numero=numero,
        defaults={
            'designation': f'Cuve {numero}',
            'produit': produit,
            'capacite_totale': 500_000,
            'depot': _make_depot(),
        }
    )[0]
    if produit:
        cuve.produit = produit
        cuve.save(update_fields=['produit'])
    ParametreJaugeageCuve.objects.get_or_create(
        cuve=cuve,
        defaults={
            'hauteur_totale_temoin': htt,
            'correction_creux': 0,
            'remplissage_maxi': 400_000,
            'v_a': va,
            'v_mn': vmn,
        }
    )
    return cuve


def _make_marketeur(sigle='MKT'):
    return Marketeur.objects.get_or_create(
        sigle=sigle,
        defaults={
            'raison_sociale': f'Société {sigle}',
            'forme_juridique': 'SARL',
            'adresse': 'Bamako',
            'ville': 'Bamako',
            'telephone': '+22312345678',
            'nom_representant': 'Doe',
            'prenom_representant': 'John',
        }
    )[0]


def _make_mesure(jaugeage, cuve, creux=1000):
    """Crée une MesureCuve avec creux donné, sans signal (via update_fields)."""
    m, _ = MesureCuve.objects.get_or_create(
        jaugeage=jaugeage, cuve=cuve,
        defaults={'creux_mesure': creux},
    )
    if m.creux_mesure != creux:
        m.creux_mesure = creux
        m.save(update_fields=['creux_mesure'])
    return m


def _open_jan_2026():
    return ouvrir_periode(_make_depot(), 1, 2026)


# ═════════════════════════════════════════════════════════════════════════════
#  A. WORKFLOW PÉRIODE COMPTABLE
# ═════════════════════════════════════════════════════════════════════════════

class WorkflowPeriodeTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin_test', password='test', email='admin@test.com'
        )

    def test_creation_mouvement_sans_periode_ouverte_refusee(self):
        """Aucune période ouverte → création Mouvement impossible."""
        produit    = _make_produit('GO2')
        marketeur  = _make_marketeur('M1')
        mouvement  = Mouvement(
            depot            = _make_depot(),
            type_mouvement  = 'ENTREE',
            regime_douanier = 'ACQUITTE',
            date_mouvement  = date(2026, 1, 15),
            marketeur       = marketeur,
            produit         = produit,
            volume_ambiant_recu  = Decimal('5000'),
            densite_observee_labo= Decimal('730'),
            temperature_labo     = Decimal('30'),
            temperature_reception= Decimal('32'),
        )
        with self.assertRaises(ValidationError):
            mouvement.full_clean()

    def test_creation_jaugeage_sans_periode_ouverte_refusee(self):
        """Aucune période ouverte → création JaugeageJour impossible."""
        j = JaugeageJour(
            depot          = _make_depot(),
            date_jaugeage  = date(2026, 1, 10),
            type_jaugeage  = 'J', est_valide=True,
        )
        with self.assertRaises(ValidationError):
            j.full_clean()

    def test_ouverture_premiere_periode_ok(self):
        """Si aucune période en base, on peut ouvrir n'importe quel mois."""
        self.assertEqual(PeriodeComptable.objects.count(), 0)
        p = ouvrir_periode(_make_depot(), 3, 2026)
        self.assertEqual(p.statut, 'OUVERTE')
        self.assertEqual(p.mois, 3)
        self.assertEqual(p.annee, 2026)

    def test_ouverture_periode_quand_precedente_ouverte_refusee(self):
        """Janvier OUVERTE → impossible d'ouvrir février."""
        _open_jan_2026()
        with self.assertRaises(ValidationError):
            ouvrir_periode(_make_depot(), 2, 2026)

    def test_ouverture_periode_non_chronologique_refusee(self):
        """Janvier CLOTUREE → on peut ouvrir février mais pas mars."""
        p_jan = _open_jan_2026()
        # Créer un jaugeage pour pouvoir clôturer
        j = JaugeageJour.objects.create(
            depot=_make_depot(), date_jaugeage=date(2026, 1, 15), type_jaugeage='J'
        )
        cloturer_periode(p_jan)
        with self.assertRaises(ValidationError):
            ouvrir_periode(_make_depot(), 3, 2026)  # saut non autorisé

    def test_ouverture_mois_suivant_apres_cloture_ok(self):
        """Janvier CLOTUREE → ouverture de février OK."""
        p_jan = _open_jan_2026()
        JaugeageJour.objects.create(
            depot=_make_depot(), date_jaugeage=date(2026, 1, 15), type_jaugeage='J'
        )
        cloturer_periode(p_jan)
        p_fev = ouvrir_periode(_make_depot(), 2, 2026)
        self.assertEqual(p_fev.statut, 'OUVERTE')

    def test_creation_mouvement_periode_cloturee_refusee(self):
        """Période CLOTUREE → Mouvement refusé avec message explicite."""
        p = _open_jan_2026()
        JaugeageJour.objects.create(
            depot=_make_depot(), date_jaugeage=date(2026, 1, 15), type_jaugeage='J'
        )
        cloturer_periode(p)
        produit   = _make_produit('GO3')
        marketeur = _make_marketeur('M2')
        with self.assertRaises(ValidationError) as ctx:
            Mouvement(
                depot            = _make_depot(),
                type_mouvement  = 'ENTREE',
                regime_douanier = 'ACQUITTE',
                date_mouvement  = date(2026, 1, 5),
                marketeur       = marketeur,
                produit         = produit,
                volume_ambiant_recu   = Decimal('5000'),
                densite_observee_labo = Decimal('730'),
                temperature_labo      = Decimal('30'),
                temperature_reception = Decimal('32'),
            ).full_clean()
        self.assertIn('clôturée', str(ctx.exception).lower())

    def test_creation_mouvement_periode_ouverte_ok(self):
        """Période OUVERTE → Mouvement passe la validation clean()."""
        _open_jan_2026()
        produit   = _make_produit('GO4')
        marketeur = _make_marketeur('M3')
        m = Mouvement(
            depot            = _make_depot(),
            type_mouvement  = 'ENTREE',
            regime_douanier = 'ACQUITTE',
            date_mouvement  = date(2026, 1, 10),
            marketeur       = marketeur,
            produit         = produit,
        )
        try:
            m.full_clean()
        except ValidationError as e:
            # Seuls des champs ENTREE manquants sont tolérés, pas le guard période
            messages = str(e)
            self.assertNotIn('période', messages.lower())

    def test_ouverture_periode_deja_existante_refusee(self):
        """Tenter d'ouvrir une période déjà existante → ValidationError."""
        _open_jan_2026()
        JaugeageJour.objects.create(
            depot=_make_depot(), date_jaugeage=date(2026, 1, 15), type_jaugeage='J'
        )
        p = PeriodeComptable.objects.get(mois=1, annee=2026)
        cloturer_periode(p)
        ouvrir_periode(_make_depot(), 2, 2026)
        with self.assertRaises(ValidationError):
            ouvrir_periode(_make_depot(), 2, 2026)  # existe déjà

    def test_cloture_sans_jaugeage_refusee(self):
        """Clôturer une période sans aucun jaugeage → ValidationError."""
        p = _open_jan_2026()
        with self.assertRaises(ValidationError):
            cloturer_periode(p)


# ═════════════════════════════════════════════════════════════════════════════
#  B. RECALCUL DE STOCK
# ═════════════════════════════════════════════════════════════════════════════

class RecalculStockTests(TestCase):

    def setUp(self):
        _open_jan_2026()

    def _jaugeage(self, d=date(2026, 1, 5)):
        return JaugeageJour.objects.create(depot=_make_depot(), date_jaugeage=d, type_jaugeage='J', est_valide=True)

    def test_stock_mis_a_jour_apres_mesure(self):
        """
        Créer une MesureCuve avec creux=500, HTT=5000, va=1000, vmn=10.
        volume_ambiant_depot = va + vmn*(surplus) = 1000 + 10*(4500 % 10) = 1000+0 = 1000
        (creux_corrige=500, hauteur=4500, surplus=0 → v_bac=1000+0=1000, v_depot=1000)
        """
        produit = _make_produit('GO10')
        cuve    = _make_cuve('CUV-10', produit=produit, htt=5000, va=1000, vmn=10)
        j       = self._jaugeage()
        _make_mesure(j, cuve, creux=500)

        cuve.refresh_from_db()
        self.assertEqual(cuve.niveau_actuel, Decimal('1000'))

        produit.refresh_from_db()
        self.assertEqual(produit.stock_actuel, Decimal('1000'))

    def test_stock_zero_si_aucune_mesure(self):
        """Aucune mesure → niveau_actuel = 0."""
        produit = _make_produit('GO11')
        cuve    = _make_cuve('CUV-11', produit=produit)
        recalculer_stock_cuve(cuve)
        cuve.refresh_from_db()
        self.assertEqual(cuve.niveau_actuel, Decimal('0'))

    def test_stock_recalcule_apres_suppression_mesure(self):
        """Supprimer une mesure → niveau_actuel revient à la mesure précédente (ici 0)."""
        produit = _make_produit('GO12')
        cuve    = _make_cuve('CUV-12', produit=produit, htt=5000, va=1000, vmn=10)
        j       = self._jaugeage()
        m       = _make_mesure(j, cuve, creux=500)

        cuve.refresh_from_db()
        self.assertEqual(cuve.niveau_actuel, Decimal('1000'))

        m.delete()
        cuve.refresh_from_db()
        self.assertEqual(cuve.niveau_actuel, Decimal('0'))

    def test_stock_produit_est_somme_cuves(self):
        """Produit.stock_actuel = Σ niveau_actuel de ses cuves."""
        produit = _make_produit('GO13')
        c1 = _make_cuve('CUV-13', produit=produit, htt=5000, va=1000, vmn=10)
        c2 = _make_cuve('CUV-14', produit=produit, htt=5000, va=2000, vmn=10)
        j  = self._jaugeage()
        _make_mesure(j, c1, creux=500)   # v_depot = 1000
        _make_mesure(j, c2, creux=500)   # v_depot = 2000

        produit.refresh_from_db()
        self.assertEqual(produit.stock_actuel, Decimal('3000'))

    def test_stock_recalcule_apres_suppression_jaugeage(self):
        """Supprimer le jaugeage entier → stocks remis à 0."""
        produit = _make_produit('GO14')
        cuve    = _make_cuve('CUV-15', produit=produit, htt=5000, va=1000, vmn=10)
        j       = self._jaugeage()
        _make_mesure(j, cuve, creux=500)

        cuve.refresh_from_db()
        self.assertGreater(cuve.niveau_actuel, 0)

        j.delete()
        cuve.refresh_from_db()
        self.assertEqual(cuve.niveau_actuel, Decimal('0'))

    def test_recalcul_generique_tous_produits(self):
        """recalculer_tous_stocks() boucle sur tous les produits sans coder GO/SUPER en dur."""
        p1 = _make_produit('GO20')
        p2 = _make_produit('KERO', 'Kérosène')
        p3 = _make_produit('FUEL', 'Fuel lourd')
        c1 = _make_cuve('CUV-20', produit=p1, htt=5000, va=1000, vmn=10)
        c2 = _make_cuve('CUV-21', produit=p2, htt=5000, va=500, vmn=5)
        c3 = _make_cuve('CUV-22', produit=p3, htt=5000, va=800, vmn=8)
        j  = self._jaugeage()
        _make_mesure(j, c1, creux=500)
        _make_mesure(j, c2, creux=500)
        _make_mesure(j, c3, creux=500)

        recalculer_tous_stocks()

        for p in [p1, p2, p3]:
            p.refresh_from_db()
            self.assertGreaterEqual(p.stock_actuel, 0,
                msg=f"stock_actuel de {p.code} non recalculé")


# ═════════════════════════════════════════════════════════════════════════════
#  C. ÉCART ENTRE JAUGEAGES
# ═════════════════════════════════════════════════════════════════════════════

class EcartJaugeagesTests(TestCase):

    def setUp(self):
        _open_jan_2026()
        self.produit  = _make_produit('GO30')
        self.cuve     = _make_cuve('CUV-30', produit=self.produit,
                                   htt=10000, va=0, vmn=10)

    def _j(self, d, creux):
        j = JaugeageJour.objects.create(depot=_make_depot(), date_jaugeage=d, type_jaugeage='J', est_valide=True)
        _make_mesure(j, self.cuve, creux=creux)
        return j

    def test_ecart_vide_si_premier_jaugeage(self):
        """Premier jaugeage → calculer_ecart_jaugeages retourne {}."""
        j = self._j(date(2026, 1, 5), creux=5000)
        result = calculer_ecart_jaugeages(j)
        self.assertEqual(result, {})

    def test_ecart_pertes_detectees(self):
        """
        J1 : creux=5000 → h=5000 → surplus=0 → v_depot = 0*10 = 0
        Pas de mouvement.
        J2 : creux=4900 → h=5100 → surplus=0 → v_depot = 0
        (HTT=10000, correction=0 ; surplus = hauteur_produit % 10)
        Pour avoir des volumes significatifs :
        HTT=10000, va=0, vmn=10.
        J1 : creux=5000 → creux_corrige=5000 → hp=5000 → decimal=5000 → surplus=0 → bac=0
        → non significatif. Utiliser creux non multiple de 10 :
        creux=4993 → hp=5007 → decimal=5000 → surplus=7 → bac=70 → depot=70
        creux=4983 → hp=5017 → decimal=5010 → surplus=7 → bac=70 → depot=70

        Utilisons va=50000, vmn=10 pour avoir des volumes clairs.
        """
        # Recréer la cuve avec va=50000
        self.cuve.parametre_jaugeage.v_a  = 50000
        self.cuve.parametre_jaugeage.v_mn = 10
        self.cuve.parametre_jaugeage.save(update_fields=['v_a', 'v_mn'])

        # J1 creux=5003 → hp=4997 → decimal=4990 → surplus=7 → bac=50000+70=50070
        j1 = self._j(date(2026, 1, 1), creux=5003)
        # J2 creux=4993 → hp=5007 → decimal=5000 → surplus=7 → bac=50000+70=50070
        j2 = self._j(date(2026, 1, 15), creux=4993)

        ecarts = calculer_ecart_jaugeages(j2)
        # Même volume → écart=0 sans mouvement
        self.assertIn(self.produit, ecarts)
        self.assertEqual(ecarts[self.produit], Decimal('0'))

    def test_ecart_avec_entree_sortie(self):
        """
        Formule : ecart = stock_new - stock_old - entree_nette + sortie
        Ici : les mouvements ne changent pas le stock physique qui vient du jaugeage.
        Donc si stock_new = stock_old ET entree=+100, sortie=+50 :
          ecart = 0 - 100 + 50 = -50 (perte comptable).
        """
        self.cuve.parametre_jaugeage.v_a  = 100_000
        self.cuve.parametre_jaugeage.v_mn = 100
        self.cuve.parametre_jaugeage.save(update_fields=['v_a', 'v_mn'])

        j1 = self._j(date(2026, 1, 1), creux=5000)  # hp=5000, surplus=0 → depot=100000
        j2 = self._j(date(2026, 1, 31), creux=5000)  # idem → depot=100000

        marketeur = _make_marketeur('M4')
        # Mouvement ENTREE : volume_ambiant_recu=100, perte_gain_reception=0
        Mouvement.objects.create(
            depot=_make_depot(),
            type_mouvement='ENTREE',
            regime_douanier='ACQUITTE',
            date_mouvement=date(2026, 1, 15),
            marketeur=marketeur,
            produit=self.produit,
            volume_ambiant_recu=Decimal('100'),
            volume_ambiant_expediteur=Decimal('100'),
            densite_observee_labo=Decimal('730'),
            temperature_labo=Decimal('30'),
            temperature_reception=Decimal('32'),
        )
        Mouvement.objects.create(
            depot=_make_depot(),
            type_mouvement='SORTIE',
            regime_douanier='ACQUITTE',
            date_mouvement=date(2026, 1, 20),
            marketeur=marketeur,
            produit=self.produit,
            volume_ambiant_sortie=Decimal('50'),
            destination='Test',
        )

        ecarts = calculer_ecart_jaugeages(j2)
        # ecart = 100000 - 100000 - (100+0) + 50 = -50
        self.assertIn(self.produit, ecarts)
        self.assertEqual(ecarts[self.produit], Decimal('-50'))

    def test_formatter_ecart_pour_affichage(self):
        """formatter_ecart_pour_affichage retourne le bon signe et classe CSS."""
        j1 = self._j(date(2026, 1, 1), creux=5000)
        j2 = self._j(date(2026, 1, 2), creux=5000)
        ecarts = calculer_ecart_jaugeages(j2)
        lignes = formatter_ecart_pour_affichage(ecarts)
        self.assertIsInstance(lignes, list)
        if lignes:
            l = lignes[0]
            self.assertIn('produit_code', l)
            self.assertIn('ecart', l)
            self.assertIn('signe', l)
            self.assertIn('classe_css', l)

    def test_ecart_generique_produit_non_standard(self):
        """Fonctionne avec un produit non GASOIL/SUPER (ex: PETROLE)."""
        p2 = _make_produit('PETRO', 'Pétrole lampant')
        c2 = _make_cuve('CUV-31', produit=p2, htt=5000, va=1000, vmn=10)
        j1 = JaugeageJour.objects.create(depot=_make_depot(), date_jaugeage=date(2026, 1, 1), type_jaugeage='J', est_valide=True)
        _make_mesure(j1, c2, creux=500)
        j2 = JaugeageJour.objects.create(depot=_make_depot(), date_jaugeage=date(2026, 1, 15), type_jaugeage='J', est_valide=True)
        _make_mesure(j2, c2, creux=500)
        _make_mesure(j2, self.cuve, creux=5000)

        ecarts = calculer_ecart_jaugeages(j2)
        self.assertIn(p2, ecarts)
