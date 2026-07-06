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
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.v1.permissions import (
    HasVoirChauffeur, HasAjouterChauffeur, HasModifierChauffeur, HasSupprimerChauffeur,
)
from SGDS.models import Chauffeur
from .serializers import ChauffeurSerializer


class ChauffeurListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [HasAjouterChauffeur()]
        return [HasVoirChauffeur()]

    def get(self, request):
        marketeur = request.user.marketeur
        qs = Chauffeur.objects.filter(marketeur=marketeur).select_related('camion')

        q = request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(numero_permis__icontains=q))

        statut = request.query_params.get('statut', '')
        if statut:
            qs = qs.filter(statut=statut)

        qs = qs.order_by('nom', 'prenom')
        serializer = ChauffeurSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = ChauffeurSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        chauffeur = serializer.save(marketeur=request.user.marketeur)
        return Response(ChauffeurSerializer(chauffeur, context={'request': request}).data, status=status.HTTP_201_CREATED)


class ChauffeurDetailView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [HasModifierChauffeur()]
        if self.request.method == 'DELETE':
            return [HasSupprimerChauffeur()]
        return [HasVoirChauffeur()]

    def _get_chauffeur(self, request, pk):
        return get_object_or_404(
            Chauffeur.objects.select_related('camion'),
            pk=pk,
            marketeur=request.user.marketeur,
        )

    def get(self, request, pk):
        chauffeur = self._get_chauffeur(request, pk)
        return Response(ChauffeurSerializer(chauffeur, context={'request': request}).data)

    def patch(self, request, pk):
        chauffeur = self._get_chauffeur(request, pk)
        serializer = ChauffeurSerializer(chauffeur, data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        chauffeur = self._get_chauffeur(request, pk)
        chauffeur.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
