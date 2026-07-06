from SGDS.models import Notification, Depot


def depot_context(request):
    """Injecte le dépôt actif (résolu par DepotContextMiddleware) et la liste
    des dépôts actifs (pour le switcher SUPERADMIN) dans tous les templates."""
    if not request.user.is_authenticated:
        return {'depot': None, 'depots_actifs': Depot.objects.none()}
    return {
        'depot': getattr(request, 'depot', None),
        'depots_actifs': Depot.objects.filter(statut='ACTIF').order_by('nom'),
    }


def notifications_marketeur(request):
    if (
        request.user.is_authenticated
        and hasattr(request.user, 'is_marketeur_role')
        and request.user.is_marketeur_role
        and request.user.marketeur
    ):
        mkt = request.user.marketeur
        notifs = Notification.objects.filter(marketeur=mkt).order_by('-date_creation')[:12]
        count_non_lues = Notification.objects.filter(marketeur=mkt, lue=False).count()
        return {'notifs_recentes': notifs, 'notif_count': count_non_lues}
    return {'notifs_recentes': [], 'notif_count': 0}
