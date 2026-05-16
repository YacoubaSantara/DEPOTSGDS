from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from SGDS.models import Notification


class NotificationsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        """Liste les 30 dernières notifications du marketeur connecté."""
        user = request.user
        if not (hasattr(user, 'is_marketeur_role') and user.is_marketeur_role and user.marketeur):
            return Response({'detail': 'Accès réservé aux marketeurs.'}, status=403)
        mkt = user.marketeur
        notifs = Notification.objects.filter(marketeur=mkt).order_by('-date_creation')[:30]
        data = [
            {
                'id':            n.pk,
                'type_notif':    n.type_notif,
                'titre':         n.titre,
                'message':       n.message,
                'lue':           n.lue,
                'date_creation': n.date_creation.isoformat(),
                'mouvement_id':  n.mouvement_id,
            }
            for n in notifs
        ]
        non_lues = sum(1 for n in notifs if not n.lue)
        return Response({'count_non_lues': non_lues, 'results': data})

    def patch(self, request):
        """Marque des notifications comme lues. Body: {"ids": [1,2,3]} ou {"all": true}"""
        user = request.user
        if not (hasattr(user, 'is_marketeur_role') and user.is_marketeur_role and user.marketeur):
            return Response({'detail': 'Accès réservé.'}, status=403)
        mkt = user.marketeur
        if request.data.get('all'):
            Notification.objects.filter(marketeur=mkt, lue=False).update(lue=True)
        else:
            ids = request.data.get('ids', [])
            Notification.objects.filter(marketeur=mkt, pk__in=ids).update(lue=True)
        return Response({'status': 'ok'})
