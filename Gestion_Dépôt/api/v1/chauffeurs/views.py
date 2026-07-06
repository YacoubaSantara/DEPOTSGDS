"""
Vues Chauffeur pour l'API mobile.

Endpoints :
  GET  /api/v1/chauffeurs/          → liste des chauffeurs du marketeur connecté
  POST /api/v1/chauffeurs/          → créer un chauffeur (assigné au marketeur connecté)
  GET  /api/v1/chauffeurs/{id}/     → détail
  PATCH/PUT /api/v1/chauffeurs/{id}/ → modifier
  DELETE /api/v1/chauffeurs/{id}/   → supprimer

Accès restreint aux marketeurs actifs (IsMarketeurActif) + permission RBAC
correspondante (voir_chauffeur / ajouter_chauffeur / modifier_chauffeur / supprimer_chauffeur),
miroir exact de SGDS/views/__init__.py::chauffeur_list/chauffeur_create/chauffeur_update/chauffeur_delete.
La mécanique CRUD vit dans api/v1/flotte_base.py (partagée avec camions).
"""
from api.v1.flotte_base import FlotteDetailView, FlotteListCreateView
from api.v1.permissions import (
    HasVoirChauffeur, HasAjouterChauffeur, HasModifierChauffeur, HasSupprimerChauffeur,
)
from SGDS.models import Chauffeur
from .serializers import ChauffeurSerializer


class _ChauffeurConfig:
    model = Chauffeur
    serializer_class = ChauffeurSerializer
    perm_voir = HasVoirChauffeur
    perm_ajouter = HasAjouterChauffeur
    perm_modifier = HasModifierChauffeur
    perm_supprimer = HasSupprimerChauffeur
    champs_recherche = ('nom', 'prenom', 'numero_permis')
    ordering = ('nom', 'prenom')

    def optimiser_queryset(self, qs):
        return qs.select_related('camion')


class ChauffeurListCreateView(_ChauffeurConfig, FlotteListCreateView):
    pass


class ChauffeurDetailView(_ChauffeurConfig, FlotteDetailView):
    pass
