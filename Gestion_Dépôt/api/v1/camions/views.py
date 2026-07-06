"""
Vues Camion pour l'API mobile.

Endpoints :
  GET  /api/v1/camions/          → liste des camions du marketeur connecté
  POST /api/v1/camions/          → créer un camion (assigné au marketeur connecté)
  GET  /api/v1/camions/{id}/     → détail
  PATCH/PUT /api/v1/camions/{id}/ → modifier
  DELETE /api/v1/camions/{id}/   → supprimer

Accès restreint aux marketeurs actifs (IsMarketeurActif) + permission RBAC
correspondante (voir_camion / ajouter_camion / modifier_camion / supprimer_camion),
miroir exact de SGDS/views/__init__.py::camion_list/camion_create/camion_update/camion_delete.
La mécanique CRUD vit dans api/v1/flotte_base.py (partagée avec chauffeurs).
"""
from api.v1.flotte_base import FlotteDetailView, FlotteListCreateView
from api.v1.permissions import (
    HasVoirCamion, HasAjouterCamion, HasModifierCamion, HasSupprimerCamion,
)
from SGDS.models import Camion
from .serializers import CamionSerializer


class _CamionConfig:
    model = Camion
    serializer_class = CamionSerializer
    perm_voir = HasVoirCamion
    perm_ajouter = HasAjouterCamion
    perm_modifier = HasModifierCamion
    perm_supprimer = HasSupprimerCamion
    champs_recherche = ('immatriculation', 'marque', 'modele')
    ordering = ('immatriculation',)

    def optimiser_queryset(self, qs):
        return qs.prefetch_related('compartiments')


class CamionListCreateView(_CamionConfig, FlotteListCreateView):
    pass


class CamionDetailView(_CamionConfig, FlotteDetailView):
    pass
