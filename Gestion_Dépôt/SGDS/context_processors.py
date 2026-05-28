from SGDS.models import Notification


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
