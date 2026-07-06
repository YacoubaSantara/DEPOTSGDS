"""
Base commune des ressources « flotte » de l'API mobile (camions, chauffeurs).

CRUD scopé au marketeur connecté, permissions RBAC par méthode HTTP.
Les sous-classes fournissent : model, serializer_class, les 4 classes de
permission (perm_voir/ajouter/modifier/supprimer), champs_recherche
(lookups icontains pour ?q=), ordering, et optionnellement
optimiser_queryset() pour leurs select_related/prefetch_related.
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication


class _FlotteBaseView(APIView):
    authentication_classes = [JWTAuthentication]

    model = None
    serializer_class = None
    perm_voir = None
    perm_ajouter = None
    perm_modifier = None
    perm_supprimer = None
    champs_recherche = ()   # ex. ('immatriculation', 'marque', 'modele')
    ordering = ()           # ex. ('immatriculation',)

    def optimiser_queryset(self, qs):
        """Hook select_related/prefetch_related propre à la ressource."""
        return qs

    def _qs_marketeur(self, request):
        return self.optimiser_queryset(
            self.model.objects.filter(marketeur=request.user.marketeur)
        )

    def _serializer(self, *args, **kwargs):
        # Toujours passer le request : ChauffeurSerializer en a besoin pour
        # scoper le choix de camion au marketeur ; ignoré par les autres.
        kwargs.setdefault('context', {'request': self.request})
        return self.serializer_class(*args, **kwargs)


class FlotteListCreateView(_FlotteBaseView):
    """GET (liste, filtres ?q=/?statut=) + POST (création assignée au marketeur)."""

    def get_permissions(self):
        if self.request.method == 'POST':
            return [self.perm_ajouter()]
        return [self.perm_voir()]

    def get(self, request):
        qs = self._qs_marketeur(request)

        q = request.query_params.get('q', '').strip()
        if q:
            filtre = Q()
            for champ in self.champs_recherche:
                filtre |= Q(**{f'{champ}__icontains': q})
            qs = qs.filter(filtre)

        statut = request.query_params.get('statut', '')
        if statut:
            qs = qs.filter(statut=statut)

        qs = qs.order_by(*self.ordering)
        return Response(self._serializer(qs, many=True).data)

    def post(self, request):
        serializer = self._serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        obj = serializer.save(marketeur=request.user.marketeur)
        return Response(self._serializer(obj).data, status=status.HTTP_201_CREATED)


class FlotteDetailView(_FlotteBaseView):
    """GET / PATCH (PUT ≡ PATCH) / DELETE, limité aux objets du marketeur."""

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [self.perm_modifier()]
        if self.request.method == 'DELETE':
            return [self.perm_supprimer()]
        return [self.perm_voir()]

    def _get_objet(self, request, pk):
        return get_object_or_404(self._qs_marketeur(request), pk=pk)

    def get(self, request, pk):
        return Response(self._serializer(self._get_objet(request, pk)).data)

    def patch(self, request, pk):
        obj = self._get_objet(request, pk)
        serializer = self._serializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        self._get_objet(request, pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
