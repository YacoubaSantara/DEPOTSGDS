"""
Tableau de bord marketeur — API mobile.
GET /api/v1/dashboard/
"""
from decimal import Decimal

from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.v1.permissions import IsMarketeurActif
from SGDS.models import Mouvement, Produit, Cuve, InventaireInitialMarketeur
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


class DashboardView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsMarketeurActif]

    def get(self, request):
        marketeur = request.user.marketeur

        # ── Inventaires initiaux du marketeur ─────────────────
        inventaires_agg = {}
        for inv in InventaireInitialMarketeur.objects.filter(marketeur=marketeur):
            pid = inv.produit_id
            if pid not in inventaires_agg:
                inventaires_agg[pid] = {
                    'amb': Decimal('0'), '15c': Decimal('0'),
                    'sd_amb': Decimal('0'), 'sd_15': Decimal('0'),
                    'ac_amb': Decimal('0'), 'ac_15': Decimal('0'),
                }
            inventaires_agg[pid]['amb'] += _D(inv.volume_ambiant)
            inventaires_agg[pid]['15c'] += _D(inv.volume_15c)
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
            qs  = Mouvement.objects.filter(marketeur=marketeur, produit=produit)
            qs_recu = Mouvement.objects.filter(
                cession_marketeur_destinataire=marketeur,
                produit=produit,
                type_mouvement='CESSION'
            )

            # Inventaire initial pour ce produit
            # Seul le stock ACQUITTE est disponible — le SOUS_DOUANE est bloqué
            # jusqu'à l'enregistrement d'un mouvement ACQUITTEMENT.
            inv_data  = inventaires_agg.get(produit.pk, {})
            inv_sd_amb = inv_data.get('sd_amb', Decimal('0'))
            inv_sd_15  = inv_data.get('sd_15',  Decimal('0'))
            inv_ac_amb = inv_data.get('ac_amb', Decimal('0'))
            inv_ac_15  = inv_data.get('ac_15',  Decimal('0'))

            # Ambiant — base = inventaire ACQUITTE uniquement
            # ENTREE SOUS_DOUANE ignorée ; l'ACQUITTEMENT AJOUTE au stock disponible.
            e_amb = _D(qs.filter(type_mouvement='ENTREE', regime_douanier='ACQUITTE').aggregate(t=Sum('volume_ambiant_recu'))['t'])
            s_amb = _D(qs.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_ambiant_sortie'))['t'])
            c_amb = _D(qs.filter(type_mouvement='CESSION').aggregate(t=Sum('cession_volume_ambiant'))['t'])
            a_amb = _D(qs.filter(type_mouvement='ACQUITTEMENT').aggregate(t=Sum('acquittement_volume_ambiant'))['t'])
            r_amb = _D(qs_recu.aggregate(t=Sum('cession_volume_ambiant'))['t'])
            stock_amb = inv_ac_amb + e_amb + r_amb + a_amb - s_amb - c_amb

            # 15°C — même logique
            e_15 = _D(qs.filter(type_mouvement='ENTREE', regime_douanier='ACQUITTE').aggregate(t=Sum('volume_15c_recu'))['t'])
            s_15 = _D(qs.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_15c_sortie'))['t'])
            c_15 = _D(qs.filter(type_mouvement='CESSION').aggregate(t=Sum('cession_volume_15c'))['t'])
            a_15 = _D(qs.filter(type_mouvement='ACQUITTEMENT').aggregate(t=Sum('acquittement_volume_15c'))['t'])
            r_15 = _D(qs_recu.aggregate(t=Sum('cession_volume_15c'))['t'])
            stock_15 = inv_ac_15 + e_15 + r_15 + a_15 - s_15 - c_15

            # SD / AC (inclut l'inventaire initial par régime)
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

            # N'inclure que les produits avec stock ou mouvements
            inv_amb = inv_ac_amb + inv_sd_amb  # total pour le test de visibilité uniquement
            if stock_amb == 0 and inv_amb == 0 and e_amb == 0 and r_amb == 0:
                continue

            capacite = _D(
                Cuve.objects.filter(produit=produit, statut='ACTIVE')
                .aggregate(t=Sum('capacite_totale'))['t']
            )

            stocks.append({
                'produit_id':    produit.pk,
                'produit_nom':   produit.nom,
                'produit_sigle': getattr(produit, 'sigle', '') or produit.nom[:4].upper(),
                'stock_ambiant': stock_amb,
                'stock_15':      stock_15,
                'sd_ambiant':    sd_amb,
                'ac_ambiant':    ac_amb,
                'sd_15':         sd_15,
                'ac_15':         ac_15,
                'total':         stock_amb,
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

        # ── Stock d'hier (mouvements jusqu'à hier inclus) ─────
        from datetime import date, timedelta
        hier = date.today() - timedelta(days=1)
        qs_hier      = Mouvement.objects.filter(marketeur=marketeur, date_mouvement__lte=hier)
        qs_hier_recu = Mouvement.objects.filter(
            cession_marketeur_destinataire=marketeur,
            type_mouvement='CESSION',
            date_mouvement__lte=hier,
        )
        e_h = _D(qs_hier.filter(type_mouvement='ENTREE').aggregate(t=Sum('volume_ambiant_recu'))['t'])
        s_h = _D(qs_hier.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_ambiant_sortie'))['t'])
        c_h = _D(qs_hier.filter(type_mouvement='CESSION').aggregate(t=Sum('cession_volume_ambiant'))['t'])
        a_h = _D(qs_hier.filter(type_mouvement='ACQUITTEMENT').aggregate(t=Sum('acquittement_volume_ambiant'))['t'])
        r_h = _D(qs_hier_recu.aggregate(t=Sum('cession_volume_ambiant'))['t'])
        inv_total_amb = sum(v.get('amb', Decimal('0')) for v in inventaires_agg.values())
        total_ambiant_hier = inv_total_amb + e_h + r_h - s_h - c_h - a_h

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
