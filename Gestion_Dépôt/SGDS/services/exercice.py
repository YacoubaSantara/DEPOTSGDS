"""
Service de gestion du cycle de vie des Exercice comptables.
Un Exercice regroupe les 12 PeriodeComptable d'une année civile.
Ouverture automatique (déclenchée par ouvrir_periode) — clôture manuelle uniquement.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone


def exercice_pour_annee(depot, annee):
    """Retourne l'Exercice de `annee` pour ce dépôt, ou None si non créé. NE CRÉE RIEN."""
    from SGDS.models import Exercice
    return Exercice.objects.filter(depot=depot, annee=annee).first()


def ouvrir_exercice_si_necessaire(depot, annee):
    """
    Crée l'Exercice de `annee` pour ce dépôt en statut OUVERT s'il n'existe pas encore.
    Idempotent — appelé depuis ouvrir_periode() à chaque ouverture de période.
    """
    from SGDS.models import Exercice
    exercice, _ = Exercice.objects.get_or_create(
        depot=depot, annee=annee,
        defaults={'statut': 'OUVERT', 'date_ouverture': timezone.now()},
    )
    return exercice


def verifier_peut_cloturer_exercice(exercice):
    """
    Vérifie qu'on peut clôturer l'exercice.

    Règles :
    1. Il doit être OUVERT.
    2. Les 12 périodes de l'année doivent exister et être toutes CLOTUREE.

    Retourne True si OK, lève ValidationError sinon.
    """
    if exercice.statut != 'OUVERT':
        raise ValidationError(f"{exercice.libelle} n'est pas ouvert.")

    periodes = list(exercice.periodes)
    if len(periodes) < 12:
        raise ValidationError(
            f"Impossible de clôturer {exercice.libelle} : "
            f"{len(periodes)}/12 périodes créées sur l'année."
        )

    non_clouturees = [p for p in periodes if p.statut != 'CLOTUREE']
    if non_clouturees:
        noms = ', '.join(p.libelle for p in non_clouturees)
        raise ValidationError(
            f"Impossible de clôturer {exercice.libelle} : "
            f"période(s) encore ouverte(s) — {noms}."
        )

    return True


@transaction.atomic
def cloturer_exercice(exercice, user=None, notes=None):
    """
    Clôture l'exercice après vérification que les 12 périodes sont CLOTUREE.
    N'ouvre PAS l'exercice suivant (créé automatiquement à la première
    ouverture de période de l'année suivante).
    Lève ValidationError si non autorisé.
    """
    verifier_peut_cloturer_exercice(exercice)

    exercice.statut       = 'CLOTURE'
    exercice.date_cloture = timezone.now()
    exercice.cloture_par  = user
    if notes:
        exercice.notes = notes
    exercice.save(update_fields=['statut', 'date_cloture', 'cloture_par', 'notes'])

    return exercice
