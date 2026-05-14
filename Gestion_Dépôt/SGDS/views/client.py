"""
Espace Marketeur — vues réservées aux utilisateurs avec rôle MARKETEUR.
Toutes les données sont filtrées sur request.user.marketeur.
"""
from functools import wraps
from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.core.paginator import Paginator


# ─────────────────────────────────────────────────────────────
#  Décorateur d'accès
# ─────────────────────────────────────────────────────────────

def marketeur_required(view_func):
    """Accès réservé aux utilisateurs avec rôle MARKETEUR liés à un Marketeur."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/auth/connexion/?next={request.path}')
        if not request.user.is_marketeur_role or not request.user.marketeur:
            messages.error(request, "Accès réservé à l'espace marketeur.")
            return redirect('chauffeur_list')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────

def _D(val):
    """Convertit val en Decimal, 0 si None."""
    if val is None:
        return Decimal('0')
    return Decimal(str(val)) if not isinstance(val, Decimal) else val


def _calculer_stock_par_produit(marketeur):
    """
    Calcule le stock @15°C et ambiant par produit pour un marketeur.

    Formule (stock disponible = régime ACQUITTE uniquement) :
      stock = inventaire_initial ACQUITTE
            + Σ ENTREE ACQUITTE(volume_15c_recu)
            + Σ ACQUITTEMENT(acquittement_volume_15c)   ← libère le stock SD
            - Σ SORTIE(volume_15c_sortie)
            - Σ CESSION émise(cession_volume_15c)
            + Σ CESSION reçue(cession_volume_15c)

    L'inventaire initial SOUS_DOUANE est exclu du stock disponible :
    il sera intégré uniquement lors de l'enregistrement d'un ACQUITTEMENT.
    """
    from SGDS.models import Mouvement, Produit, InventaireInitialMarketeur

    produits = Produit.objects.filter(statut='ACTIF').select_related('famille').order_by('famille__nom', 'nom')

    # Charger uniquement les inventaires ACQUITTE — le stock SOUS_DOUANE
    # n'est pas disponible tant que l'acquittement douanier n'est pas enregistré.
    inventaires_agg = {}  # {produit_id: {'volume_15c': Decimal, 'volume_ambiant': Decimal}}
    for inv in InventaireInitialMarketeur.objects.filter(marketeur=marketeur):
        pid = inv.produit_id
        if pid not in inventaires_agg:
            inventaires_agg[pid] = {'volume_15c': Decimal('0'), 'volume_ambiant': Decimal('0')}
        if inv.regime_douanier == 'ACQUITTE':
            inventaires_agg[pid]['volume_15c']    += _D(inv.volume_15c)
            inventaires_agg[pid]['volume_ambiant'] += _D(inv.volume_ambiant)

    resultats = []

    for produit in produits:
        base_qs = Mouvement.objects.filter(marketeur=marketeur, produit=produit)

        # ── Stock inventaire initial (ACQUITTE uniquement) ────────
        inv_data = inventaires_agg.get(produit.pk, {})
        inv_15c  = inv_data.get('volume_15c',    Decimal('0'))
        inv_amb  = inv_data.get('volume_ambiant', Decimal('0'))

        # ── Mouvements ────────────────────────────────────────────
        # Seules les ENTREES en régime ACQUITTE s'ajoutent au stock disponible.
        # Les ENTREES SOUS_DOUANE restent bloquées jusqu'à l'acquittement.
        entrees = _D(
            base_qs.filter(type_mouvement='ENTREE', regime_douanier='ACQUITTE')
            .aggregate(t=Sum('volume_15c_recu'))['t']
        )
        sorties = _D(
            base_qs.filter(type_mouvement='SORTIE')
            .aggregate(t=Sum('volume_15c_sortie'))['t']
        )
        cessions_emises = _D(
            base_qs.filter(type_mouvement='CESSION')
            .aggregate(t=Sum('cession_volume_15c'))['t']
        )
        # L'acquittement libère le stock SOUS_DOUANE → s'AJOUTE au stock disponible.
        acquittements = _D(
            base_qs.filter(type_mouvement='ACQUITTEMENT')
            .aggregate(t=Sum('acquittement_volume_15c'))['t']
        )
        cessions_recues = _D(
            Mouvement.objects.filter(
                cession_marketeur_destinataire=marketeur,
                produit=produit,
                type_mouvement='CESSION',
            ).aggregate(t=Sum('cession_volume_15c'))['t']
        )

        stock_15c = inv_15c + entrees + acquittements - sorties - cessions_emises + cessions_recues

        # Volume ambiant
        entrees_amb = _D(
            base_qs.filter(type_mouvement='ENTREE', regime_douanier='ACQUITTE')
            .aggregate(t=Sum('volume_ambiant_recu'))['t']
        )
        sorties_amb = _D(
            base_qs.filter(type_mouvement='SORTIE')
            .aggregate(t=Sum('volume_ambiant_sortie'))['t']
        )
        acquittements_amb = _D(
            base_qs.filter(type_mouvement='ACQUITTEMENT')
            .aggregate(t=Sum('acquittement_volume_ambiant'))['t']
        )
        stock_amb = inv_amb + entrees_amb + acquittements_amb - sorties_amb

        resultats.append({
            'produit':     produit,
            'stock_15c':   stock_15c,
            'stock_amb':   stock_amb,
            'inv_15c':     inv_15c,
            'inv_amb':     inv_amb,
            'entrees':     entrees,
            'sorties':     sorties,
            'entrees_amb': entrees_amb,
            'sorties_amb': sorties_amb,
        })

    # Garder les produits avec un stock non nul OU un inventaire initial OU des mouvements
    return [r for r in resultats if r['stock_15c'] != 0 or r['entrees'] != 0 or r['inv_15c'] != 0]


# ─────────────────────────────────────────────────────────────
#  VUE 1 : Tableau de bord
# ─────────────────────────────────────────────────────────────

@marketeur_required
def client_dashboard(request):
    from SGDS.models import Mouvement, ClotureCoulageLigne

    mkt = request.user.marketeur

    # ── Stock par produit ─────────────────────────────────────
    stocks = _calculer_stock_par_produit(mkt)

    # ── Statistiques globales ─────────────────────────────────
    base_qs = Mouvement.objects.filter(marketeur=mkt)

    nb_entrees  = base_qs.filter(type_mouvement='ENTREE').count()
    nb_sorties  = base_qs.filter(type_mouvement='SORTIE').count()
    nb_cessions = base_qs.filter(type_mouvement='CESSION').count()

    total_vol_entree_15c = _D(
        base_qs.filter(type_mouvement='ENTREE')
        .aggregate(t=Sum('volume_15c_recu'))['t']
    )
    total_vol_sortie_15c = _D(
        base_qs.filter(type_mouvement='SORTIE')
        .aggregate(t=Sum('volume_15c_sortie'))['t']
    )

    # ── 10 derniers mouvements ────────────────────────────────
    derniers_mouvements = (
        base_qs
        .select_related('produit', 'camion', 'chauffeur')
        .order_by('-date_mouvement', '-date_saisie')[:10]
    )

    # ── Frais de coulage récents ──────────────────────────────
    frais_coulage = (
        ClotureCoulageLigne.objects
        .filter(marketeur=mkt)
        .select_related('cloture__periode', 'produit')
        .order_by('-cloture__periode__annee', '-cloture__periode__mois')[:6]
    )

    ctx = {
        'mkt':                  mkt,
        'stocks':               stocks,
        'nb_entrees':           nb_entrees,
        'nb_sorties':           nb_sorties,
        'nb_cessions':          nb_cessions,
        'total_vol_entree_15c': total_vol_entree_15c,
        'total_vol_sortie_15c': total_vol_sortie_15c,
        'derniers_mouvements':  derniers_mouvements,
        'frais_coulage':        frais_coulage,
    }
    return render(request, 'Espace_Marketeur/dashboard.html', ctx)


# ─────────────────────────────────────────────────────────────
#  VUE 2 : Mes mouvements
# ─────────────────────────────────────────────────────────────

@marketeur_required
def client_mouvements(request):
    from SGDS.models import Mouvement, Produit

    mkt = request.user.marketeur

    qs = (
        Mouvement.objects
        .filter(marketeur=mkt)
        .select_related('produit', 'camion', 'chauffeur',
                        'cession_marketeur_destinataire')
        .order_by('-date_mouvement', '-date_saisie')
    )

    # ── Filtres GET ───────────────────────────────────────────
    type_filtre   = request.GET.get('type', '').strip()
    produit_filtre = request.GET.get('produit', '').strip()
    regime_filtre = request.GET.get('regime', '').strip()
    date_debut    = request.GET.get('date_debut', '').strip()
    date_fin      = request.GET.get('date_fin', '').strip()

    if type_filtre:
        qs = qs.filter(type_mouvement=type_filtre)
    if produit_filtre:
        qs = qs.filter(produit_id=produit_filtre)
    if regime_filtre:
        qs = qs.filter(regime_douanier=regime_filtre)
    if date_debut:
        qs = qs.filter(date_mouvement__gte=date_debut)
    if date_fin:
        qs = qs.filter(date_mouvement__lte=date_fin)

    # ── Totaux sur le QuerySet filtré ─────────────────────────
    totaux = {
        'vol_amb_entree':  _D(qs.filter(type_mouvement='ENTREE').aggregate(t=Sum('volume_ambiant_recu'))['t']),
        'vol_15c_entree':  _D(qs.filter(type_mouvement='ENTREE').aggregate(t=Sum('volume_15c_recu'))['t']),
        'vol_amb_sortie':  _D(qs.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_ambiant_sortie'))['t']),
        'vol_15c_sortie':  _D(qs.filter(type_mouvement='SORTIE').aggregate(t=Sum('volume_15c_sortie'))['t']),
        'vol_cession':     _D(qs.filter(type_mouvement='CESSION').aggregate(t=Sum('cession_volume_15c'))['t']),
    }

    # ── Pagination ────────────────────────────────────────────
    paginator = Paginator(qs, 20)
    page_num  = request.GET.get('page', 1)
    page_obj  = paginator.get_page(page_num)

    # ── Données pour filtres ──────────────────────────────────
    produits = Produit.objects.filter(statut='ACTIF').order_by('nom')

    ctx = {
        'mkt':           mkt,
        'page_obj':      page_obj,
        'produits':      produits,
        'totaux':        totaux,
        'type_filtre':   type_filtre,
        'produit_filtre': produit_filtre,
        'regime_filtre': regime_filtre,
        'date_debut':    date_debut,
        'date_fin':      date_fin,
        'total_count':   qs.count(),
        'TYPE_CHOICES':  Mouvement.TYPE_CHOICES,
        'REGIME_CHOICES': Mouvement.REGIME_CHOICES,
    }
    return render(request, 'Espace_Marketeur/mouvements.html', ctx)
