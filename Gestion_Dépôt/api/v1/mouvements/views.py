"""
Vues mouvements pour l'API mobile.

Endpoints :
  GET /api/v1/mouvements/          → liste paginée (filtres : produit, type, regime, date)
  GET /api/v1/mouvements/{id}/     → détail complet d'un mouvement
"""
from decimal import Decimal

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404

from api.v1.permissions import IsMarketeurActif
from SGDS.models import Mouvement
from .serializers import MouvementListSerializer, MouvementDetailSerializer


LABELS_TYPE = {
    'ENTREE':       'Entrée',
    'SORTIE':       'Sortie',
    'CESSION':      'Cession',
    'ACQUITTEMENT': 'Acquittement',
}
LABELS_REGIME = {
    'ACQUITTE':    'Acquitté',
    'SOUS_DOUANE': 'Sous douane',
}

PAGE_SIZE = 20


def _volume_amb(m):
    t = m.type_mouvement
    if t == 'ENTREE':        return m.volume_ambiant_recu
    if t == 'SORTIE':        return m.volume_ambiant_sortie
    if t == 'CESSION':       return m.cession_volume_ambiant
    if t == 'ACQUITTEMENT':  return m.acquittement_volume_ambiant
    return None


def _volume_15c(m):
    t = m.type_mouvement
    if t == 'ENTREE':        return m.volume_15c_recu
    if t == 'SORTIE':        return m.volume_15c_sortie
    if t == 'CESSION':       return m.cession_volume_15c
    if t == 'ACQUITTEMENT':  return m.acquittement_volume_15c
    return None


def _serialize_list(m):
    return {
        'id':               m.pk,
        'reference':        m.numero_enregistrement or '',
        'type':             m.type_mouvement,
        'produit_id':       m.produit_id,
        'produit':          m.produit.nom,
        'produit_sigle':    getattr(m.produit, 'sigle', '') or m.produit.nom[:4].upper(),
        'regime':           LABELS_REGIME.get(m.regime_douanier, m.regime_douanier),
        'date':             m.date_saisie,       # DateTimeField → inclut la date ET l'heure
        'quantite_ambiant': _volume_amb(m) or 0,
        'quantite_15':      _volume_15c(m) or 0,
        'observation':      m.notes or '',
    }


def _serialize_detail(m):
    d = _serialize_list(m)
    d.update({
        'provenance':                      m.provenance,
        'bl_expediteur':                   m.bl_expediteur,
        'bl_client':                       m.bl_client,
        'date_chargement':                 m.date_chargement,
        'date_dechargement':               m.date_dechargement,
        'volume_ambiant_expediteur':       m.volume_ambiant_expediteur,
        'volume_ambiant_recu':             m.volume_ambiant_recu,
        'volume_15c_recu':                 m.volume_15c_recu,
        'perte_gain_reception':            m.perte_gain_reception,
        'camion_immatriculation':          m.camion.immatriculation if m.camion else None,
        'chauffeur_nom':                   f"{m.chauffeur.prenom} {m.chauffeur.nom}" if m.chauffeur else None,
        'destination':                     m.destination,
        'numero_permis_sortie':            m.numero_permis_sortie,
        'volume_ambiant_sortie':           m.volume_ambiant_sortie,
        'volume_15c_sortie':               m.volume_15c_sortie,
        'mode_reglement':                  m.mode_reglement,
        'cession_destinataire':            m.cession_marketeur_destinataire.raison_sociale if m.cession_marketeur_destinataire else None,
        'cession_volume_ambiant':          m.cession_volume_ambiant,
        'cession_volume_15c':              m.cession_volume_15c,
        'cession_motif':                   m.cession_motif,
        'acquittement_volume_ambiant':     m.acquittement_volume_ambiant,
        'acquittement_reference_declaration': m.acquittement_reference_declaration,
        'acquittement_date_declaration':   m.acquittement_date_declaration,
    })
    return d


class MouvementListView(APIView):
    """
    GET /api/v1/mouvements/

    Paramètres (query string) :
      - produit      : ID du produit
      - type         : ENTREE | SORTIE | CESSION | ACQUITTEMENT
      - regime       : ACQUITTE | SOUS_DOUANE
      - date_debut   : YYYY-MM-DD
      - date_fin     : YYYY-MM-DD
      - page         : numéro de page (défaut 1)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsMarketeurActif]

    def get(self, request):
        marketeur = request.user.marketeur
        qs = (
            Mouvement.objects
            .filter(marketeur=marketeur)
            .select_related('produit', 'camion', 'chauffeur')
            .order_by('-date_mouvement', '-date_saisie')
        )

        # Filtres
        produit_id = request.query_params.get('produit')
        if produit_id:
            qs = qs.filter(produit_id=produit_id)

        type_mv = request.query_params.get('type', '').upper()
        if type_mv in ('ENTREE', 'SORTIE', 'CESSION', 'ACQUITTEMENT'):
            qs = qs.filter(type_mouvement=type_mv)

        regime = request.query_params.get('regime', '').upper()
        if regime in ('ACQUITTE', 'SOUS_DOUANE'):
            qs = qs.filter(regime_douanier=regime)

        date_debut = request.query_params.get('date_debut')
        if date_debut:
            qs = qs.filter(date_mouvement__gte=date_debut)

        date_fin = request.query_params.get('date_fin')
        if date_fin:
            qs = qs.filter(date_mouvement__lte=date_fin)

        # Pagination manuelle
        count = qs.count()
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (ValueError, TypeError):
            page = 1
        start = (page - 1) * PAGE_SIZE
        end   = start + PAGE_SIZE
        items = qs[start:end]

        base_url = request.build_absolute_uri(request.path)
        params   = request.query_params.copy()

        def make_url(p):
            params['page'] = p
            return f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

        import math
        total_pages = max(1, math.ceil(count / PAGE_SIZE))
        return Response({
            'count':       count,
            'page':        page,
            'page_size':   PAGE_SIZE,
            'total_pages': total_pages,
            'results':     [_serialize_list(m) for m in items],
        })


class MouvementDetailView(APIView):
    """
    GET /api/v1/mouvements/{id}/

    Retourne le détail complet d'un mouvement.
    L'utilisateur ne peut accéder qu'aux mouvements de son propre marketeur.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsMarketeurActif]

    def get(self, request, pk):
        marketeur = request.user.marketeur
        m = get_object_or_404(
            Mouvement.objects.select_related(
                'produit', 'camion', 'chauffeur', 'cession_marketeur_destinataire'
            ),
            pk=pk,
            marketeur=marketeur  # sécurité : seulement ses propres mouvements
        )
        serializer = MouvementDetailSerializer(_serialize_detail(m))
        return Response(serializer.data)
