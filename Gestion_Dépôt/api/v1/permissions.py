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


class HasVoirPermission(IsMarketeurActif):
    """
    Étend IsMarketeurActif : vérifie en plus que le rôle du marketeur possède
    la permission RBAC `permission_codename` (référentiel
    SGDS.users.permissions_registry), pour que l'API mobile applique les
    mêmes restrictions d'accès que les pages web équivalentes
    (cf. @voir_required(codename) dans SGDS/views/*.py).

    Un admin qui retire une permission (ex. voir_coulage) au rôle d'un
    marketeur lui bloque désormais l'accès à l'endpoint mobile correspondant,
    comme c'est déjà le cas côté web.
    """
    permission_codename = None
    message = "Permission insuffisante pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.has_perm(self.permission_codename)


class HasVoirMouvement(HasVoirPermission):
    permission_codename = 'voir_mouvement'


class HasVoirDetailMouvement(HasVoirPermission):
    permission_codename = 'voir_detail_mouvement'


class HasVoirEtat(HasVoirPermission):
    permission_codename = 'voir_etat'


class HasVoirCoulage(HasVoirPermission):
    permission_codename = 'voir_coulage'


class HasVoirFraisPassage(HasVoirPermission):
    permission_codename = 'voir_frais_passage'


class HasVoirCamion(HasVoirPermission):
    permission_codename = 'voir_camion'


class HasAjouterCamion(HasVoirPermission):
    permission_codename = 'ajouter_camion'


class HasModifierCamion(HasVoirPermission):
    permission_codename = 'modifier_camion'


class HasSupprimerCamion(HasVoirPermission):
    permission_codename = 'supprimer_camion'


class HasVoirChauffeur(HasVoirPermission):
    permission_codename = 'voir_chauffeur'


class HasAjouterChauffeur(HasVoirPermission):
    permission_codename = 'ajouter_chauffeur'


class HasModifierChauffeur(HasVoirPermission):
    permission_codename = 'modifier_chauffeur'


class HasSupprimerChauffeur(HasVoirPermission):
    permission_codename = 'supprimer_chauffeur'


# Codenames RBAC couvrant le module "Ma Flotte" (camions + chauffeurs) côté
# mobile. Exposés au client (login + profil) pour piloter l'affichage des
# actions créer/modifier/supprimer sans dupliquer le référentiel RBAC.
MOBILE_FLOTTE_PERMISSIONS = [
    'voir_camion', 'ajouter_camion', 'modifier_camion', 'supprimer_camion',
    'voir_chauffeur', 'ajouter_chauffeur', 'modifier_chauffeur', 'supprimer_chauffeur',
]


def permissions_dict(user) -> dict:
    """Retourne {codename: bool} pour les permissions du module Flotte."""
    return {code: user.has_perm(code) for code in MOBILE_FLOTTE_PERMISSIONS}
