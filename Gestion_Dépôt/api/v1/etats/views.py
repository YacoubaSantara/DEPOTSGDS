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

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.v1.permissions import IsMarketeurActif
from SGDS.models import (
    Mouvement, Produit, PeriodeComptable,
    StockOuverture, ParametresCoulage, ClotureCoulageLigne,
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


class StockGlobalView(APIView):
    """
    GET /api/v1/etats/stock-global/

    Paramètres :
      produit    : ID du produit (optionnel)
      date_debut : YYYY-MM-DD (optionnel)
      date_fin   : YYYY-MM-DD (optionnel)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsMarketeurActif]

    def get(self, request):
        marketeur  = request.user.marketeur
        produit_id = request.query_params.get('produit')
        date_debut = request.query_params.get('date_debut')
        date_fin   = request.query_params.get('date_fin')

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

        if date_debut:
            qs = qs.filter(date_mouvement__gte=date_debut)
        if date_fin:
            qs = qs.filter(date_mouvement__lte=date_fin)

        lignes         = []
        stock_courant  = Decimal('0')
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
      date_debut : YYYY-MM-DD (optionnel)
      date_fin   : YYYY-MM-DD (optionnel)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsMarketeurActif]

    def get(self, request):
        marketeur  = request.user.marketeur
        date_debut = request.query_params.get('date_debut')
        date_fin   = request.query_params.get('date_fin')

        qs = (
            Mouvement.objects
            .filter(marketeur=marketeur)
            .select_related('produit')
            .order_by('date_mouvement')
        )
        if date_debut:
            qs = qs.filter(date_mouvement__gte=date_debut)
        if date_fin:
            qs = qs.filter(date_mouvement__lte=date_fin)

        produits_dict = {}
        for m in qs:
            pid = m.produit_id
            if pid not in produits_dict:
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
                    'stock_final_ambiant':    Decimal('0'),
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

        par_produit = sorted(produits_dict.values(), key=lambda x: x['produit_nom'])

        def _sum(key):
            return sum(p[key] for p in par_produit)

        totaux = {
            'nb_mouvements':          qs.count(),
            'nb_entrees':             sum(p['nb_entrees']        for p in par_produit),
            'volume_entree_ambiant':  _sum('volume_entree_ambiant'),
            'nb_sorties':             sum(p['nb_sorties']        for p in par_produit),
            'volume_sortie_ambiant':  _sum('volume_sortie_ambiant'),
            'nb_cessions':            sum(p['nb_cessions']       for p in par_produit),
            'volume_cession_ambiant': _sum('volume_cession_ambiant'),
            'nb_acquittements':       sum(p['nb_acquittements']  for p in par_produit),
            'volume_acquit_ambiant':  _sum('volume_acquit_ambiant'),
            'stock_final_ambiant':    _sum('stock_final_ambiant'),
        }

        data = {
            'marketeur_nom': marketeur.raison_sociale,
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
        periodes = PeriodeComptable.objects.all().order_by('-annee', '-mois')
        data = [
            {
                'id':     p.pk,
                'nom':    str(p),
                'statut': p.statut,
                'mois':   p.mois,
                'annee':  p.annee,
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
    permission_classes     = [IsMarketeurActif]

    def get(self, request):
        marketeur  = request.user.marketeur
        periode_id = request.query_params.get('periode_id')

        # ── Résoudre la période cible ──────────────────────────────
        target_periode = None
        if periode_id:
            try:
                target_periode = PeriodeComptable.objects.get(pk=periode_id)
            except PeriodeComptable.DoesNotExist:
                pass

        if target_periode is None:
            # Priorité à la période ouverte ; sinon la plus récente
            target_periode = (
                PeriodeComptable.objects.filter(statut='OUVERTE').first()
                or PeriodeComptable.objects.first()
            )

        # ── Mouvements de la période ────────────────────────────────
        mvt_qs = (
            Mouvement.objects
            .filter(marketeur=marketeur)
            .select_related('produit')
        )

        if target_periode:
            mvt_qs = mvt_qs.filter(
                date_mouvement__gte=target_periode.date_debut,
                date_mouvement__lte=target_periode.date_fin,
            )

        # Agréger par produit
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

        # ── Stocks d'ouverture ──────────────────────────────────────
        # 1) Depuis le modèle StockOuverture (dépôt global) si disponible
        # 2) Sinon calculé = somme des mouvements AVANT la période
        so_by_produit = {}
        if target_periode:
            for so in StockOuverture.objects.filter(periode=target_periode):
                so_by_produit[so.produit_id] = _D(so.volume_ambiant)

        # Pour les produits sans StockOuverture enregistré, calculer depuis l'historique
        if target_periode:
            for pid in produits_map:
                if pid not in so_by_produit:
                    agg = Mouvement.objects.filter(
                        marketeur=marketeur,
                        produit_id=pid,
                        date_mouvement__lt=target_periode.date_debut,
                    )
                    stock = Decimal('0')
                    for m in agg:
                        t = m.type_mouvement
                        if t == 'ENTREE':
                            stock += _D(m.volume_ambiant_recu)
                        elif t == 'SORTIE':
                            stock -= _D(m.volume_ambiant_sortie)
                        elif t == 'CESSION':
                            stock -= _D(m.cession_volume_ambiant)
                    so_by_produit[pid] = stock

        # ── Construire les lignes ───────────────────────────────────
        lignes = []
        for d in sorted(produits_map.values(), key=lambda x: x['produit_nom']):
            pid        = d['produit_id']
            stock_ouv  = so_by_produit.get(pid, Decimal('0'))
            stock_ferm = stock_ouv + d['entrees'] - d['sorties']
            lignes.append({
                'produit_id':      pid,
                'produit_nom':     d['produit_nom'],
                'produit_sigle':   d['produit_sigle'],
                'stock_ouverture': stock_ouv,
                'entrees':         d['entrees'],
                'sorties':         d['sorties'],
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

    Retourne :
      - tarif_global     : prix unitaire de passage ParametresCoulage en vigueur
      - date_application : date d'application du tarif global
      - produits         : liste avec prix_passage par produit (spécifique ou global)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsMarketeurActif]

    def get(self, request):
        # Tarif global en vigueur aujourd'hui
        params = ParametresCoulage.en_vigueur(date_type.today())
        tarif_global     = _D(params.prix_unitaire_passage) if params else Decimal('0')
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
    permission_classes     = [IsMarketeurActif]

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
