from django import template
from django.utils import timezone

register = template.Library()


@register.inclusion_tag('includes/bandeau_periode.html', takes_context=True)
def bandeau_periode(context):
    """Affiche le bandeau d'alerte si aucune période n'est ouverte (quel que soit le mois)."""
    from SGDS.services.periode_comptable import periode_courante_ou_alerte
    request = context.get('request')
    return {
        'periode_ouverte': periode_courante_ou_alerte(),
        'request':         request,
    }


@register.inclusion_tag('includes/periode_indicateur.html', takes_context=True)
def periode_indicateur(context):
    """Badge topbar — période ouverte (vert) ou absente (rouge) avec dropdown d'actions.
    La période active est la période OUVERTE, quel que soit son mois (ex: avril non clôturé
    reste la période active même si on est en mai).
    """
    from SGDS.services.periode_comptable import periode_courante_ou_alerte
    from SGDS.models import PeriodeComptable
    request = context.get('request')
    periode = periode_courante_ou_alerte()
    # derniere = utile uniquement si periode est None (aucune ouverte)
    derniere = PeriodeComptable.objects.order_by('-annee', '-mois').first()
    return {
        'periode':  periode,
        'derniere': derniere,
        'request':  request,
    }
