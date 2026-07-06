"""
Tableau de bord marketeur — API mobile.
GET /api/v1/dashboard/
"""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.v1.permissions import IsMarketeurActif
from SGDS.models import (
    Mouvement, Produit, Cuve, InventaireInitialMarketeur,
    PeriodeComptable, StockOuvertureMarketeur,
)
from .serializers import DashboardSerializer


def _D(val):
    """Convertit en Decimal, 0 si None."""
    if val is None:
        return Decimal('0')
    return Decimal(str(val)) if not isinstance(val, Decimal) else val


def _volume_amb(m):
    t = m.type_mouvement
    if t == 'ENTREE':       return _D(m.volume_ambiant_recu)
    if t == 'SORTIE':       return _D(m.volume_ambiant_sortie)
    if t == 'CESSION':      return _D(m.cession_volume_ambiant)
    if t == 'ACQUITTEMENT': return _D(m.acquittement_volume_ambiant)
    return Decimal('0')


def _volume_15(m):
    t = m.type_mouvement
    if t == 'ENTREE':       return _D(m.volume_15c_recu)
    if t == 'SORTIE':       return _D(m.volume_15c_sortie)
    if t == 'CESSION':      return _D(m.cession_volume_15c)
    if t == 'ACQUITTEMENT': return _D(m.acquittement_volume_15c)
    return Decimal('0')


def _quote_part_coulage(marketeur, periode_courante):
    """
    Quote-part P/G Installation (ambiant) de la période en cours pour ce
    marketeur — même logique que le dashboard web, cf.
    SGDS/views/client.py::_calculer_stock_par_produit.
    """
    if not periode_courante:
        return {}
    try:
        from SGDS.services.coulage_repartition import calculer_repartition_coulage
        rapport = calculer_repartition_coulage(periode_courante, marketeurs=[marketeur])
        if rapport['lignes']:
            return rapport['lignes'][0]['par_produit']
    except Exception:
        pass
    return {}


def _calc_stock_produit(marketeur, produit, periode_courante, ac_ouverture,
                         inventaires_agg, qp_coul_par_produit, upto=None):
    """
    Calcule le stock (ambiant et @15°C) d'un produit pour un marketeur, sur
    la période comptable en cours (ou sur tout l'historique s'il n'y a pas
    encore de période), en s'alignant sur la formule du dashboard web :
      stock = stock d'ouverture (StockOuvertureMarketeur ACQUITTE, reporté
              depuis la fermeture du mois précédent)
            + entrées ACQUITTE + acquittements + cessions reçues
            - sorties - cessions émises
            + quote-part P/G Installation (ambiant uniquement)
    `upto` permet de borner les mouvements pris en compte (ex. calcul du
    stock « à hier » pour la variation journalière).
    """
    qs = Mouvement.objects.filter(marketeur=marketeur, produit=produit)
    qs_recu = Mouvement.objects.filter(
        cession_marketeur_destinataire=marketeur,
        produit=produit,
        type_mouvement='CESSION',
    )
    if periode_courante:
        qs = qs.filter(date_mouvement__range=(periode_courante.date_debut, periode_courante.date_fin))
        qs_recu = qs_recu.filter(date_mouvement__range=(periode_courante.date_debut, periode_courante.date_fin))
    if upto is not None:
        qs = qs.filter(date_mouvement__lte=upto)
        qs_recu = qs_recu.filter(date_mouvement__lte=upto)

    inv_data   = inventaires_agg.get(produit.pk, {})
    inv_sd_amb = inv_data.get('sd_amb', Decimal('0'))
    inv_sd_15  = inv_data.get('sd_15',  Decimal('0'))

    # Stock d'ouverture ACQUITTE : reporté depuis la fermeture du mois
    # précédent (StockOuvertureMarketeur) si disponible pour la période en
    # cours, sinon repli sur l'inventaire initial du marketeur.
    ouverture = ac_ouverture.get(produit.pk)
    if ouverture is not None:
        inv_ac_amb = ouverture['amb']
        inv_ac_15  = ouverture['15c']
    else:
        inv_ac_amb = inv_data.get('ac_amb', Decimal('0'))
        inv_ac_15  = inv_data.get('ac_15',  Decimal('0'))

    # Ambiant — base = stock d'ouverture ACQUITTE uniquement.
    # ENTREE SOUS_DOUANE ignorée ; l'ACQUITTEMENT AJOUTE au stock disponible.
    e_amb = _D(qs.filter(type_mouvement='ENTREE', regime_douanier='ACQUITTE').aggregate(t=Sum('volume_ambiant_recu'))['t'])
    s_amb = _D(qs.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_ambiant_sortie'))['t'])
    c_amb = _D(qs.filter(type_mouvement='CESSION').aggregate(t=Sum('cession_volume_ambiant'))['t'])
    a_amb = _D(qs.filter(type_mouvement='ACQUITTEMENT').aggregate(t=Sum('acquittement_volume_ambiant'))['t'])
    r_amb = _D(qs_recu.aggregate(t=Sum('cession_volume_ambiant'))['t'])
    pg_amb = qp_coul_par_produit.get(produit.pk, {}).get('qp_coul', Decimal('0'))
    stock_amb = inv_ac_amb + e_amb + r_amb + a_amb - s_amb - c_amb + pg_amb

    # 15°C — même logique (sans quote-part coulage, comme sur le web)
    e_15 = _D(qs.filter(type_mouvement='ENTREE', regime_douanier='ACQUITTE').aggregate(t=Sum('volume_15c_recu'))['t'])
    s_15 = _D(qs.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_15c_sortie'))['t'])
    c_15 = _D(qs.filter(type_mouvement='CESSION').aggregate(t=Sum('cession_volume_15c'))['t'])
    a_15 = _D(qs.filter(type_mouvement='ACQUITTEMENT').aggregate(t=Sum('acquittement_volume_15c'))['t'])
    r_15 = _D(qs_recu.aggregate(t=Sum('cession_volume_15c'))['t'])
    stock_15 = inv_ac_15 + e_15 + r_15 + a_15 - s_15 - c_15

    # SD / AC (répartition informative par régime douanier)
    qs_sd = qs.filter(regime_douanier='SOUS_DOUANE')
    qs_ac = qs.filter(regime_douanier='ACQUITTE')
    sd_amb = (
        inv_sd_amb
        + _D(qs_sd.filter(type_mouvement='ENTREE').aggregate(t=Sum('volume_ambiant_recu'))['t'])
        - _D(qs_sd.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_ambiant_sortie'))['t'])
        - _D(qs_sd.filter(type_mouvement='CESSION').aggregate(t=Sum('cession_volume_ambiant'))['t'])
        - _D(qs_sd.filter(type_mouvement='ACQUITTEMENT').aggregate(t=Sum('acquittement_volume_ambiant'))['t'])
    )
    ac_amb = (
        inv_ac_amb
        + _D(qs_ac.filter(type_mouvement='ENTREE').aggregate(t=Sum('volume_ambiant_recu'))['t'])
        + _D(qs_ac.filter(type_mouvement='ACQUITTEMENT').aggregate(t=Sum('acquittement_volume_ambiant'))['t'])
        - _D(qs_ac.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_ambiant_sortie'))['t'])
        - _D(qs_ac.filter(type_mouvement='CESSION').aggregate(t=Sum('cession_volume_ambiant'))['t'])
    )
    sd_15 = (
        inv_sd_15
        + _D(qs_sd.filter(type_mouvement='ENTREE').aggregate(t=Sum('volume_15c_recu'))['t'])
        - _D(qs_sd.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_15c_sortie'))['t'])
        - _D(qs_sd.filter(type_mouvement='CESSION').aggregate(t=Sum('cession_volume_15c'))['t'])
        - _D(qs_sd.filter(type_mouvement='ACQUITTEMENT').aggregate(t=Sum('acquittement_volume_15c'))['t'])
    )
    ac_15 = (
        inv_ac_15
        + _D(qs_ac.filter(type_mouvement='ENTREE').aggregate(t=Sum('volume_15c_recu'))['t'])
        + _D(qs_ac.filter(type_mouvement='ACQUITTEMENT').aggregate(t=Sum('acquittement_volume_15c'))['t'])
        - _D(qs_ac.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_15c_sortie'))['t'])
        - _D(qs_ac.filter(type_mouvement='CESSION').aggregate(t=Sum('cession_volume_15c'))['t'])
    )

    return {
        'stock_amb': stock_amb, 'stock_15': stock_15,
        'sd_amb': sd_amb, 'ac_amb': ac_amb, 'sd_15': sd_15, 'ac_15': ac_15,
        'inv_ac_amb': inv_ac_amb, 'inv_sd_amb': inv_sd_amb,
        'e_amb': e_amb, 'r_amb': r_amb,
    }


class DashboardView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsMarketeurActif]

    def get(self, request):
        marketeur = request.user.marketeur

        periode_courante = PeriodeComptable.objects.order_by('-annee', '-mois').first()
        qp_coul_par_produit = _quote_part_coulage(marketeur, periode_courante)

        # ── Stock d'ouverture ACQUITTE de la période en cours ─────
        # (reporté depuis la fermeture du mois précédent)
        ac_ouverture = {}
        if periode_courante:
            for som in StockOuvertureMarketeur.objects.filter(
                periode=periode_courante, marketeur=marketeur, regime_douanier='ACQUITTE',
            ):
                ac_ouverture[som.produit_id] = {'amb': _D(som.volume_ambiant), '15c': _D(som.volume_15c)}

        # ── Inventaires initiaux du marketeur (repli + régime SOUS_DOUANE) ─
        inventaires_agg = {}
        for inv in InventaireInitialMarketeur.objects.filter(marketeur=marketeur):
            pid = inv.produit_id
            if pid not in inventaires_agg:
                inventaires_agg[pid] = {
                    'sd_amb': Decimal('0'), 'sd_15': Decimal('0'),
                    'ac_amb': Decimal('0'), 'ac_15': Decimal('0'),
                }
            if inv.regime_douanier == 'SOUS_DOUANE':
                inventaires_agg[pid]['sd_amb'] += _D(inv.volume_ambiant)
                inventaires_agg[pid]['sd_15']  += _D(inv.volume_15c)
            elif inv.regime_douanier == 'ACQUITTE':
                inventaires_agg[pid]['ac_amb'] += _D(inv.volume_ambiant)
                inventaires_agg[pid]['ac_15']  += _D(inv.volume_15c)

        # ── Stocks par produit ────────────────────────────────
        produits = (
            Produit.objects
            .filter(statut='ACTIF')
            .order_by('nom')
        )

        stocks = []
        for produit in produits:
            calc = _calc_stock_produit(
                marketeur, produit, periode_courante, ac_ouverture,
                inventaires_agg, qp_coul_par_produit,
            )

            # N'inclure que les produits avec stock ou mouvements
            inv_test = calc['inv_ac_amb'] + calc['inv_sd_amb']
            if calc['stock_amb'] == 0 and inv_test == 0 and calc['e_amb'] == 0 and calc['r_amb'] == 0:
                continue

            capacite = _D(
                Cuve.objects.filter(produit=produit, statut='ACTIVE')
                .aggregate(t=Sum('capacite_totale'))['t']
            )

            stocks.append({
                'produit_id':    produit.pk,
                'produit_nom':   produit.nom,
                'produit_sigle': getattr(produit, 'sigle', '') or produit.nom[:4].upper(),
                'stock_ambiant': calc['stock_amb'],
                'stock_15':      calc['stock_15'],
                'sd_ambiant':    calc['sd_amb'],
                'ac_ambiant':    calc['ac_amb'],
                'sd_15':         calc['sd_15'],
                'ac_15':         calc['ac_15'],
                'total':         calc['stock_amb'],
                'capacite':      capacite,
            })

        # ── 10 derniers mouvements ────────────────────────────
        derniers = (
            Mouvement.objects
            .filter(marketeur=marketeur)
            .select_related('produit')
            .order_by('-date_mouvement', '-date_saisie')[:10]
        )

        derniers_data = [
            {
                'id':               m.pk,
                'type':             m.type_mouvement,
                'date':             m.date_mouvement,
                'produit':          m.produit.nom,
                'quantite_ambiant': _volume_amb(m),
                'quantite_15':      _volume_15(m),
                'reference':        getattr(m, 'numero_enregistrement', None),
            }
            for m in derniers
        ]

        total = Mouvement.objects.filter(marketeur=marketeur).count()

        # ── KPI globaux ───────────────────────────────────────
        qs_all = Mouvement.objects.filter(marketeur=marketeur)
        total_entrees = _D(qs_all.filter(type_mouvement='ENTREE').aggregate(t=Sum('volume_ambiant_recu'))['t'])
        total_sorties = _D(qs_all.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_ambiant_sortie'))['t'])
        nb_entrees    = qs_all.filter(type_mouvement='ENTREE').count()
        nb_sorties    = qs_all.filter(type_mouvement='SORTIE').count()

        total_cap_all = sum(float(_D(s.get('capacite') or 0)) for s in stocks)
        total_amb_all = sum(float(_D(s.get('stock_ambiant') or 0)) for s in stocks)
        taux_remplissage = round((total_amb_all / total_cap_all * 100), 1) if total_cap_all > 0 else 0

        # ── Stock d'hier (même formule que le stock actuel, bornée à hier) ─
        hier = date.today() - timedelta(days=1)
        total_ambiant_hier = Decimal('0')
        for produit in produits:
            calc_hier = _calc_stock_produit(
                marketeur, produit, periode_courante, ac_ouverture,
                inventaires_agg, qp_coul_par_produit, upto=hier,
            )
            total_ambiant_hier += calc_hier['stock_amb']

        total_amb_dec = _D(str(total_amb_all))
        if total_ambiant_hier != 0:
            delta_hier = round(float((total_amb_dec - total_ambiant_hier) / abs(total_ambiant_hier) * 100), 1)
        else:
            delta_hier = 0.0

        serializer = DashboardSerializer({
            'marketeur_nom':       marketeur.raison_sociale,
            'stocks':              stocks,
            'derniers_mouvements': derniers_data,
            'total_mouvements':    total,
            'total_entrees':       total_entrees,
            'total_sorties':       total_sorties,
            'nb_entrees':          nb_entrees,
            'nb_sorties':          nb_sorties,
            'taux_remplissage':    taux_remplissage,
            'total_ambiant_hier':  total_ambiant_hier,
            'delta_hier':          delta_hier,
        })
        return Response(serializer.data)
