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
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.v1.permissions import (
    HasVoirCamion, HasAjouterCamion, HasModifierCamion, HasSupprimerCamion,
)
from SGDS.models import Camion
from .serializers import CamionSerializer


class CamionListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [HasAjouterCamion()]
        return [HasVoirCamion()]

    def get(self, request):
        marketeur = request.user.marketeur
        qs = Camion.objects.filter(marketeur=marketeur).prefetch_related('compartiments')

        q = request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(Q(immatriculation__icontains=q) | Q(marque__icontains=q) | Q(modele__icontains=q))

        statut = request.query_params.get('statut', '')
        if statut:
            qs = qs.filter(statut=statut)

        qs = qs.order_by('immatriculation')
        serializer = CamionSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CamionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        camion = serializer.save(marketeur=request.user.marketeur)
        return Response(CamionSerializer(camion).data, status=status.HTTP_201_CREATED)


class CamionDetailView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [HasModifierCamion()]
        if self.request.method == 'DELETE':
            return [HasSupprimerCamion()]
        return [HasVoirCamion()]

    def _get_camion(self, request, pk):
        return get_object_or_404(
            Camion.objects.prefetch_related('compartiments'),
            pk=pk,
            marketeur=request.user.marketeur,
        )

    def get(self, request, pk):
        camion = self._get_camion(request, pk)
        return Response(CamionSerializer(camion).data)

    def patch(self, request, pk):
        camion = self._get_camion(request, pk)
        serializer = CamionSerializer(camion, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        camion = self._get_camion(request, pk)
        camion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
