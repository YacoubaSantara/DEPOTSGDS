"""
Espace Marketeur — vues réservées aux utilisateurs avec rôle MARKETEUR.
Toutes les données sont filtrées sur request.user.marketeur.
"""
from functools import wraps
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.core.paginator import Paginator

from SGDS.users.decorators import voir_required


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


def _uuid_valide(s):
    """True si s est un UUID valide (paramètres GET protégés)."""
    import uuid as _uuid
    try:
        _uuid.UUID(str(s))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


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

    Le volume ambiant est en plus corrigé par la quote-part P/G Installation
    de la période en cours (même quote-part que celle utilisée par l'état
    « Stock de fermeture » — cf. _calculer_stock_ouverture_fermeture_marketeur
    dans views/mensuel.py), afin que les deux écrans restent cohérents.

    Le stock de départ (inv_15c/inv_amb) est le stock d'ouverture ACQUITTE
    de la période en cours (StockOuvertureMarketeur), reporté depuis la
    fermeture du mois précédent — pas un rejeu de tout l'historique des
    mouvements depuis le déploiement. Seuls les mouvements DE LA PÉRIODE EN
    COURS sont ajoutés à ce stock de départ.

    L'inventaire initial SOUS_DOUANE est exclu du stock disponible :
    il sera intégré uniquement lors de l'enregistrement d'un ACQUITTEMENT.
    """
    from SGDS.models import Mouvement, Produit, InventaireInitialMarketeur, PeriodeComptable, StockOuvertureMarketeur

    produits = Produit.objects.filter(statut='ACTIF').select_related('famille').order_by('famille__nom', 'nom')

    periode_courante = PeriodeComptable.objects.order_by('-annee', '-mois').first()

    # Quote-part P/G Installation de la période en cours (même logique que
    # l'état « Stock de fermeture » marketeur) — ambiant uniquement.
    qp_coul_par_produit = {}
    if periode_courante:
        try:
            from SGDS.services.coulage_repartition import calculer_repartition_coulage
            rapport_coul = calculer_repartition_coulage(periode_courante, marketeurs=[marketeur])
            if rapport_coul['lignes']:
                qp_coul_par_produit = rapport_coul['lignes'][0]['par_produit']
        except Exception:
            pass

    # Stock d'ouverture ACQUITTE de la période en cours, reporté depuis la
    # fermeture du mois précédent. Repli sur InventaireInitialMarketeur
    # uniquement si rien n'a encore été résolu (1ère période, ou aucune
    # période comptable encore créée).
    inventaires_agg = {}  # {produit_id: {'volume_15c': Decimal, 'volume_ambiant': Decimal}}
    if periode_courante:
        for som in StockOuvertureMarketeur.objects.filter(
            periode=periode_courante, marketeur=marketeur, regime_douanier='ACQUITTE',
        ):
            inventaires_agg[som.produit_id] = {
                'volume_15c': _D(som.volume_15c), 'volume_ambiant': _D(som.volume_ambiant),
            }
    if not inventaires_agg:
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
        if periode_courante:
            base_qs = base_qs.filter(
                date_mouvement__range=(periode_courante.date_debut, periode_courante.date_fin)
            )

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
        cess_recues_qs = Mouvement.objects.filter(
            cession_marketeur_destinataire=marketeur,
            produit=produit,
            type_mouvement='CESSION',
        )
        if periode_courante:
            cess_recues_qs = cess_recues_qs.filter(
                date_mouvement__range=(periode_courante.date_debut, periode_courante.date_fin)
            )
        cessions_recues = _D(cess_recues_qs.aggregate(t=Sum('cession_volume_15c'))['t'])

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
        cessions_emises_amb = _D(
            base_qs.filter(type_mouvement='CESSION')
            .aggregate(t=Sum('cession_volume_ambiant'))['t']
        )
        cessions_recues_amb = _D(cess_recues_qs.aggregate(t=Sum('cession_volume_ambiant'))['t'])
        pg_inst_amb = qp_coul_par_produit.get(produit.pk, {}).get('qp_coul', Decimal('0'))
        stock_amb = (
            inv_amb + entrees_amb + acquittements_amb - sorties_amb
            - cessions_emises_amb + cessions_recues_amb + pg_inst_amb
        )

        resultats.append({
            'produit':     produit,
            'stock_15c':   stock_15c,
            'stock_amb':   stock_amb,
            'inv_15c':     inv_15c,
            'inv_amb':     inv_amb,
            # Entrées/Sorties affichées au tableau de bord = mouvements directs
            # + cessions (reçues côté entrées, émises côté sorties), pour que
            # les totaux affichés reflètent réellement les flux qui alimentent
            # ou réduisent le stock.
            'entrees':     entrees + cessions_recues,
            'sorties':     sorties + cessions_emises,
            'entrees_amb': entrees_amb + cessions_recues_amb,
            'sorties_amb': sorties_amb + cessions_emises_amb,
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
    total_vol_entree_amb = _D(
        base_qs.filter(type_mouvement='ENTREE')
        .aggregate(t=Sum('volume_ambiant_recu'))['t']
    )
    total_vol_sortie_amb = _D(
        base_qs.filter(type_mouvement='SORTIE')
        .aggregate(t=Sum('volume_ambiant_sortie'))['t']
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
        'total_vol_entree_amb': total_vol_entree_amb,
        'total_vol_sortie_amb': total_vol_sortie_amb,
        'derniers_mouvements':  derniers_mouvements,
        'frais_coulage':        frais_coulage,
    }
    return render(request, 'Espace_Marketeur/dashboard.html', ctx)


# ─────────────────────────────────────────────────────────────
#  VUE 2 : Mes mouvements
# ─────────────────────────────────────────────────────────────

@marketeur_required
@voir_required('voir_mouvement')
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
    if produit_filtre and _uuid_valide(produit_filtre):
        qs = qs.filter(produit__uuid=produit_filtre)
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

    # ── Pagination (?tout=1 : tout afficher, pour impression complète) ──
    if request.GET.get('tout') == '1':
        paginator = Paginator(qs, max(qs.count(), 1))
    else:
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


@marketeur_required
@voir_required('voir_mouvement')
def client_mouvements_pdf(request):
    """Télécharge la liste des mouvements du marketeur en PDF (max 500 lignes)."""
    from django.utils import timezone
    from SGDS.models import Mouvement, Societe
    from SGDS.services.export_pdf import render_to_pdf

    mkt = request.user.marketeur
    societe = Societe.get_instance()
    qs = (
        Mouvement.objects
        .filter(marketeur=mkt)
        .select_related('produit', 'camion', 'chauffeur', 'cession_marketeur_destinataire')
        .order_by('-date_mouvement', '-date_saisie')
    )

    type_filtre    = request.GET.get('type', '').strip()
    produit_filtre = request.GET.get('produit', '').strip()
    regime_filtre  = request.GET.get('regime', '').strip()
    date_debut     = request.GET.get('date_debut', '').strip()
    date_fin       = request.GET.get('date_fin', '').strip()

    if type_filtre:    qs = qs.filter(type_mouvement=type_filtre)
    if produit_filtre and _uuid_valide(produit_filtre): qs = qs.filter(produit__uuid=produit_filtre)
    if regime_filtre:  qs = qs.filter(regime_douanier=regime_filtre)
    if date_debut:     qs = qs.filter(date_mouvement__gte=date_debut)
    if date_fin:       qs = qs.filter(date_mouvement__lte=date_fin)

    nb_total   = qs.count()
    mouvements = list(qs[:500])
    sigle      = mkt.sigle or mkt.raison_sociale
    today      = timezone.now().strftime('%Y%m%d')

    return render_to_pdf(
        'Espace_Marketeur/mouvements_pdf.html',
        {
            'mkt':          mkt,
            'societe':      societe,
            'mouvements':   mouvements,
            'nb_total':     nb_total,
            'generated_at': timezone.now().strftime('%d/%m/%Y à %H:%M'),
            'filtres': {
                'type': type_filtre, 'produit': produit_filtre,
                'regime': regime_filtre, 'date_debut': date_debut, 'date_fin': date_fin,
            },
        },
        filename=f"Mouvements_{sigle}_{today}.pdf",
    )


# ─────────────────────────────────────────────────────────────
#  NOTIFICATIONS
# ─────────────────────────────────────────────────────────────

@marketeur_required
@voir_required('voir_detail_mouvement')
def client_mouvement_detail(request, uuid, slug):
    from SGDS.models import Mouvement, MouvementDocument
    mkt = request.user.marketeur
    mouvement = get_object_or_404(
        Mouvement.objects.select_related(
            'marketeur', 'produit', 'camion', 'camion__marketeur',
            'chauffeur', 'cession_marketeur_destinataire',
            'cession_cuve', 'entree_source',
        ).prefetch_related('lignes__cuve__produit'),
        uuid=uuid,
    )
    if mouvement.marketeur_id != mkt.pk:
        if mouvement.cession_marketeur_destinataire_id != mkt.pk:
            messages.error(request, "Ce mouvement ne vous appartient pas.")
            return redirect('client_mouvements')
    documents = MouvementDocument.objects.filter(mouvement=mouvement).order_by('date_upload')
    return render(request, 'Espace_Marketeur/mouvement_detail.html', {
        'mouvement': mouvement,
        'mkt': mkt,
        'documents': documents,
    })


# ─────────────────────────────────────────────────────────────
#  NOTIFICATIONS
# ─────────────────────────────────────────────────────────────

@marketeur_required
def notif_marquer_lue(request, notif_id):
    from SGDS.models import Notification
    from django.urls import reverse
    mkt = request.user.marketeur
    notif = Notification.objects.filter(pk=notif_id, marketeur=mkt).select_related('mouvement').first()
    if notif:
        notif.lue = True
        notif.save(update_fields=['lue'])
        if notif.mouvement_id:
            return redirect(reverse('mouvement_detail', kwargs={'uuid': str(notif.mouvement.uuid), 'slug': notif.mouvement.slug}))
    return redirect(request.META.get('HTTP_REFERER', 'client_dashboard'))


@marketeur_required
def notif_tout_marquer_lu(request):
    from SGDS.models import Notification
    mkt = request.user.marketeur
    Notification.objects.filter(marketeur=mkt, lue=False).update(lue=True)
    return redirect(request.META.get('HTTP_REFERER', 'client_dashboard'))


# ─────────────────────────────────────────────────────────────
#  PARAMÈTRES — sous-menus : Profil (fiche entreprise) / Sécurité (mot de passe)
# ─────────────────────────────────────────────────────────────

@marketeur_required
def client_parametres_profil(request):
    from SGDS.forms import MarketeurContactForm

    mkt = request.user.marketeur

    if request.method == 'POST':
        form = MarketeurContactForm(request.POST, request.FILES, instance=mkt)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos coordonnées ont été mises à jour.")
            return redirect('client_parametres_profil')
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = MarketeurContactForm(instance=mkt)

    return render(request, 'Espace_Marketeur/parametres/profil.html', {
        'mkt':  mkt,
        'form': form,
    })


@marketeur_required
def client_parametres_securite(request):
    mkt = request.user.marketeur

    if request.method == 'POST':
        ancien   = request.POST.get('ancien_mot_de_passe', '')
        nouveau  = request.POST.get('nouveau_mot_de_passe', '')
        confirme = request.POST.get('confirme_mot_de_passe', '')
        if not request.user.check_password(ancien):
            messages.error(request, "Ancien mot de passe incorrect.")
        elif len(nouveau) < 8:
            messages.error(request, "Le nouveau mot de passe doit faire au moins 8 caractères.")
        elif nouveau != confirme:
            messages.error(request, "Les deux mots de passe ne correspondent pas.")
        else:
            request.user.set_password(nouveau)
            request.user.save(update_fields=['password'])
            messages.success(request, "Mot de passe modifié. Veuillez vous reconnecter.")
            return redirect('connexion')

    return render(request, 'Espace_Marketeur/parametres/securite.html', {
        'mkt': mkt,
    })
