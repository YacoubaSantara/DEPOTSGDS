"""
Service de gestion du cycle de vie des PériodeComptable.
Aucune création implicite — tout passe par ouvrir_periode().
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone


# ─── Helpers ────────────────────────────────────────────────────

def mois_suivant(mois, annee):
    """Retourne (mois+1, annee) en gérant décembre → janvier+1."""
    if mois == 12:
        return 1, annee + 1
    return mois + 1, annee


def _noms_mois():
    return ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']


# ─── Lecture (sans écriture) ─────────────────────────────────────

def periode_pour_date(d, depot):
    """
    Retourne la PeriodeComptable (OUVERTE ou CLOTUREE) du dépôt `depot`
    pour la date `d`, ou None si aucune n'existe. NE CRÉE RIEN.
    """
    from SGDS.models import PeriodeComptable
    try:
        return PeriodeComptable.objects.filter(
            depot=depot, mois=d.month, annee=d.year,
        ).first()
    except Exception:
        return None


def periode_ouverte_pour_date(d, depot):
    """
    Retourne la PeriodeComptable OUVERTE du dépôt `depot` pour la date `d`, ou None.
    """
    from SGDS.models import PeriodeComptable
    try:
        return PeriodeComptable.objects.filter(
            depot=depot, mois=d.month, annee=d.year, statut='OUVERTE',
        ).first()
    except Exception:
        return None


def periode_courante_ou_alerte(depot=None):
    """
    Retourne la PeriodeComptable OUVERTE du dépôt `depot`, quel que soit le
    mois, ou None. Si `depot` est None (vue consolidée / non authentifié),
    retourne None — il n'y a pas de "période courante" globale multi-dépôt.
    Utilisée par le templatetag du bandeau d'alerte et le context processor.
    """
    from SGDS.models import PeriodeComptable
    if depot is None:
        return None
    return PeriodeComptable.objects.filter(
        depot=depot, statut='OUVERTE'
    ).order_by('-annee', '-mois').first()


# ─── Vérification ────────────────────────────────────────────────

def verifier_peut_ouvrir_periode(depot, mois, annee):
    """
    Vérifie qu'on peut ouvrir (mois, annee) pour ce dépôt.

    Règles :
    1. La période ne doit pas déjà exister pour ce dépôt.
    2. Si aucune période en base pour ce dépôt → OK (première période).
    3. Sinon, la dernière par ordre chronologique doit être CLOTUREE
       ET la nouvelle doit être exactement M+1.

    Retourne True si OK, lève ValidationError sinon.
    """
    from SGDS.models import PeriodeComptable

    # Déjà existante ?
    if PeriodeComptable.objects.filter(depot=depot, mois=mois, annee=annee).exists():
        noms = _noms_mois()
        raise ValidationError(
            f"La période {noms[mois]} {annee} existe déjà pour ce dépôt."
        )

    derniere = PeriodeComptable.objects.filter(depot=depot).order_by('-annee', '-mois').first()

    # Première période ?
    if derniere is None:
        return True

    # La dernière doit être clôturée
    if derniere.statut != 'CLOTUREE':
        noms = _noms_mois()
        raise ValidationError(
            f"La période {derniere.libelle} est encore ouverte. "
            "Clôturez-la avant d'ouvrir une nouvelle période."
        )

    # La nouvelle doit être exactement M+1 après la dernière
    m_attendu, a_attendu = mois_suivant(derniere.mois, derniere.annee)
    if (mois, annee) != (m_attendu, a_attendu):
        noms = _noms_mois()
        raise ValidationError(
            f"La prochaine période à ouvrir est {noms[m_attendu]} {a_attendu}, "
            f"pas {noms[mois]} {annee}. Les périodes doivent se suivre sans saut."
        )

    return True


# ─── Ouverture ───────────────────────────────────────────────────

@transaction.atomic
def ouvrir_periode(depot, mois, annee, user=None):
    """
    Ouvre la période (mois, annee) pour ce dépôt après vérification.
    Crée PeriodeComptable en statut OUVERTE.
    Résout les stocks d'ouverture depuis le dernier jaugeage de la
    période précédente si elle existe.
    Retourne l'instance créée.
    Lève ValidationError si non autorisé.
    """
    from SGDS.models import PeriodeComptable
    from SGDS.services.stock_ouverture import resoudre_stocks_ouverture
    from SGDS.services.stock_ouverture_marketeur import resoudre_stock_ouverture_marketeur
    from SGDS.services.exercice import ouvrir_exercice_si_necessaire

    verifier_peut_ouvrir_periode(depot, mois, annee)

    periode = PeriodeComptable.objects.create(
        depot=depot,
        mois=mois,
        annee=annee,
        statut='OUVERTE',
        date_ouverture=timezone.now(),
    )

    # Crée l'Exercice de l'année si nécessaire (idempotent)
    ouvrir_exercice_si_necessaire(depot, annee)

    # Résoudre les stocks d'ouverture depuis la période précédente
    precedente = periode.periode_precedente()
    if precedente is not None:
        try:
            resoudre_stocks_ouverture(periode)
        except Exception:
            pass  # Non bloquant — les stocks peuvent être saisis manuellement

    try:
        resoudre_stock_ouverture_marketeur(periode)
    except Exception:
        pass  # Non bloquant — les stocks peuvent être saisis manuellement

    return periode


# ─── Clôture ─────────────────────────────────────────────────────

@transaction.atomic
def cloturer_periode(periode, user=None, notes=None):
    """
    Clôture la période.
    1. Vérifie qu'elle est OUVERTE et qu'au moins un jaugeage existe.
    2. Appelle figer_cloture_coulage().
    3. Marque statut=CLOTUREE.

    N'ouvre PAS la période suivante (action séparée via ouvrir_periode).
    Lève ValidationError si non autorisé.
    """
    from SGDS.models import JaugeageJour
    from SGDS.services.coulage_repartition import figer_cloture_coulage

    if periode.statut != 'OUVERTE':
        raise ValidationError(f"La période {periode} n'est pas ouverte.")

    if not JaugeageJour.objects.filter(
        depot=periode.depot,
        date_jaugeage__gte=periode.date_debut,
        date_jaugeage__lte=periode.date_fin,
    ).exists():
        raise ValidationError(
            f"Impossible de clôturer {periode} : aucun jaugeage enregistré ce mois."
        )

    figer_cloture_coulage(periode, user=user, notes=notes)

    periode.statut       = 'CLOTUREE'
    periode.date_cloture = timezone.now()
    periode.cloture_par  = user
    periode.save(update_fields=['statut', 'date_cloture', 'cloture_par'])

    return periode
