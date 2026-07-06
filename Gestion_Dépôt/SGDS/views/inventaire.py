"""
Vues — Inventaire Initial Marketeur.

Permet de saisir les stocks de départ pour chaque marketeur / produit /
régime douanier avant le premier mouvement. Ces valeurs sont intégrées
automatiquement comme REPORT dans la carte de stock.
"""

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from SGDS.models import InventaireInitialMarketeur, Marketeur, Produit, Cuve
from SGDS.services.depot_scope import depot_scope, depot_requis, get_object_or_404_depot
from SGDS.users.decorators import voir_required


def _d(v):
    return Decimal(str(v)) if v is not None else Decimal('0')


def _totaux_lignes(lignes_list):
    """Totaux SD / AC (ambiant et @15°C) pour une liste de lignes d'inventaire."""
    total_amb_sd = sum(_d(l.volume_ambiant) for l in lignes_list if l.regime_douanier == 'SOUS_DOUANE')
    total_amb_ac = sum(_d(l.volume_ambiant) for l in lignes_list if l.regime_douanier == 'ACQUITTE')
    total_15c_sd = sum(_d(l.volume_15c)     for l in lignes_list if l.regime_douanier == 'SOUS_DOUANE')
    total_15c_ac = sum(_d(l.volume_15c)     for l in lignes_list if l.regime_douanier == 'ACQUITTE')
    return {
        'total_amb_sd': total_amb_sd,
        'total_amb_ac': total_amb_ac,
        'total_amb':    total_amb_sd + total_amb_ac,
        'total_15c_sd': total_15c_sd,
        'total_15c_ac': total_15c_ac,
        'total_15c':    total_15c_sd + total_15c_ac,
    }


# ─────────────────────────────────────────────────────────────
#  LISTE GLOBALE — un résumé par marketeur, cliquable vers le détail
# ─────────────────────────────────────────────────────────────

@voir_required('voir_inventaire')
def inventaire_initial_liste(request):
    """Liste résumée : une ligne par marketeur (totaux + nb de lignes).
    Le clic sur une ligne ouvre le détail du marketeur pour modification."""
    q = request.GET.get('q', '').strip()

    inventaires = depot_scope(request,
        InventaireInitialMarketeur.objects
        .select_related('marketeur', 'produit')
        .order_by('marketeur__raison_sociale', 'produit__nom', 'regime_douanier')
    )
    if q:
        inventaires = inventaires.filter(
            Q(marketeur__raison_sociale__icontains=q) | Q(marketeur__sigle__icontains=q)
        )

    # Regroupement par marketeur + totaux
    from itertools import groupby
    grouped = []
    for mkt, lignes in groupby(inventaires, key=lambda x: x.marketeur):
        lignes_list = list(lignes)
        produits_set = {l.produit_id for l in lignes_list}
        grouped.append({
            'marketeur':   mkt,
            'nb_lignes':   len(lignes_list),
            'nb_produits': len(produits_set),
            **_totaux_lignes(lignes_list),
        })

    paginator = Paginator(grouped, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    marketeurs = Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale')
    produits   = Produit.objects.filter(statut='ACTIF').order_by('nom')
    cuves      = depot_scope(request, Cuve.objects.filter(statut='ACTIVE')).select_related('produit').order_by('numero')

    return render(request, 'inventaire/liste.html', {
        'page_obj':   page_obj,
        'grouped':    page_obj.object_list,
        'q':          q,
        'filtres':    {'q': q},
        'marketeurs': marketeurs,
        'produits':   produits,
        'cuves':      cuves,
    })


# ─────────────────────────────────────────────────────────────
#  DÉTAIL PAR MARKETEUR — lignes complètes + modification
# ─────────────────────────────────────────────────────────────

@voir_required('voir_inventaire')
def inventaire_initial_detail(request, uuid):
    """Détail des stocks initiaux d'un marketeur : toutes les lignes,
    avec modification / suppression / ajout pour ce marketeur."""
    marketeur = get_object_or_404(Marketeur, uuid=uuid)

    lignes = list(depot_scope(request,
        InventaireInitialMarketeur.objects
        .filter(marketeur=marketeur)
        .select_related('marketeur', 'produit', 'saisi_par')
        .prefetch_related('cuves')
        .order_by('produit__nom', 'regime_douanier')
    ))

    produits = Produit.objects.filter(statut='ACTIF').order_by('nom')
    cuves    = depot_scope(request, Cuve.objects.filter(statut='ACTIVE')).select_related('produit').order_by('numero')

    return render(request, 'inventaire/detail.html', {
        'marketeur': marketeur,
        'lignes':    lignes,
        'totaux':    _totaux_lignes(lignes),
        'produits':  produits,
        'cuves':     cuves,
    })


# ─────────────────────────────────────────────────────────────
#  SAISIE (création ou mise à jour)
# ─────────────────────────────────────────────────────────────

@login_required
def inventaire_initial_saisir(request):
    """
    Saisie ou modification d'un stock initial (POST).

    • Sans pk_edit  → création ou mise à jour par (marketeur, produit, régime).
    • Avec pk_edit  → modification directe par PK : seuls volumes, date,
                      notes et cuves sont mis à jour ; les champs clés sont
                      conservés tels quels (ils sont verrouillés côté UI).
    """
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('inventaire_initial_liste')

    if request.method != 'POST':
        return redirect('inventaire_initial_liste')

    if depot_requis(request):
        return redirect('inventaire_initial_liste')

    try:
        # ── Champs communs ────────────────────────────────────
        raw_vamb        = request.POST.get('volume_ambiant', '0').replace(',', '.') or '0'
        raw_v15c        = request.POST.get('volume_15c',     '0').replace(',', '.') or '0'
        date_inventaire = request.POST.get('date_inventaire', '').strip()
        notes           = request.POST.get('notes', '').strip()
        cuves_ids       = request.POST.getlist('cuves')

        volume_ambiant = Decimal(raw_vamb)
        volume_15c     = Decimal(raw_v15c)

        # Les valeurs négatives sont autorisées (solde débiteur / déficit marketeur)

        if not date_inventaire:
            raise ValueError("La date d'inventaire est obligatoire.")

        # ── Mode édition par PK ───────────────────────────────
        pk_edit = request.POST.get('pk_edit', '').strip()
        if pk_edit:
            inv = get_object_or_404_depot(request, InventaireInitialMarketeur, pk=int(pk_edit))
            inv.volume_ambiant  = volume_ambiant
            inv.volume_15c      = volume_15c
            inv.date_inventaire = date_inventaire
            inv.notes           = notes
            inv.saisi_par       = request.user
            inv.save()
            created   = False
            marketeur = inv.marketeur
            produit   = inv.produit

        # ── Mode création / update_or_create ─────────────────
        else:
            marketeur_id = int(request.POST['marketeur'])
            produit_id   = int(request.POST['produit'])
            regime       = request.POST['regime_douanier']

            if regime not in ('SOUS_DOUANE', 'ACQUITTE'):
                raise ValueError("Régime douanier invalide.")

            marketeur = get_object_or_404(Marketeur, pk=marketeur_id)
            produit   = get_object_or_404(Produit,   pk=produit_id)

            inv, created = InventaireInitialMarketeur.objects.update_or_create(
                depot=request.depot,
                marketeur=marketeur,
                produit=produit,
                regime_douanier=regime,
                defaults={
                    'volume_ambiant':  volume_ambiant,
                    'volume_15c':      volume_15c,
                    'date_inventaire': date_inventaire,
                    'notes':           notes,
                    'saisi_par':       request.user,
                }
            )

        # ── Cuves M2M (commun aux deux modes) ────────────────
        if cuves_ids:
            cuves_qs = depot_scope(request, Cuve.objects.filter(pk__in=cuves_ids))
            inv.cuves.set(cuves_qs)
        else:
            inv.cuves.clear()

        action = "créé" if created else "mis à jour"
        messages.success(
            request,
            f"Stock initial de {marketeur} — {produit.code} "
            f"({inv.get_regime_douanier_display()}) {action} avec succès."
        )
        # Retour sur le détail du marketeur concerné
        return redirect('inventaire_initial_detail', uuid=marketeur.uuid)

    except (KeyError, ValueError, Exception) as e:
        messages.error(request, f"Erreur de saisie : {e}")

    return redirect('inventaire_initial_liste')


# ─────────────────────────────────────────────────────────────
#  SUPPRESSION
# ─────────────────────────────────────────────────────────────

@login_required
def inventaire_initial_supprimer(request, uuid):
    """Supprime un stock initial après confirmation (POST)."""
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('inventaire_initial_liste')

    inv = get_object_or_404_depot(request, InventaireInitialMarketeur, uuid=uuid)

    if request.method == 'POST':
        label = str(inv)
        marketeur_uuid = inv.marketeur.uuid
        inv.delete()
        messages.success(request, f"Stock initial supprimé : {label}.")
        return redirect('inventaire_initial_detail', uuid=marketeur_uuid)

    # GET → page de confirmation
    return render(request, 'inventaire/supprimer_confirm.html', {'inv': inv})


# ─────────────────────────────────────────────────────────────
#  SAISIE EN MASSE — tous les marketeurs d'un coup
# ─────────────────────────────────────────────────────────────

@login_required
def inventaire_initial_masse(request):
    """
    Tableau de saisie en masse : toutes les combinaisons
    marketeur × produit × régime douanier sur une seule page.
    Chaque ligne peut être remplie ou laissée vide.
    Un POST enregistre/met à jour toutes les lignes non vides.
    """
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('inventaire_initial_liste')

    if depot_requis(request):
        return redirect('inventaire_initial_liste')

    marketeurs = list(Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale'))
    produits   = list(Produit.objects.filter(statut='ACTIF').order_by('nom'))
    regimes    = [('SOUS_DOUANE', 'Sous douane (SD)'), ('ACQUITTE', 'Acquitté (AC)')]

    # Charger les valeurs existantes dans un dict pour pré-remplissage
    existants = {
        (inv.marketeur_id, inv.produit_id, inv.regime_douanier): inv
        for inv in depot_scope(request, InventaireInitialMarketeur.objects.select_related('marketeur', 'produit'))
    }

    if request.method == 'POST':
        date_inventaire = request.POST.get('date_inventaire_global', '').strip()
        if not date_inventaire:
            messages.error(request, "Veuillez saisir une date d'inventaire.")
            return redirect('inventaire_initial_masse')

        nb_crees = nb_maj = nb_ignores = 0

        for mkt in marketeurs:
            for prod in produits:
                for regime_code, _ in regimes:
                    key_vamb = f"vamb_{mkt.pk}_{prod.pk}_{regime_code}"
                    key_v15c = f"v15c_{mkt.pk}_{prod.pk}_{regime_code}"
                    raw_vamb = request.POST.get(key_vamb, '').strip().replace(',', '.')
                    raw_v15c = request.POST.get(key_v15c, '').strip().replace(',', '.')

                    # Ignorer si les deux champs sont vides
                    if not raw_vamb and not raw_v15c:
                        nb_ignores += 1
                        continue

                    try:
                        v_amb = Decimal(raw_vamb) if raw_vamb else Decimal('0')
                        v_15c = Decimal(raw_v15c) if raw_v15c else Decimal('0')
                        if v_amb < 0 or v_15c < 0:
                            raise ValueError("Valeur négative")
                    except (InvalidOperation, ValueError):
                        messages.warning(
                            request,
                            f"Valeur invalide ignorée : {mkt.raison_sociale} / {prod.code} / {regime_code}"
                        )
                        continue

                    _, created = InventaireInitialMarketeur.objects.update_or_create(
                        depot=request.depot, marketeur=mkt, produit=prod, regime_douanier=regime_code,
                        defaults={
                            'volume_ambiant':  v_amb,
                            'volume_15c':      v_15c,
                            'date_inventaire': date_inventaire,
                            'saisi_par':       request.user,
                        }
                    )
                    if created:
                        nb_crees += 1
                    else:
                        nb_maj += 1

        parts = []
        if nb_crees:  parts.append(f"{nb_crees} créé(s)")
        if nb_maj:    parts.append(f"{nb_maj} mis à jour")
        messages.success(request, f"Inventaire enregistré : {', '.join(parts) or 'aucune modification'}.")
        return redirect('inventaire_initial_liste')

    # Construction de la grille pour le template
    # grille[marketeur] = [ { produit, regime, inv_ou_None }, ... ]
    grille = []
    for mkt in marketeurs:
        lignes = []
        for prod in produits:
            for regime_code, regime_label in regimes:
                inv = existants.get((mkt.pk, prod.pk, regime_code))
                lignes.append({
                    'produit':      prod,
                    'regime_code':  regime_code,
                    'regime_label': regime_label,
                    'key_vamb':     f"vamb_{mkt.pk}_{prod.pk}_{regime_code}",
                    'key_v15c':     f"v15c_{mkt.pk}_{prod.pk}_{regime_code}",
                    'vamb':         inv.volume_ambiant if inv else '',
                    'v15c':         inv.volume_15c     if inv else '',
                    'date':         inv.date_inventaire if inv else '',
                    'existe':       inv is not None,
                })
        grille.append({'marketeur': mkt, 'lignes': lignes})

    from django.utils import timezone
    today = timezone.now().date()

    return render(request, 'inventaire/saisie_masse.html', {
        'grille':    grille,
        'produits':  produits,
        'today':     today,
    })
