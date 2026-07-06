from django import template

register = template.Library()


@register.inclusion_tag('includes/depot_indicateur.html', takes_context=True)
def depot_indicateur(context):
    """Badge topbar — dépôt actif. Switcher dropdown pour SUPERADMIN
    (qui peut basculer entre dépôts ou choisir la vue consolidée) et pour
    les rôles rattachés à plusieurs dépôts (switcher limité à leurs dépôts
    assignés, sans vue consolidée), badge statique sinon (dépôt fixe ou aucun)."""
    request = context.get('request')
    profil = getattr(request.user, 'profile', None) if request else None
    est_superadmin = bool(profil and profil.est_superadmin)

    # Liste déjà résolue (et matérialisée) par DepotContextMiddleware —
    # aucune requête supplémentaire. Repli si rendu hors middleware.
    selectionnables = getattr(request, 'depots_selectionnables', None)
    if selectionnables is None and profil:
        selectionnables = list(profil.depots_selectionnables())
    selectionnables = selectionnables or []

    mes_depots = None if est_superadmin else selectionnables
    return {
        'depot':          context.get('depot'),
        'depots_actifs':  selectionnables if est_superadmin else [],
        'est_superadmin': est_superadmin,
        'mes_depots':     mes_depots,
        'multi_depot':    bool(mes_depots and len(mes_depots) > 1),
        'request':        request,
    }
