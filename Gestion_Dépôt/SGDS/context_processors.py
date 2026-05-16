from SGDS.models import Notification


def notifications_marketeur(request):
    if (
        request.user.is_authenticated
        and hasattr(request.user, 'is_marketeur_role')
        and request.user.is_marketeur_role
        and request.user.marketeur
    ):
        mkt = request.user.marketeur
        notifs = Notification.objects.filter(marketeur=mkt, lue=False).order_by('-date_creation')[:8]
        return {'notifs_recentes': notifs, 'notif_count': notifs.count()}
    return {'notifs_recentes': [], 'notif_count': 0}
