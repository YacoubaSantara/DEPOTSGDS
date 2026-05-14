"""
Vues d'authentification JWT pour l'API mobile SGDS.

Endpoints :
  POST /api/v1/auth/login/    → obtenir access + refresh tokens
  POST /api/v1/auth/refresh/  → renouveler l'access token
  POST /api/v1/auth/logout/   → blacklister le refresh token
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import LoginSerializer, TokenResponseSerializer


class LoginView(APIView):
    """
    POST /api/v1/auth/login/

    Corps :
        { "username": "...", "password": "..." }

    Réponse 200 :
        { "access": "...", "refresh": "...", "user": { ... } }
    """
    permission_classes = [AllowAny]
    authentication_classes = []   # pas de cookie session pour l'API

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            # Aplatit les erreurs en une seule chaîne lisible pour le client mobile
            errors = serializer.errors
            first_msg = next(
                (msgs[0] if isinstance(msgs, (list, tuple)) else str(msgs)
                 for msgs in errors.values() if msgs),
                'Identifiants invalides.',
            )
            return Response(
                {'detail': str(first_msg)},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        data = {
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user':    user,
        }

        response_serializer = TokenResponseSerializer(data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/

    Corps :
        { "refresh": "<refresh_token>" }

    Blackliste le refresh token pour invalider la session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Le token de rafraîchissement est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {'detail': 'Token invalide ou déjà révoqué.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response({'detail': 'Déconnexion réussie.'}, status=status.HTTP_200_OK)


class TokenRefreshAPIView(TokenRefreshView):
    """
    POST /api/v1/auth/refresh/

    Corps :
        { "refresh": "<refresh_token>" }

    Réponse :
        { "access": "<nouveau_access_token>" }
    """
    pass
