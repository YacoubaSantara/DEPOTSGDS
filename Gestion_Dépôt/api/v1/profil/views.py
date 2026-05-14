"""
Vues profil utilisateur pour l'API mobile.

Endpoints :
  GET   /api/v1/profil/           → mon profil
  PATCH /api/v1/profil/           → modifier prénom, nom, email, téléphone
  POST  /api/v1/profil/password/  → changer mon mot de passe
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.db.models import Sum

from api.v1.permissions import IsMarketeurActif
from SGDS.models import Mouvement
from .serializers import (
    ProfilSerializer,
    UpdateProfilSerializer,
    ChangePasswordSerializer,
)


def _build_profil(user, request):
    """Construit le dict profil à partir de l'utilisateur."""
    profile = getattr(user, 'profile', None)
    mkt     = getattr(user, 'marketeur', None)
    photo_url = None
    if profile and getattr(profile, 'photo', None):
        try:
            photo_url = request.build_absolute_uri(profile.photo.url)
        except Exception:
            pass

    # Statistiques mouvements
    total_mouvements     = 0
    volume_total_ambiant = 0.0
    if mkt:
        qs = Mouvement.objects.filter(marketeur=mkt)
        total_mouvements = qs.count()
        agg = qs.filter(type_mouvement='ENTREE').aggregate(
            s=Sum('volume_ambiant_recu')
        )
        volume_total_ambiant = float(agg['s'] or 0)

    return {
        'id':                    user.id,
        'username':              user.username,
        'full_name':             user.get_full_name() or user.username,
        'email':                 user.email,
        'telephone':             profile.telephone if profile else None,
        'poste':                 profile.poste if profile else None,
        'date_joined':           user.date_joined,
        'derniere_ip':           profile.derniere_ip if profile else None,
        'marketeur_id':          mkt.pk if mkt else None,
        'marketeur_nom':         mkt.raison_sociale if mkt else None,
        'marketeur_sigle':       mkt.sigle if mkt else None,
        'photo_url':             photo_url,
        'total_mouvements':      total_mouvements,
        'volume_total_ambiant':  volume_total_ambiant,
    }


class ProfilView(APIView):
    """
    GET  /api/v1/profil/   → afficher le profil
    PATCH /api/v1/profil/  → modifier prénom, nom, email, téléphone
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsMarketeurActif]

    def get(self, request: Request):
        serializer = ProfilSerializer(_build_profil(request.user, request))
        return Response(serializer.data)

    def patch(self, request: Request):
        serializer = UpdateProfilSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        data = serializer.validated_data

        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']
        user.save(update_fields=['first_name', 'last_name', 'email'])

        profile = getattr(user, 'profile', None)
        if profile and 'telephone' in data:
            profile.telephone = data['telephone']
            profile.save(update_fields=['telephone'])

        return Response(_build_profil(user, request))


class ChangePasswordView(APIView):
    """
    POST /api/v1/profil/password/

    Corps :
        {
            "ancien_mot_de_passe": "...",
            "nouveau_mot_de_passe": "...",
            "confirmation": "..."
        }
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsMarketeurActif]

    def post(self, request: Request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        data = serializer.validated_data

        # Vérifier l'ancien mot de passe
        if not user.check_password(data['ancien_mot_de_passe']):
            return Response(
                {'ancien_mot_de_passe': 'Mot de passe actuel incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(data['nouveau_mot_de_passe'])
        user.save()

        return Response({'detail': 'Mot de passe modifié avec succès.'})
