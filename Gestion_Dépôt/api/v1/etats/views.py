"""
Vues des états pour l'API mobile.

Endpoints :
  GET  /api/v1/etats/stock-global/        → carte de stock (filtres : produit, date)
  GET  /api/v1/etats/recap/               → récapitulatif par produit (filtres : date)
  GET  /api/v1/etats/stock-ouverture/     → stock ouverture/fermeture par période
  GET  /api/v1/etats/frais-passage/       → tarifs de passage (global + par produit)
  GET  /api/v1/etats/coulage/             → coulage par marketeur (clôtures mensuelles)
  GET  /api/v1/etats/produits/            → liste des produits actifs
  GET  /api/v1/etats/periodes/            → périodes comptables
"""
from decimal import Decimal
from datetime import date as date_type

from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.v1.permissions import (
    IsMarketeurActif, HasVoirMouvement, HasVoirEtat, HasVoirCoulage, HasVoirFraisPassage,
)
from SGDS.models import (
    Mouvement, Produit, PeriodeComptable,
    StockOuvertureMarketeur, ParametresCoulage, ClotureCoulageLigne,
)
from .serializers import (
    StockGlobalResponseSerializer,
    RecapSerializer,
    StockOuvertureResponseSerializer,
    FraisPassageResponseSerializer,
    CoulageResponseSerializer,
    ProduitDispoSerializer,
    PeriodeSerializer,
)


def _D(val):
    if val is None:
        return Decimal('0')
    return Decimal(str(val)) if not isinstance(val, Decimal) else val


def _periode_cible(periode_id, *, defaut_ouverte=False):
    """
    Résout la période cible d'un état. Les périodes sont PAR DÉPÔT : tout
    état calculé « pour la période X » doit ensuite filtrer les mouvements
    sur periode.depot pour rester cohérent avec son stock d'ouverture.
      - periode_id fourni : la période demandée (None si inexistante) ;
      - sinon, si defaut_ouverte : la période OUVERTE la plus récente
        (ordre déterministe par dépôt), à défaut la plus récente.
    """
    if periode_id:
        try:
            return PeriodeComptable.objects.select_related('depot').get(pk=periode_id)
        except PeriodeComptable.DoesNotExist:
            return None
    if defaut_ouverte:
        base = PeriodeComptable.objects.select_related('depot').order_by(
            '-annee', '-mois', 'depot__nom')
        return base.filter(statut='OUVERTE').first() or base.first()
    return None


class StockGlobalView(APIView):
    """
    GET /api/v1/etats/stock-global/

    Paramètres :
      produit    : ID du produit (optionnel)
      periode_id : ID de PeriodeComptable (optionnel) — si fourni, prime sur
                   date_debut/date_fin et ajoute le stock d'ouverture (report)
                   de la période comme point de départ du stock courant.
      date_debut : YYYY-MM-DD (optionnel, ignoré si periode_id est fourni)
      date_fin   : YYYY-MM-DD (optionnel, ignoré si periode_id est fourni)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [HasVoirEtat]

    def get(self, request):
        marketeur  = request.user.marketeur
        produit_id = request.query_params.get('produit')
        date_debut = request.query_params.get('date_debut')
        date_fin   = request.query_params.get('date_fin')
        periode_id = request.query_params.get('periode_id')

        periode = _periode_cible(periode_id)

        qs = (
            Mouvement.objects
            .filter(marketeur=marketeur)
            .select_related('produit')
            .order_by('date_mouvement', 'date_saisie')
        )

        produit_obj = None
        if produit_id:
            try:
                produit_obj = Produit.objects.get(pk=produit_id)
                qs = qs.filter(produit=produit_obj)
            except Produit.DoesNotExist:
                pass

        if periode:
            # Les périodes sont par dépôt : on scope les mouvements au dépôt
            # de la période pour rester cohérent avec son stock d'ouverture.
            qs = qs.filter(depot=periode.depot,
                           date_mouvement__range=(periode.date_debut, periode.date_fin))
        else:
            if date_debut:
                qs = qs.filter(date_mouvement__gte=date_debut)
            if date_fin:
                qs = qs.filter(date_mouvement__lte=date_fin)

        # ── Stock d'ouverture (report) de la période sélectionnée ─────
        # Même source que l'état « Stock ouverture/fermeture »
        # (StockOuvertureMarketeur, tous régimes douaniers confondus).
        stock_ouverture = Decimal('0')
        if periode:
            som_qs = StockOuvertureMarketeur.objects.filter(periode=periode, marketeur=marketeur)
            if produit_obj:
                som_qs = som_qs.filter(produit=produit_obj)
            stock_ouverture = _D(som_qs.aggregate(t=Sum('volume_ambiant'))['t'])

        lignes         = []
        stock_courant  = stock_ouverture
        cumul_entrees  = Decimal('0')
        cumul_sorties  = Decimal('0')

        for m in qs:
            t = m.type_mouvement

            entree  = _D(m.volume_ambiant_recu)         if t == 'ENTREE'       else Decimal('0')
            sortie  = _D(m.volume_ambiant_sortie)        if t == 'SORTIE'       else Decimal('0')
            cession = _D(m.cession_volume_ambiant)       if t == 'CESSION'      else Decimal('0')

            if t == 'ENTREE':
                stock_courant += entree
                cumul_entrees += entree
            elif t in ('SORTIE', 'CESSION'):
                v = sortie if t == 'SORTIE' else cession
                stock_courant -= v
                cumul_sorties += v

            lignes.append({
                'date':           m.date_mouvement,
                'reference':      m.numero_enregistrement or '',
                'type':           t,
                'entree_ambiant': entree if t == 'ENTREE' else Decimal('0'),
                'entree_15':      _D(m.volume_15c_recu)   if t == 'ENTREE' else Decimal('0'),
                'sortie_ambiant': sortie if t == 'SORTIE' else (cession if t == 'CESSION' else Decimal('0')),
                'sortie_15':      (
                    _D(m.volume_15c_sortie)    if t == 'SORTIE'  else
                    (_D(m.cession_volume_15c)  if t == 'CESSION' else Decimal('0'))
                ),
                'stock_ambiant':  stock_courant,
                'stock_15':       Decimal('0'),
            })

        data = {
            'marketeur_nom': marketeur.raison_sociale,
            'produit_id':    produit_obj.pk  if produit_obj else None,
            'produit_nom':   produit_obj.nom if produit_obj else 'Tous les produits',
            'produit_sigle': (getattr(produit_obj, 'sigle', '') or produit_obj.nom[:4].upper()) if produit_obj else '',
            'periode_id':               periode.pk if periode else None,
            'periode_nom':              str(periode) if periode else '',
            'stock_ouverture_ambiant':  stock_ouverture,
            'lignes':                   lignes,
            'cumul_entrees_ambiant':    cumul_entrees,
            'cumul_entrees_15':         Decimal('0'),
            'cumul_sorties_ambiant':    cumul_sorties,
            'cumul_sorties_15':         Decimal('0'),
            'stock_final_ambiant':      stock_courant,
            'stock_final_15':           Decimal('0'),
        }

        serializer = StockGlobalResponseSerializer(data)
        return Response(serializer.data)


class RecapView(APIView):
    """
    GET /api/v1/etats/recap/

    Récapitulatif des mouvements groupés par produit.
    Paramètres :
      periode_id : ID de PeriodeComptable (optionnel) — prime sur
                   date_debut/date_fin ; ajoute le stock d'ouverture (report)
                   de la période comme point de départ du stock final.
      date_debut : YYYY-MM-DD (optionnel, ignoré si periode_id est fourni)
      date_fin   : YYYY-MM-DD (optionnel, ignoré si periode_id est fourni)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [HasVoirMouvement]

    def get(self, request):
        marketeur  = request.user.marketeur
        date_debut = request.query_params.get('date_debut')
        date_fin   = request.query_params.get('date_fin')
        periode_id = request.query_params.get('periode_id')

        periode = _periode_cible(periode_id)

        qs = (
            Mouvement.objects
            .filter(marketeur=marketeur)
            .select_related('produit')
            .order_by('date_mouvement')
        )
        if periode:
            # Cohérence dépôt : voir _periode_cible
            qs = qs.filter(depot=periode.depot,
                           date_mouvement__range=(periode.date_debut, periode.date_fin))
        else:
            if date_debut:
                qs = qs.filter(date_mouvement__gte=date_debut)
            if date_fin:
                qs = qs.filter(date_mouvement__lte=date_fin)

        # ── Stock d'ouverture (report) par produit, pour la période ───
        # Même source que l'état « Stock ouverture/fermeture » (tous
        # régimes douaniers confondus).
        ouverture_par_produit = {}
        if periode:
            for som in StockOuvertureMarketeur.objects.filter(periode=periode, marketeur=marketeur):
                pid = som.produit_id
                ouverture_par_produit[pid] = ouverture_par_produit.get(pid, Decimal('0')) + _D(som.volume_ambiant)

        produits_dict = {}
        for m in qs:
            pid = m.produit_id
            if pid not in produits_dict:
                stock_ouverture = ouverture_par_produit.get(pid, Decimal('0'))
                produits_dict[pid] = {
                    'produit_id':             pid,
                    'produit_nom':            m.produit.nom,
                    'produit_sigle':          getattr(m.produit, 'sigle', '') or m.produit.nom[:4].upper(),
                    'nb_entrees':             0,
                    'volume_entree_ambiant':  Decimal('0'),
                    'volume_entree_15':       Decimal('0'),
                    'nb_sorties':             0,
                    'volume_sortie_ambiant':  Decimal('0'),
                    'nb_cessions':            0,
                    'volume_cession_ambiant': Decimal('0'),
                    'nb_acquittements':       0,
                    'volume_acquit_ambiant':  Decimal('0'),
                    'stock_ouverture_ambiant': stock_ouverture,
                    'stock_final_ambiant':    stock_ouverture,
                }
            d = produits_dict[pid]
            t = m.type_mouvement

            if t == 'ENTREE':
                d['nb_entrees']            += 1
                d['volume_entree_ambiant'] += _D(m.volume_ambiant_recu)
                d['volume_entree_15']      += _D(m.volume_15c_recu)
                d['stock_final_ambiant']   += _D(m.volume_ambiant_recu)
            elif t == 'SORTIE':
                d['nb_sorties']            += 1
                d['volume_sortie_ambiant'] += _D(m.volume_ambiant_sortie)
                d['stock_final_ambiant']   -= _D(m.volume_ambiant_sortie)
            elif t == 'CESSION':
                d['nb_cessions']           += 1
                d['volume_cession_ambiant'] += _D(m.cession_volume_ambiant)
                d['stock_final_ambiant']   -= _D(m.cession_volume_ambiant)
            elif t == 'ACQUITTEMENT':
                d['nb_acquittements']      += 1
                d['volume_acquit_ambiant'] += _D(m.acquittement_volume_ambiant)

        # Inclure les produits qui n'ont qu'un stock d'ouverture (aucun
        # mouvement sur la période), pour que le report reste visible.
        for pid, stock_ouverture in ouverture_par_produit.items():
            if pid in produits_dict or stock_ouverture == 0:
                continue
            try:
                produit = Produit.objects.get(pk=pid)
            except Produit.DoesNotExist:
                continue
            produits_dict[pid] = {
                'produit_id':             pid,
                'produit_nom':            produit.nom,
                'produit_sigle':          getattr(produit, 'sigle', '') or produit.nom[:4].upper(),
                'nb_entrees':             0,
                'volume_entree_ambiant':  Decimal('0'),
                'volume_entree_15':       Decimal('0'),
                'nb_sorties':             0,
                'volume_sortie_ambiant':  Decimal('0'),
                'nb_cessions':            0,
                'volume_cession_ambiant': Decimal('0'),
                'nb_acquittements':       0,
                'volume_acquit_ambiant':  Decimal('0'),
                'stock_ouverture_ambiant': stock_ouverture,
                'stock_final_ambiant':    stock_ouverture,
            }

        par_produit = sorted(produits_dict.values(), key=lambda x: x['produit_nom'])

        def _sum(key):
            return sum(p[key] for p in par_produit)

        totaux = {
            'nb_mouvements':           qs.count(),
            'nb_entrees':              sum(p['nb_entrees']        for p in par_produit),
            'volume_entree_ambiant':   _sum('volume_entree_ambiant'),
            'nb_sorties':              sum(p['nb_sorties']        for p in par_produit),
            'volume_sortie_ambiant':   _sum('volume_sortie_ambiant'),
            'nb_cessions':             sum(p['nb_cessions']       for p in par_produit),
            'volume_cession_ambiant':  _sum('volume_cession_ambiant'),
            'nb_acquittements':        sum(p['nb_acquittements']  for p in par_produit),
            'volume_acquit_ambiant':   _sum('volume_acquit_ambiant'),
            'stock_ouverture_ambiant': _sum('stock_ouverture_ambiant'),
            'stock_final_ambiant':     _sum('stock_final_ambiant'),
        }

        data = {
            'marketeur_nom': marketeur.raison_sociale,
            'periode_id':    periode.pk if periode else None,
            'periode_nom':   str(periode) if periode else '',
            'par_produit':   par_produit,
            'totaux':        totaux,
        }
        serializer = RecapSerializer(data)
        return Response(serializer.data)


class ProduitsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsMarketeurActif]

    def get(self, request):
        produits = Produit.objects.filter(statut='ACTIF').order_by('nom')
        data = [
            {
                'id':    p.pk,
                'nom':   p.nom,
                'sigle': getattr(p, 'sigle', '') or p.nom[:4].upper(),
            }
            for p in produits
        ]
        serializer = ProduitDispoSerializer(data, many=True)
        return Response(serializer.data)


class PeriodesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsMarketeurActif]

    def get(self, request):
        periodes = (
            PeriodeComptable.objects.select_related('depot')
            .order_by('-annee', '-mois', 'depot__nom')
        )
        plusieurs_depots = len({p.depot_id for p in periodes}) > 1
        data = [
            {
                'id':     p.pk,
                # Les périodes sont par dépôt : dès qu'il y en a plusieurs,
                # le libellé distingue les mois homonymes.
                'nom':    f"{p} — {p.depot}" if plusieurs_depots else str(p),
                'statut': p.statut,
                'mois':   p.mois,
                'annee':  p.annee,
                'depot_id':  p.depot_id,
                'depot_nom': str(p.depot) if p.depot_id else '',
            }
            for p in periodes
        ]
        serializer = PeriodeSerializer(data, many=True)
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────
#  STOCK OUVERTURE / FERMETURE
# ─────────────────────────────────────────────────────────────────────

class StockOuvertureFermetureView(APIView):
    """
    GET /api/v1/etats/stock-ouverture/

    Paramètres :
      periode_id : ID de PeriodeComptable (optionnel — défaut = période ouverte)

    Retourne, pour chaque produit du marketeur :
      - stock_ouverture  (depuis StockOuverture ou calculé à partir des mouvements précédents)
      - entrees          (somme des entrées pendant la période)
      - sorties          (somme des sorties/cessions pendant la période)
      - stock_fermeture  = ouverture + entrées − sorties
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [HasVoirEtat]

    def get(self, request):
        marketeur  = request.user.marketeur
        periode_id = request.query_params.get('periode_id')

        # ── Résoudre la période cible (périodes par dépôt) ─────────
        target_periode = _periode_cible(periode_id, defaut_ouverte=True)

        # ── Mouvements propres du marketeur ────────────────────────
        mvt_qs = (
            Mouvement.objects
            .filter(marketeur=marketeur)
            .select_related('produit')
        )
        # Cessions reçues par ce marketeur (enregistrées sous le marketeur émetteur)
        cessions_recues_qs = (
            Mouvement.objects
            .filter(cession_marketeur_destinataire=marketeur, type_mouvement='CESSION')
            .select_related('produit')
        )

        if target_periode:
            # Cohérence dépôt : le stock d'ouverture (StockOuvertureMarketeur)
            # est lié à la période — donc au dépôt — cible.
            mvt_qs = mvt_qs.filter(
                depot=target_periode.depot,
                date_mouvement__gte=target_periode.date_debut,
                date_mouvement__lte=target_periode.date_fin,
            )
            cessions_recues_qs = cessions_recues_qs.filter(
                depot=target_periode.depot,
                date_mouvement__gte=target_periode.date_debut,
                date_mouvement__lte=target_periode.date_fin,
            )

        # Agréger par produit — mouvements propres
        produits_map = {}
        for m in mvt_qs:
            pid = m.produit_id
            if pid not in produits_map:
                produits_map[pid] = {
                    'produit_id':    pid,
                    'produit_nom':   m.produit.nom,
                    'produit_sigle': getattr(m.produit, 'sigle', '') or m.produit.nom[:4].upper(),
                    'entrees':       Decimal('0'),
                    'sorties':       Decimal('0'),
                }
            t = m.type_mouvement
            if t == 'ENTREE':
                produits_map[pid]['entrees'] += _D(m.volume_ambiant_recu)
            elif t == 'SORTIE':
                produits_map[pid]['sorties'] += _D(m.volume_ambiant_sortie)
            elif t == 'CESSION':
                produits_map[pid]['sorties'] += _D(m.cession_volume_ambiant)

        # Cessions reçues → entrées
        for m in cessions_recues_qs:
            pid = m.produit_id
            if pid not in produits_map:
                produits_map[pid] = {
                    'produit_id':    pid,
                    'produit_nom':   m.produit.nom,
                    'produit_sigle': getattr(m.produit, 'sigle', '') or m.produit.nom[:4].upper(),
                    'entrees':       Decimal('0'),
                    'sorties':       Decimal('0'),
                }
            produits_map[pid]['entrees'] += _D(m.cession_volume_ambiant)

        # ── Stocks d'ouverture depuis StockOuvertureMarketeur ───────
        # Somme SD + AC par produit, pour ce marketeur et cette période
        so_by_produit = {}
        if target_periode:
            for som in StockOuvertureMarketeur.objects.filter(
                periode=target_periode, marketeur=marketeur
            ).select_related('produit'):
                pid = som.produit_id
                if pid not in so_by_produit:
                    so_by_produit[pid] = Decimal('0')
                so_by_produit[pid] += _D(som.volume_ambiant)

        # Fallback : produits sans StockOuvertureMarketeur → calculé depuis l'historique
        if target_periode:
            for pid in list(produits_map.keys()):
                if pid not in so_by_produit:
                    agg_own = Mouvement.objects.filter(
                        marketeur=marketeur,
                        produit_id=pid,
                        date_mouvement__lt=target_periode.date_debut,
                    )
                    agg_recu = Mouvement.objects.filter(
                        cession_marketeur_destinataire=marketeur,
                        produit_id=pid,
                        type_mouvement='CESSION',
                        date_mouvement__lt=target_periode.date_debut,
                    )
                    stock = Decimal('0')
                    for m in agg_own:
                        t = m.type_mouvement
                        if t == 'ENTREE':
                            stock += _D(m.volume_ambiant_recu)
                        elif t == 'SORTIE':
                            stock -= _D(m.volume_ambiant_sortie)
                        elif t == 'CESSION':
                            stock -= _D(m.cession_volume_ambiant)
                    for m in agg_recu:
                        stock += _D(m.cession_volume_ambiant)
                    so_by_produit[pid] = max(stock, Decimal('0'))

        # Produits avec stock d'ouverture mais sans mouvement cette période
        # → les ajouter quand même pour que les totaux d'ouverture soient exacts
        if target_periode:
            for som in StockOuvertureMarketeur.objects.filter(
                periode=target_periode, marketeur=marketeur
            ).select_related('produit'):
                pid = som.produit_id
                if pid not in produits_map and som.produit:
                    produits_map[pid] = {
                        'produit_id':    pid,
                        'produit_nom':   som.produit.nom,
                        'produit_sigle': getattr(som.produit, 'sigle', '') or som.produit.nom[:4].upper(),
                        'entrees':       Decimal('0'),
                        'sorties':       Decimal('0'),
                    }

        # ── Quote-part coulage (qp_coul) par produit ────────────────
        # La QP P/G Installation s'ajoute au stock Acquitté en clôture
        # (peut être positive ou négative). Identique à la logique web :
        #   Stock Clôture = Stock Comptable + qp_coul  (côté AC uniquement)
        qp_by_produit = {}
        if target_periode:
            for ligne in ClotureCoulageLigne.objects.filter(
                marketeur=marketeur,
                cloture__periode=target_periode,
            ).select_related('produit'):
                pid = ligne.produit_id
                if pid not in qp_by_produit:
                    qp_by_produit[pid] = Decimal('0')
                qp_by_produit[pid] += _D(ligne.qp_coul)

        # ── Construire les lignes ───────────────────────────────────
        lignes = []
        for d in sorted(produits_map.values(), key=lambda x: x['produit_nom']):
            pid        = d['produit_id']
            stock_ouv  = so_by_produit.get(pid, Decimal('0'))
            qp_coul    = qp_by_produit.get(pid, Decimal('0'))
            sorties    = d['sorties']                                  # mouvements uniquement (idem web)
            stock_ferm = stock_ouv + d['entrees'] - sorties + qp_coul  # QP s'ajoute à la fermeture (côté AC)
            lignes.append({
                'produit_id':      pid,
                'produit_nom':     d['produit_nom'],
                'produit_sigle':   d['produit_sigle'],
                'stock_ouverture': stock_ouv,
                'entrees':         d['entrees'],
                'sorties':         sorties,
                'stock_fermeture': stock_ferm,
            })

        def _s(key):
            return sum(l[key] for l in lignes)

        data = {
            'marketeur_nom':   marketeur.raison_sociale,
            'periode_id':      target_periode.pk  if target_periode else None,
            'periode_nom':     str(target_periode) if target_periode else '',
            'lignes':          lignes,
            'total_ouverture': _s('stock_ouverture'),
            'total_entrees':   _s('entrees'),
            'total_sorties':   _s('sorties'),
            'total_fermeture': _s('stock_fermeture'),
        }
        return Response(StockOuvertureResponseSerializer(data).data)


class Stock15View(APIView):
    """
    GET /api/v1/etats/stock-15/

    Équivalent de StockOuvertureFermetureView, mais en volumes @15°C
    (standard température) au lieu de volumes ambiants.

    Paramètres :
      periode_id : ID de PeriodeComptable (optionnel — défaut = période ouverte)

    Retourne, pour chaque produit du marketeur :
      - stock_ouverture  (StockOuvertureMarketeur.volume_15c de la période)
      - entrees          (Σ volume_15c_recu pendant la période)
      - sorties          (Σ volume_15c_sortie / cession_volume_15c pendant la période)
      - stock_fermeture  = ouverture + entrées − sorties

    Le coulage n'étant pas suivi en @15°C dans ce système (cf. web
    SGDS/views/mensuel.py::_calculer_stock_a_15), aucune quote-part n'est
    ajoutée ici, contrairement au stock ambiant.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [HasVoirEtat]

    def get(self, request):
        marketeur  = request.user.marketeur
        periode_id = request.query_params.get('periode_id')

        target_periode = _periode_cible(periode_id, defaut_ouverte=True)

        mvt_qs = (
            Mouvement.objects
            .filter(marketeur=marketeur)
            .select_related('produit')
        )
        cessions_recues_qs = (
            Mouvement.objects
            .filter(cession_marketeur_destinataire=marketeur, type_mouvement='CESSION')
            .select_related('produit')
        )

        if target_periode:
            # Cohérence dépôt : voir _periode_cible
            mvt_qs = mvt_qs.filter(
                depot=target_periode.depot,
                date_mouvement__gte=target_periode.date_debut,
                date_mouvement__lte=target_periode.date_fin,
            )
            cessions_recues_qs = cessions_recues_qs.filter(
                depot=target_periode.depot,
                date_mouvement__gte=target_periode.date_debut,
                date_mouvement__lte=target_periode.date_fin,
            )

        produits_map = {}
        for m in mvt_qs:
            pid = m.produit_id
            if pid not in produits_map:
                produits_map[pid] = {
                    'produit_id':    pid,
                    'produit_nom':   m.produit.nom,
                    'produit_sigle': getattr(m.produit, 'sigle', '') or m.produit.nom[:4].upper(),
                    'entrees':       Decimal('0'),
                    'sorties':       Decimal('0'),
                }
            t = m.type_mouvement
            if t == 'ENTREE':
                produits_map[pid]['entrees'] += _D(m.volume_15c_recu)
            elif t == 'SORTIE':
                produits_map[pid]['sorties'] += _D(m.volume_15c_sortie)
            elif t == 'CESSION':
                produits_map[pid]['sorties'] += _D(m.cession_volume_15c)

        for m in cessions_recues_qs:
            pid = m.produit_id
            if pid not in produits_map:
                produits_map[pid] = {
                    'produit_id':    pid,
                    'produit_nom':   m.produit.nom,
                    'produit_sigle': getattr(m.produit, 'sigle', '') or m.produit.nom[:4].upper(),
                    'entrees':       Decimal('0'),
                    'sorties':       Decimal('0'),
                }
            produits_map[pid]['entrees'] += _D(m.cession_volume_15c)

        # ── Stocks d'ouverture @15°C depuis StockOuvertureMarketeur ───
        so_by_produit = {}
        if target_periode:
            for som in StockOuvertureMarketeur.objects.filter(
                periode=target_periode, marketeur=marketeur
            ).select_related('produit'):
                pid = som.produit_id
                so_by_produit[pid] = so_by_produit.get(pid, Decimal('0')) + _D(som.volume_15c)

        # Fallback : produits sans StockOuvertureMarketeur → calculé depuis l'historique
        if target_periode:
            for pid in list(produits_map.keys()):
                if pid not in so_by_produit:
                    agg_own = Mouvement.objects.filter(
                        marketeur=marketeur,
                        produit_id=pid,
                        date_mouvement__lt=target_periode.date_debut,
                    )
                    agg_recu = Mouvement.objects.filter(
                        cession_marketeur_destinataire=marketeur,
                        produit_id=pid,
                        type_mouvement='CESSION',
                        date_mouvement__lt=target_periode.date_debut,
                    )
                    stock = Decimal('0')
                    for m in agg_own:
                        t = m.type_mouvement
                        if t == 'ENTREE':
                            stock += _D(m.volume_15c_recu)
                        elif t == 'SORTIE':
                            stock -= _D(m.volume_15c_sortie)
                        elif t == 'CESSION':
                            stock -= _D(m.cession_volume_15c)
                    for m in agg_recu:
                        stock += _D(m.cession_volume_15c)
                    so_by_produit[pid] = max(stock, Decimal('0'))

        # Produits avec stock d'ouverture mais sans mouvement cette période
        if target_periode:
            for som in StockOuvertureMarketeur.objects.filter(
                periode=target_periode, marketeur=marketeur
            ).select_related('produit'):
                pid = som.produit_id
                if pid not in produits_map and som.produit:
                    produits_map[pid] = {
                        'produit_id':    pid,
                        'produit_nom':   som.produit.nom,
                        'produit_sigle': getattr(som.produit, 'sigle', '') or som.produit.nom[:4].upper(),
                        'entrees':       Decimal('0'),
                        'sorties':       Decimal('0'),
                    }

        lignes = []
        for d in sorted(produits_map.values(), key=lambda x: x['produit_nom']):
            pid        = d['produit_id']
            stock_ouv  = so_by_produit.get(pid, Decimal('0'))
            sorties    = d['sorties']
            stock_ferm = stock_ouv + d['entrees'] - sorties
            lignes.append({
                'produit_id':      pid,
                'produit_nom':     d['produit_nom'],
                'produit_sigle':   d['produit_sigle'],
                'stock_ouverture': stock_ouv,
                'entrees':         d['entrees'],
                'sorties':         sorties,
                'stock_fermeture': stock_ferm,
            })

        def _s(key):
            return sum(l[key] for l in lignes)

        data = {
            'marketeur_nom':   marketeur.raison_sociale,
            'periode_id':      target_periode.pk  if target_periode else None,
            'periode_nom':     str(target_periode) if target_periode else '',
            'lignes':          lignes,
            'total_ouverture': _s('stock_ouverture'),
            'total_entrees':   _s('entrees'),
            'total_sorties':   _s('sorties'),
            'total_fermeture': _s('stock_fermeture'),
        }
        return Response(StockOuvertureResponseSerializer(data).data)


# ─────────────────────────────────────────────────────────────────────
#  FRAIS DE PASSAGE
# ─────────────────────────────────────────────────────────────────────

class FraisPassageView(APIView):
    """
    GET /api/v1/etats/frais-passage/

    Paramètres :
      periode_id : ID de PeriodeComptable (optionnel) — résout le tarif en
                   vigueur à la date de début de cette période, au lieu
                   d'aujourd'hui (utile pour consulter le tarif d'un mois
                   passé si plusieurs tarifs se sont succédé).

    Retourne :
      - tarif_global     : prix unitaire de passage ParametresCoulage en vigueur
      - date_application : date d'application du tarif global
      - produits         : liste avec prix_passage par produit (spécifique ou global)

    Si aucun ParametresCoulage n'est configuré, on retombe sur le même tarif
    par défaut que le document web (cf. SGDS/services/frais_passage.py::
    calculer_frais_passage), pour rester cohérent entre les deux plateformes.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [HasVoirFraisPassage]

    TARIF_DEFAUT = Decimal('4.7554')

    def get(self, request):
        periode_id = request.query_params.get('periode_id')
        periode = _periode_cible(periode_id)

        ref_date = periode.date_debut if periode else date_type.today()
        params = ParametresCoulage.en_vigueur(ref_date)
        tarif_global     = _D(params.prix_unitaire_passage) if params else self.TARIF_DEFAUT
        date_application = str(params.date_application)     if params else ''

        # Produits actifs avec leur tarif spécifique éventuel
        produits = Produit.objects.filter(statut='ACTIF').order_by('nom')
        produits_data = []
        for p in produits:
            prix_specifique = getattr(p, 'prix_passage', None)
            if prix_specifique:
                prix  = _D(prix_specifique)
                is_gl = False
            else:
                prix  = tarif_global
                is_gl = True
            produits_data.append({
                'produit_id':    p.pk,
                'produit_nom':   p.nom,
                'produit_sigle': getattr(p, 'sigle', '') or p.nom[:4].upper(),
                'prix_passage':  prix,
                'is_global':     is_gl,
            })

        data = {
            'tarif_global':     tarif_global,
            'date_application': date_application,
            'periode_id':       periode.pk if periode else None,
            'periode_nom':      str(periode) if periode else '',
            'produits':         produits_data,
        }
        return Response(FraisPassageResponseSerializer(data).data)


# ─────────────────────────────────────────────────────────────────────
#  COULAGE DES MARKETEURS
# ─────────────────────────────────────────────────────────────────────

class CoulageView(APIView):
    """
    GET /api/v1/etats/coulage/

    Paramètres :
      periode_id : ID de PeriodeComptable (optionnel — retourne toutes les clôtures si absent)

    Retourne les lignes de coulage (ClotureCoulageLigne) du marketeur connecté,
    avec les totaux.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [HasVoirCoulage]

    def get(self, request):
        marketeur  = request.user.marketeur
        periode_id = request.query_params.get('periode_id')

        lignes_qs = (
            ClotureCoulageLigne.objects
            .filter(marketeur=marketeur)
            .select_related('cloture__periode', 'produit')
            .order_by('-cloture__periode__annee', '-cloture__periode__mois', 'produit__nom')
        )

        if periode_id:
            lignes_qs = lignes_qs.filter(cloture__periode_id=periode_id)

        lignes = []
        for l in lignes_qs:
            produit_nom   = l.produit.nom  if l.produit else ''
            produit_sigle = (
                getattr(l.produit, 'sigle', '') or l.produit.nom[:4].upper()
            ) if l.produit else ''

            lignes.append({
                'periode_id':    l.cloture.periode_id,
                'periode_nom':   str(l.cloture.periode),
                'produit_id':    l.produit_id,
                'produit_nom':   produit_nom,
                'produit_sigle': produit_sigle,
                'brut_entree':   _D(l.brut_entree),
                'coul_entree':   _D(l.coul_entree),
                'entree_nette':  _D(l.entree_nette),
                'sortie':        _D(l.sortie),
                'qp_coul':       _D(l.qp_coul),
                'volume_sorti':  _D(l.volume_sorti),
                'prix_unitaire': _D(l.prix_unitaire),
                'montant':       _D(l.montant),
                'motif':         l.motif or '',
            })

        total_montant = sum(l['montant']      for l in lignes)
        total_volume  = sum(l['volume_sorti'] for l in lignes)

        data = {
            'marketeur_nom':      marketeur.raison_sociale,
            'lignes':             lignes,
            'total_montant':      total_montant,
            'total_volume_sorti': total_volume,
        }
        return Response(CoulageResponseSerializer(data).data)
