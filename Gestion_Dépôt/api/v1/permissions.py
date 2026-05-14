"""
Permissions personnalisées pour l'API SGDS mobile.
"""
from rest_framework.permissions import BasePermission


class IsMarketeurActif(BasePermission):
    """
    Autorise uniquement les utilisateurs authentifiés ayant :
      - le rôle MARKETEUR (is_marketeur_role)
      - un lien vers un Marketeur actif (user.marketeur)
    """
    message = "Accès réservé aux marketeurs actifs."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if not getattr(user, 'is_marketeur_role', False):
            return False
        marketeur = getattr(user, 'marketeur', None)
        if not marketeur:
            return False
        if marketeur.statut != 'ACTIF':
            return False
        return True
