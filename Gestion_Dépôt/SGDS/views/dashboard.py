"""
Tableau de bord administrateur — vue principale après connexion.
Agrège : cuves, stocks, mouvements, jaugeages, alertes, graphes.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import json

_Z = Decimal('0')


def _D(v):
    if v is None:
        return _Z
    return Decimal(str(v)) if not isinstance(v, Decimal) else v


@login_required
def admin_dashboard(request):
    from SGDS.models import (
        Cuve, Produit, Mouvement, JaugeageJour,
        Marketeur, Chauffeur, Camion, PeriodeComptable,
    )

    today = date.today()

    # ── 1. Cuves actives ──────────────────────────────────────
    cuves = list(
        Cuve.objects.filter(statut='ACTIVE')
        .select_related('produit')
        .order_by('produit__nom', 'numero')
    )
    cuves_data = []
    for c in cuves:
        cap  = float(_D(c.capacite_totale))
        niv  = float(_D(c.niveau_actuel))
        pct  = round((niv / cap * 100), 1) if cap > 0 else 0
        if pct <= 10:
            alerte = 'critique'
        elif pct <= 25:
            alerte = 'basse'
        elif pct >= 92:
            alerte = 'pleine'
        else:
            alerte = 'normale'
        cuves_data.append({
            'obj':      c,
            'cap':      cap,
            'niv':      niv,
            'pct':      pct,
            'alerte':   alerte,
            'produit':  c.produit.nom if c.produit else '—',
            'couleur':  c.produit.couleur if (c.produit and hasattr(c.produit, 'couleur')) else None,
        })

    # ── 2. Stocks par produit ────────────────────────────────
    produits = list(Produit.objects.filter(statut='ACTIF').order_by('nom'))

    # ── 3. Période courante ───────────────────────────────────
    periode_courante = (
        PeriodeComptable.objects.filter(statut='OUVERTE')
        .order_by('-annee', '-mois')
        .first()
    )

    # ── 4. Mouvements du mois courant ────────────────────────
    debut_mois = today.replace(day=1)
    mvts_mois  = Mouvement.objects.filter(
        date_mouvement__range=(debut_mois, today)
    )
    nb_entrees_mois = mvts_mois.filter(type_mouvement='ENTREE').count()
    nb_sorties_mois = mvts_mois.filter(type_mouvement='SORTIE').count()
    vol_entrees_mois = float(
        mvts_mois.filter(type_mouvement='ENTREE')
        .aggregate(t=Sum('volume_ambiant_recu'))['t'] or 0
    )
    vol_sorties_mois = float(
        mvts_mois.filter(type_mouvement='SORTIE')
        .aggregate(t=Sum('volume_ambiant_sortie'))['t'] or 0
    )

    # ── 5. Jaugeages récents + non validés ───────────────────
    jaugeages_recents = (
        JaugeageJour.objects
        .select_related('valide_par')
        .order_by('-date_jaugeage', '-heure_jaugeage', '-date_creation')
        [:8]
    )
    nb_jaugeages_attente = JaugeageJour.objects.filter(est_valide=False).count()

    # ── 6. Derniers mouvements ───────────────────────────────
    derniers_mvts = (
        Mouvement.objects
        .select_related('produit', 'marketeur', 'camion')
        .order_by('-date_mouvement', '-date_saisie')
        [:8]
    )

    # ── 7. Compteurs globaux ──────────────────────────────────
    nb_marketeurs  = Marketeur.objects.filter(statut='ACTIF').count()
    nb_chauffeurs  = Chauffeur.objects.filter(statut='ACTIF').count()
    nb_camions     = Camion.objects.filter(statut='EN_SERVICE').count()
    nb_cuves_total = Cuve.objects.filter(statut='ACTIVE').count()
    total_mvts     = Mouvement.objects.count()

    # ── 8. Graphe : Entrées & Sorties 6 derniers mois ────────
    mois_labels = []
    series_entrees = []
    series_sorties = []
    for i in range(5, -1, -1):
        # Calculer le 1er jour du mois i mois en arrière
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        from calendar import monthrange
        debut = date(y, m, 1)
        fin   = date(y, m, monthrange(y, m)[1])
        noms  = ['Jan','Fév','Mar','Avr','Mai','Juin','Juil','Aoû','Sep','Oct','Nov','Déc']
        mois_labels.append(f"{noms[m-1]} {y}")
        e = float(
            Mouvement.objects.filter(
                type_mouvement='ENTREE',
                date_mouvement__range=(debut, fin),
            ).aggregate(t=Sum('volume_ambiant_recu'))['t'] or 0
        )
        s = float(
            Mouvement.objects.filter(
                type_mouvement='SORTIE',
                date_mouvement__range=(debut, fin),
            ).aggregate(t=Sum('volume_ambiant_sortie'))['t'] or 0
        )
        series_entrees.append(round(e / 1000, 2))   # en m³ pour lisibilité
        series_sorties.append(round(s / 1000, 2))

    # ── 9. Graphe : Stock actuel par produit ─────────────────
    chart_produits_labels = [p.nom for p in produits]
    chart_produits_stocks  = [float(_D(p.stock_actuel)) / 1000 for p in produits]

    # ── 10. Alertes ───────────────────────────────────────────
    alertes = []
    for cd in cuves_data:
        if cd['alerte'] == 'critique':
            alertes.append({
                'niveau':  'danger',
                'icone':   '🔴',
                'message': f"Cuve {cd['obj'].numero} ({cd['produit']}) critique : {cd['pct']}% ({cd['niv']:,.0f} L)",
            })
        elif cd['alerte'] == 'basse':
            alertes.append({
                'niveau':  'warning',
                'icone':   '🟡',
                'message': f"Cuve {cd['obj'].numero} ({cd['produit']}) niveau bas : {cd['pct']}%",
            })
        elif cd['alerte'] == 'pleine':
            alertes.append({
                'niveau':  'info',
                'icone':   '🔵',
                'message': f"Cuve {cd['obj'].numero} ({cd['produit']}) quasi pleine : {cd['pct']}%",
            })
    if nb_jaugeages_attente:
        alertes.append({
            'niveau':  'warning',
            'icone':   '⏳',
            'message': f"{nb_jaugeages_attente} jaugeage(s) en attente de validation",
        })
    if not periode_courante:
        alertes.append({
            'niveau':  'danger',
            'icone':   '📅',
            'message': "Aucune période comptable ouverte — créez-en une pour enregistrer des mouvements",
        })

    # JSON pour Chart.js
    chart_mvts_json = json.dumps({
        'labels':   mois_labels,
        'entrees':  series_entrees,
        'sorties':  series_sorties,
    })
    chart_stocks_json = json.dumps({
        'labels': chart_produits_labels,
        'stocks': chart_produits_stocks,
    })

    return render(request, 'dashboard.html', {
        'cuves_data':           cuves_data,
        'produits':             produits,
        'periode_courante':     periode_courante,
        'nb_entrees_mois':      nb_entrees_mois,
        'nb_sorties_mois':      nb_sorties_mois,
        'vol_entrees_mois':     vol_entrees_mois,
        'vol_sorties_mois':     vol_sorties_mois,
        'jaugeages_recents':    jaugeages_recents,
        'nb_jaugeages_attente': nb_jaugeages_attente,
        'derniers_mvts':        derniers_mvts,
        'nb_marketeurs':        nb_marketeurs,
        'nb_chauffeurs':        nb_chauffeurs,
        'nb_camions':           nb_camions,
        'nb_cuves_total':       nb_cuves_total,
        'total_mvts':           total_mvts,
        'alertes':              alertes,
        'chart_mvts_json':      chart_mvts_json,
        'chart_stocks_json':    chart_stocks_json,
        'today':                today,
    })
