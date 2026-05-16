# ── Espace Marketeur ────────────────────────────────────────────
from .client import (  # noqa: F401
    client_dashboard, client_mouvements, client_mouvements_pdf,
    notif_marquer_lue, notif_tout_marquer_lu,
)

# ── États ────────────────────────────────────────────────────────
from .etat import (  # noqa: F401
    carte_stock, carte_stock_admin,
    carte_stock_export, carte_stock_export_admin,
    etat_carte_stock_redirect,
    stock_global_marketeur, stock_global_marketeur_export,
    stock_global_admin, stock_global_admin_export,
)

# ── États mensuels ───────────────────────────────────────────────
from .mensuel import (  # noqa: F401
    etat_stock_ouverture_fermeture, etat_stock_ouverture_fermeture_export,
    etat_stock_fermeture, etat_stock_fermeture_export,
    etat_global_mensuel_depot, etat_global_mensuel_depot_export,
    etat_global_mensuel_rjj, etat_global_mensuel_rjj_export,
    etat_coulage_repartition, etat_coulage_repartition_export,
    etat_coulage_repartition_marketeur, etat_coulage_repartition_marketeur_export,
    etat_stock_mensuel_a, etat_stock_mensuel_a_export,
    etat_stock_mensuel_a_marketeur, etat_stock_mensuel_a_marketeur_export,
    etat_stock_mensuel_b, etat_stock_mensuel_b_export,
    etat_stock_mensuel_b_marketeur, etat_stock_mensuel_b_marketeur_export,
    etat_frais_passage_mensuel, etat_frais_passage_mensuel_export,
    etat_frais_passage_mensuel_marketeur, etat_frais_passage_mensuel_marketeur_export,
)

# ── Société / Dépôt ──────────────────────────────────────────────
from .societe import societe_detail  # noqa: F401

# ── Inventaire initial marketeur ─────────────────────────────────
from .inventaire import (  # noqa: F401
    inventaire_initial_liste,
    inventaire_initial_saisir,
    inventaire_initial_supprimer,
    inventaire_initial_masse,
)

# Periodes comptables
from .periode import ListePeriodesView, OuvrirPeriodeView  # noqa: F401

# Coulage / Suivi / Frais de passage
from .dashboard import admin_dashboard  # noqa: F401
from .coulage import (  # noqa: F401
    ListePeriodesCoulageView,
    RepartitionCoulageView,
    ClotureCoulageView,
    ExportCoulageExcelView,
    SuiviEvolutionView,
    ExportSuiviExcelView,
    FraisPassageView,
    ExportFraisPassageExcelView,
)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import modelformset_factory
from django.views.decorators.http import require_POST
from django.db import IntegrityError
from SGDS.models import Marketeur, Camion, Chauffeur, Famille, Produit, Cuve, ParametreJaugeageCuve, JaugeageJour, MesureCuve, Mouvement, LigneMouvement
from SGDS.forms import (
    MarketeurForm, CamionForm, ChauffeurForm, FamilleForm, ProduitForm, CuveForm,
    ParametreJaugeageCuveForm, JaugeageJourForm, MesureCuveForm, MouvementForm,
    LigneMouvementFormSet,
)
import qrcode
import base64
import io


# ── Helpers ────────────────────────────────────────────────────
def _deny_marketeur(request):
    """Refuse l'accès aux utilisateurs avec rôle MARKETEUR (lecture seule)."""
    if request.user.is_marketeur_role:
        messages.error(request, "Action non autorisée pour votre rôle.")
        return True
    return False


# ─────────────────────────────────────────────────────────────
#  MARKETEUR
# ─────────────────────────────────────────────────────────────

@login_required
def marketeur_list(request):
    if request.user.is_marketeur_role:
        if request.user.marketeur:
            return redirect('marketeur_detail', pk=request.user.marketeur.pk)
        messages.error(request, "Votre compte n'est lié à aucun marketeur.")
        return redirect('connexion')

    qs     = Marketeur.objects.all()
    q      = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '')
    ville  = request.GET.get('ville', '')

    if q:
        qs = qs.filter(
            Q(raison_sociale__icontains=q) | Q(sigle__icontains=q) |
            Q(ville__icontains=q) | Q(email__icontains=q) | Q(telephone__icontains=q)
        )
    if statut:
        qs = qs.filter(statut=statut)
    if ville:
        qs = qs.filter(ville__icontains=ville)

    villes = Marketeur.objects.values_list('ville', flat=True).distinct().order_by('ville')

    ctx = {
        'marketeurs': qs, 'count': qs.count(), 'total': Marketeur.objects.count(),
        'nb_actif': Marketeur.objects.filter(statut='ACTIF').count(),
        'nb_suspendu': Marketeur.objects.filter(statut='SUSPENDU').count(),
        'nb_black': Marketeur.objects.filter(statut='BLACKLIST').count(),
        'villes': villes, 'q': q, 'statut': statut, 'ville': ville,
    }
    return render(request, 'Marketeur/marketeur_list.html', ctx)


@login_required
def marketeur_detail(request, pk):
    mkt = get_object_or_404(Marketeur, pk=pk)
    if request.user.is_marketeur_role:
        if not request.user.marketeur or request.user.marketeur.pk != pk:
            messages.error(request, "Accès refusé.")
            if request.user.marketeur:
                return redirect('marketeur_detail', pk=request.user.marketeur.pk)
            return redirect('connexion')
    return render(request, 'Marketeur/marketeur_detail.html', {'mkt': mkt})


@login_required
def marketeur_create(request):
    if _deny_marketeur(request):
        return redirect('marketeur_list')
    if request.method == 'POST':
        form = MarketeurForm(request.POST, request.FILES)
        if form.is_valid():
            mkt = form.save()
            messages.success(request, f'Marketeur « {mkt.raison_sociale} » créé avec succès.')
            return redirect('marketeur_list')
    else:
        form = MarketeurForm()
    return render(request, 'Marketeur/marketeur_form.html', {'form': form, 'action': 'Nouveau'})


@login_required
def marketeur_update(request, pk):
    if _deny_marketeur(request):
        return redirect('marketeur_detail', pk=pk)
    mkt = get_object_or_404(Marketeur, pk=pk)
    if request.method == 'POST':
        form = MarketeurForm(request.POST, request.FILES, instance=mkt)
        if form.is_valid():
            form.save()
            messages.success(request, f'Marketeur « {mkt.raison_sociale} » modifié avec succès.')
            return redirect('marketeur_detail', pk=pk)
    else:
        form = MarketeurForm(instance=mkt)
    return render(request, 'Marketeur/marketeur_form.html', {'form': form, 'action': 'Modifier', 'mkt': mkt})


@login_required
def marketeur_delete(request, pk):
    if _deny_marketeur(request):
        return redirect('marketeur_detail', pk=pk)
    mkt = get_object_or_404(Marketeur, pk=pk)
    if request.method == 'POST':
        nom = mkt.raison_sociale
        mkt.delete()
        messages.success(request, f'Marketeur « {nom} » supprimé.')
        return redirect('marketeur_list')
    return render(request, 'Marketeur/marketeur_confirm_delete.html', {'mkt': mkt})


# ─────────────────────────────────────────────────────────────
#  CAMION
# ─────────────────────────────────────────────────────────────

@login_required
def camion_list(request):
    qs = Camion.objects.select_related('marketeur').all()
    if request.user.is_marketeur_role and request.user.marketeur:
        qs = qs.filter(marketeur=request.user.marketeur)
    q      = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '')
    type_p = request.GET.get('type_produit', '')
    if q:
        qs = qs.filter(
            Q(immatriculation__icontains=q) | Q(marque__icontains=q) |
            Q(modele__icontains=q) | Q(marketeur__raison_sociale__icontains=q)
        )
    if statut:
        qs = qs.filter(statut=statut)
    if type_p:
        qs = qs.filter(type_produit=type_p)
    ctx = {
        'camions': qs, 'total': Camion.objects.count(),
        'nb_service': Camion.objects.filter(statut='EN_SERVICE').count(),
        'nb_maintenance': Camion.objects.filter(statut='EN_MAINTENANCE').count(),
        'nb_hors_service': Camion.objects.filter(statut='HORS_SERVICE').count(),
        'type_choices': Camion.TYPE_PRODUIT_CHOICES, 'statut_choices': Camion.STATUT_CHOICES,
        'q': q, 'statut': statut, 'type_produit': type_p,
    }
    return render(request, 'Camion/camion_list.html', ctx)


@login_required
def camion_detail(request, pk):
    camion = get_object_or_404(Camion, pk=pk)
    if request.user.is_marketeur_role and request.user.marketeur:
        if camion.marketeur_id != request.user.marketeur.pk:
            messages.error(request, "Accès refusé.")
            return redirect('camion_list')
    return render(request, 'Camion/camion_detail.html', {'camion': camion})


@login_required
def camion_create(request):
    if _deny_marketeur(request):
        return redirect('camion_list')
    if request.method == 'POST':
        form = CamionForm(request.POST, request.FILES)
        if form.is_valid():
            cam = form.save()
            messages.success(request, f'Camion « {cam.immatriculation} » enregistré avec succès.')
            return redirect('camion_list')
    else:
        form = CamionForm()
    return render(request, 'Camion/camion_form.html', {'form': form, 'action': 'Nouveau'})


@login_required
def camion_update(request, pk):
    if _deny_marketeur(request):
        return redirect('camion_detail', pk=pk)
    camion = get_object_or_404(Camion, pk=pk)
    if request.method == 'POST':
        form = CamionForm(request.POST, request.FILES, instance=camion)
        if form.is_valid():
            form.save()
            messages.success(request, f'Camion « {camion.immatriculation} » modifié avec succès.')
            return redirect('camion_detail', pk=pk)
    else:
        form = CamionForm(instance=camion)
    return render(request, 'Camion/camion_form.html', {'form': form, 'action': 'Modifier', 'camion': camion})


@login_required
def camion_delete(request, pk):
    if _deny_marketeur(request):
        return redirect('camion_detail', pk=pk)
    camion = get_object_or_404(Camion, pk=pk)
    if request.method == 'POST':
        immat = camion.immatriculation
        camion.delete()
        messages.success(request, f'Camion « {immat} » supprimé.')
        return redirect('camion_list')
    return render(request, 'Camion/camion_confirm_delete.html', {'camion': camion})


# ─────────────────────────────────────────────────────────────
#  CHAUFFEUR
# ─────────────────────────────────────────────────────────────

@login_required
def chauffeur_list(request):
    qs = Chauffeur.objects.select_related('marketeur', 'camion').all()
    if request.user.is_marketeur_role and request.user.marketeur:
        qs = qs.filter(marketeur=request.user.marketeur)
    q      = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '')
    if q:
        qs = qs.filter(
            Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(telephone__icontains=q) |
            Q(numero_permis__icontains=q) | Q(marketeur__raison_sociale__icontains=q)
        )
    if statut:
        qs = qs.filter(statut=statut)
    ctx = {
        'chauffeurs': qs, 'total': Chauffeur.objects.count(),
        'nb_actif': Chauffeur.objects.filter(statut='ACTIF').count(),
        'nb_inactif': Chauffeur.objects.filter(statut='INACTIF').count(),
        'nb_suspendu': Chauffeur.objects.filter(statut='SUSPENDU').count(),
        'q': q, 'statut': statut,
    }
    return render(request, 'Chauffeur/chauffeur_list.html', ctx)


@login_required
def chauffeur_detail(request, pk):
    chauffeur = get_object_or_404(Chauffeur, pk=pk)
    if request.user.is_marketeur_role and request.user.marketeur:
        if chauffeur.marketeur_id != request.user.marketeur.pk:
            messages.error(request, "Accès refusé.")
            return redirect('chauffeur_list')
    return render(request, 'Chauffeur/chauffeur_detail.html', {'chauffeur': chauffeur})


@login_required
def chauffeur_create(request):
    if _deny_marketeur(request):
        return redirect('chauffeur_list')
    if request.method == 'POST':
        form = ChauffeurForm(request.POST, request.FILES)
        if form.is_valid():
            chf = form.save(commit=False)
            chf.numero_employe = Chauffeur.get_next_numero()
            chf.save()
            messages.success(request, f'Chauffeur « {chf.nom_complet} » enregistré avec succès.')
            return redirect('chauffeur_list')
    else:
        form = ChauffeurForm()
    return render(request, 'Chauffeur/chauffeur_form.html', {'form': form, 'action': 'Nouveau'})


@login_required
def chauffeur_update(request, pk):
    if _deny_marketeur(request):
        return redirect('chauffeur_detail', pk=pk)
    chauffeur = get_object_or_404(Chauffeur, pk=pk)
    if request.method == 'POST':
        form = ChauffeurForm(request.POST, request.FILES, instance=chauffeur)
        if form.is_valid():
            form.save()
            messages.success(request, f'Chauffeur « {chauffeur.nom_complet} » modifié avec succès.')
            return redirect('chauffeur_detail', pk=pk)
    else:
        form = ChauffeurForm(instance=chauffeur)
    return render(request, 'Chauffeur/chauffeur_form.html', {'form': form, 'action': 'Modifier', 'chauffeur': chauffeur})


@login_required
def chauffeur_delete(request, pk):
    if _deny_marketeur(request):
        return redirect('chauffeur_detail', pk=pk)
    chauffeur = get_object_or_404(Chauffeur, pk=pk)
    if request.method == 'POST':
        nom = chauffeur.nom_complet
        chauffeur.delete()
        messages.success(request, f'Chauffeur « {nom} » supprimé.')
        return redirect('chauffeur_list')
    return render(request, 'Chauffeur/chauffeur_confirm_delete.html', {'chauffeur': chauffeur})


@login_required
def chauffeur_badge(request, pk):
    chauffeur = get_object_or_404(Chauffeur.objects.select_related('marketeur', 'camion'), pk=pk)
    if request.user.is_marketeur_role and request.user.marketeur:
        if chauffeur.marketeur_id != request.user.marketeur.pk:
            messages.error(request, "Accès refusé.")
            return redirect('chauffeur_list')
    badge_url = request.build_absolute_uri(f'/chauffeurs/{pk}/')
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(badge_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E3A5F", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    return render(request, 'Chauffeur/chauffeur_badge.html', {'chauffeur': chauffeur, 'qr_b64': qr_b64})


# ─────────────────────────────────────────────────────────────
#  FAMILLE
# ─────────────────────────────────────────────────────────────

@login_required
def famille_list(request):
    qs = Famille.objects.all()
    q = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '')
    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(code__icontains=q) | Q(description__icontains=q))
    if statut:
        qs = qs.filter(statut=statut)
    ctx = {
        'familles': qs, 'total': Famille.objects.count(),
        'nb_actif': Famille.objects.filter(statut='ACTIF').count(),
        'nb_inactif': Famille.objects.filter(statut='INACTIF').count(),
        'q': q, 'statut': statut,
    }
    return render(request, 'Famille/famille_list.html', ctx)


@login_required
def famille_detail(request, pk):
    famille = get_object_or_404(Famille, pk=pk)
    return render(request, 'Famille/famille_detail.html', {'famille': famille, 'produits': famille.produits.all()})


@login_required
def famille_create(request):
    if _deny_marketeur(request):
        return redirect('famille_list')
    if request.method == 'POST':
        form = FamilleForm(request.POST)
        if form.is_valid():
            fam = form.save()
            messages.success(request, f'Famille « {fam.nom} » créée avec succès.')
            return redirect('famille_list')
    else:
        form = FamilleForm()
    return render(request, 'Famille/famille_form.html', {'form': form, 'action': 'Nouvelle'})


@login_required
def famille_update(request, pk):
    if _deny_marketeur(request):
        return redirect('famille_detail', pk=pk)
    famille = get_object_or_404(Famille, pk=pk)
    if request.method == 'POST':
        form = FamilleForm(request.POST, instance=famille)
        if form.is_valid():
            form.save()
            messages.success(request, f'Famille « {famille.nom} » modifiée avec succès.')
            return redirect('famille_detail', pk=pk)
    else:
        form = FamilleForm(instance=famille)
    return render(request, 'Famille/famille_form.html', {'form': form, 'action': 'Modifier', 'famille': famille})


@login_required
def famille_delete(request, pk):
    if _deny_marketeur(request):
        return redirect('famille_detail', pk=pk)
    famille = get_object_or_404(Famille, pk=pk)
    if request.method == 'POST':
        nom = famille.nom
        famille.delete()
        messages.success(request, f'Famille « {nom} » supprimée.')
        return redirect('famille_list')
    return render(request, 'Famille/famille_confirm_delete.html', {'famille': famille})


# ─────────────────────────────────────────────────────────────
#  PRODUIT
# ─────────────────────────────────────────────────────────────

@login_required
def produit_list(request):
    qs = Produit.objects.select_related('famille').all()
    q = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '')
    famille_id = request.GET.get('famille', '')
    if q:
        qs = qs.filter(
            Q(nom__icontains=q) | Q(code__icontains=q) |
            Q(description__icontains=q) | Q(famille__nom__icontains=q)
        )
    if statut:
        qs = qs.filter(statut=statut)
    if famille_id:
        qs = qs.filter(famille_id=famille_id)
    ctx = {
        'produits': qs, 'total': Produit.objects.count(),
        'nb_actif': Produit.objects.filter(statut='ACTIF').count(),
        'nb_inactif': Produit.objects.filter(statut='INACTIF').count(),
        'nb_discontinue': Produit.objects.filter(statut='DISCONTINUE').count(),
        'familles': Famille.objects.filter(statut='ACTIF'),
        'q': q, 'statut': statut, 'famille_id': famille_id,
    }
    return render(request, 'Produit/produit_list.html', ctx)


@login_required
def produit_detail(request, pk):
    produit = get_object_or_404(Produit.objects.select_related('famille'), pk=pk)
    return render(request, 'Produit/produit_detail.html', {'produit': produit, 'cuves': produit.cuves.all()})


@login_required
def produit_create(request):
    if _deny_marketeur(request):
        return redirect('produit_list')
    if request.method == 'POST':
        form = ProduitForm(request.POST)
        if form.is_valid():
            prod = form.save()
            messages.success(request, f'Produit « {prod.nom} » créé avec succès.')
            return redirect('produit_list')
    else:
        form = ProduitForm()
    return render(request, 'Produit/produit_form.html', {'form': form, 'action': 'Nouveau'})


@login_required
def produit_update(request, pk):
    if _deny_marketeur(request):
        return redirect('produit_detail', pk=pk)
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(request, f'Produit « {produit.nom} » modifié avec succès.')
            return redirect('produit_detail', pk=pk)
    else:
        form = ProduitForm(instance=produit)
    return render(request, 'Produit/produit_form.html', {'form': form, 'action': 'Modifier', 'produit': produit})


@login_required
def produit_delete(request, pk):
    if _deny_marketeur(request):
        return redirect('produit_detail', pk=pk)
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        nom = produit.nom
        produit.delete()
        messages.success(request, f'Produit « {nom} » supprimé.')
        return redirect('produit_list')
    return render(request, 'Produit/produit_confirm_delete.html', {'produit': produit})


# ─────────────────────────────────────────────────────────────
#  CUVE
# ─────────────────────────────────────────────────────────────

@login_required
def cuve_list(request):
    qs = Cuve.objects.select_related('produit', 'produit__famille').all()
    q = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '')
    produit_id = request.GET.get('produit', '')
    if q:
        qs = qs.filter(
            Q(numero__icontains=q) | Q(designation__icontains=q) |
            Q(localisation__icontains=q) | Q(produit__nom__icontains=q)
        )
    if statut:
        qs = qs.filter(statut=statut)
    if produit_id:
        qs = qs.filter(produit_id=produit_id)
    ctx = {
        'cuves': qs, 'total': Cuve.objects.count(),
        'nb_active': Cuve.objects.filter(statut='ACTIVE').count(),
        'nb_maintenance': Cuve.objects.filter(statut='EN_MAINTENANCE').count(),
        'nb_hors_service': Cuve.objects.filter(statut='HORS_SERVICE').count(),
        'nb_inactive': Cuve.objects.filter(statut='INACTIVE').count(),
        'produits': Produit.objects.filter(statut='ACTIF'),
        'statut_choices': Cuve.STATUT_CHOICES,
        'q': q, 'statut': statut, 'produit_id': produit_id,
    }
    return render(request, 'Cuve/cuve_list.html', ctx)


@login_required
def cuve_detail(request, pk):
    cuve = get_object_or_404(Cuve.objects.select_related('produit', 'produit__famille'), pk=pk)
    return render(request, 'Cuve/cuve_detail.html', {'cuve': cuve})


@login_required
def cuve_create(request):
    if _deny_marketeur(request):
        return redirect('cuve_list')
    if request.method == 'POST':
        form = CuveForm(request.POST)
        if form.is_valid():
            cuve = form.save()
            messages.success(request, f'Cuve « {cuve.numero} » enregistrée avec succès.')
            return redirect('cuve_list')
    else:
        form = CuveForm()
    return render(request, 'Cuve/cuve_form.html', {'form': form, 'action': 'Nouvelle'})


@login_required
def cuve_update(request, pk):
    if _deny_marketeur(request):
        return redirect('cuve_detail', pk=pk)
    cuve = get_object_or_404(Cuve, pk=pk)
    if request.method == 'POST':
        form = CuveForm(request.POST, instance=cuve)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cuve « {cuve.numero} » modifiée avec succès.')
            return redirect('cuve_detail', pk=pk)
    else:
        form = CuveForm(instance=cuve)
    return render(request, 'Cuve/cuve_form.html', {'form': form, 'action': 'Modifier', 'cuve': cuve})


@login_required
def cuve_delete(request, pk):
    if _deny_marketeur(request):
        return redirect('cuve_detail', pk=pk)
    cuve = get_object_or_404(Cuve, pk=pk)
    if request.method == 'POST':
        num = cuve.numero
        cuve.delete()
        messages.success(request, f'Cuve « {num} » supprimée.')
        return redirect('cuve_list')
    return render(request, 'Cuve/cuve_confirm_delete.html', {'cuve': cuve})


# ─────────────────────────────────────────────────────────────
#  PARAMÈTRES DE JAUGEAGE
# ─────────────────────────────────────────────────────────────

@login_required
def parametre_list(request):
    cuves = Cuve.objects.select_related('parametre_jaugeage').order_by('numero')
    return render(request, 'ParametreJaugeage/parametre_list.html', {
        'cuves': cuves, 'total_cuves': cuves.count(),
        'nb_configures': sum(1 for c in cuves if hasattr(c, 'parametre_jaugeage')),
    })


@login_required
def parametre_detail(request, pk):
    parametre = get_object_or_404(ParametreJaugeageCuve.objects.select_related('cuve'), pk=pk)
    return render(request, 'ParametreJaugeage/parametre_detail.html', {'parametre': parametre})


@login_required
def parametre_create_update(request, cuve_pk):
    if _deny_marketeur(request):
        return redirect('parametre_list')
    cuve = get_object_or_404(Cuve, pk=cuve_pk)
    instance = getattr(cuve, 'parametre_jaugeage', None)
    action = 'Modifier' if instance else 'Configurer'
    if request.method == 'POST':
        form = ParametreJaugeageCuveForm(request.POST, instance=instance)
        if form.is_valid():
            parametre = form.save(commit=False)
            parametre.cuve = cuve
            parametre.save()
            messages.success(request, f'Paramètres de jaugeage de la cuve {cuve.numero} enregistrés.')
            return redirect('parametre_detail', pk=parametre.pk)
    else:
        form = ParametreJaugeageCuveForm(instance=instance)
    return render(request, 'ParametreJaugeage/parametre_form.html', {
        'form': form, 'cuve': cuve, 'action': action, 'instance': instance,
    })


@login_required
def parametre_delete(request, pk):
    if _deny_marketeur(request):
        return redirect('parametre_list')
    parametre = get_object_or_404(ParametreJaugeageCuve.objects.select_related('cuve'), pk=pk)
    if request.method == 'POST':
        num = parametre.cuve.numero
        parametre.delete()
        messages.success(request, f'Paramètres de jaugeage de la cuve {num} supprimés.')
        return redirect('parametre_list')
    return render(request, 'ParametreJaugeage/parametre_confirm_delete.html', {'parametre': parametre})


# ─────────────────────────────────────────────────────────────
#  JAUGEAGE DU JOUR
# ─────────────────────────────────────────────────────────────

@login_required
def jaugeage_list(request):
    qs = JaugeageJour.objects.prefetch_related('mesures__cuve__parametre_jaugeage').all()
    q = request.GET.get('q', '').strip()
    type_j = request.GET.get('type_jaugeage', '')
    date_d = request.GET.get('date_debut', '')
    date_f = request.GET.get('date_fin', '')
    if q:
        qs = qs.filter(Q(operateur__icontains=q) | Q(depot__icontains=q))
    if type_j:
        qs = qs.filter(type_jaugeage=type_j)
    if date_d:
        qs = qs.filter(date_jaugeage__gte=date_d)
    if date_f:
        qs = qs.filter(date_jaugeage__lte=date_f)

    jaugeages_list = list(qs)
    jaugeages_with_totals = []
    for j in jaugeages_list:
        mesures = list(j.mesures.all())
        total = sum(float(m.volume_standard_15c_calcule or 0) for m in mesures)
        total_vad = sum(float(m.volume_ambiant_depot or 0) for m in mesures)
        jaugeages_with_totals.append((j, total if total > 0 else None, total_vad if total_vad > 0 else None))

    from django.db.models import Max
    stocks_produits = Produit.objects.filter(statut='ACTIF').order_by('famille', 'nom')
    date_derniere_maj = stocks_produits.aggregate(Max('date_maj_stock'))['date_maj_stock__max']

    ctx = {
        'jaugeages': jaugeages_list, 'jaugeages_with_totals': jaugeages_with_totals,
        'total': JaugeageJour.objects.count(),
        'nb_avr': JaugeageJour.objects.filter(type_jaugeage='AVR').count(),
        'nb_apr': JaugeageJour.objects.filter(type_jaugeage='APR').count(),
        'nb_j': JaugeageJour.objects.filter(type_jaugeage='J').count(),
        'type_choices': JaugeageJour.TYPE_CHOICES,
        'q': q, 'type_jaugeage': type_j, 'date_debut': date_d, 'date_fin': date_f,
        'stocks_produits': stocks_produits, 'date_derniere_maj': date_derniere_maj,
    }
    return render(request, 'Jaugeage/jaugeage_list.html', ctx)


@login_required
def jaugeage_detail(request, pk):
    jaugeage = get_object_or_404(
        JaugeageJour.objects.prefetch_related('mesures__cuve__parametre_jaugeage'), pk=pk
    )
    mesures = list(jaugeage.mesures.all())
    def _sum(attr):
        vals = [float(getattr(m, attr)) for m in mesures if getattr(m, attr) is not None]
        return sum(vals) if vals else None

    # Écart physique / comptable depuis le jaugeage précédent (générique)
    ecarts_affiches = []
    try:
        from SGDS.services.ecart_jaugeages import (
            calculer_ecart_jaugeages, formatter_ecart_pour_affichage,
        )
        ecarts = calculer_ecart_jaugeages(jaugeage)
        if ecarts:
            ecarts_affiches = formatter_ecart_pour_affichage(ecarts)
    except Exception:
        pass

    return render(request, 'Jaugeage/jaugeage_detail.html', {
        'jaugeage': jaugeage, 'total_vab': _sum('volume_ambiant_bac'),
        'total_vad': _sum('volume_ambiant_depot'), 'total_v15c': _sum('volume_standard_15c'),
        'total_vdispo': _sum('volume_disponible'),
        'ecarts_jaugeages': ecarts_affiches,
    })


@login_required
def jaugeage_create(request):
    if _deny_marketeur(request):
        return redirect('jaugeage_list')
    if request.method == 'POST':
        form = JaugeageJourForm(request.POST)
        if form.is_valid():
            try:
                from datetime import date as _date
                jaugeage = JaugeageJour.creer_nouveau_jaugeage(
                    date_jaugeage=form.cleaned_data['date_jaugeage'],
                    type_jaugeage=form.cleaned_data['type_jaugeage'],
                    heure_jaugeage=form.cleaned_data.get('heure_jaugeage'),
                    operateur=form.cleaned_data.get('operateur'),
                    notes=form.cleaned_data.get('notes'),
                )
                jaugeage.depot               = form.cleaned_data.get('depot') or 'SGDS SANKE'
                jaugeage.type_depot          = form.cleaned_data.get('type_depot') or 'Dépôt de droit'
                jaugeage.temperature_reference = form.cleaned_data.get('temperature_reference') or 15.0
                jaugeage.save()
                messages.success(request, f'Jaugeage du {jaugeage.date_jaugeage} créé. Saisissez les mesures.')
                return redirect('jaugeage_saisie', pk=jaugeage.pk)
            except IntegrityError:
                form.add_error(None, 'Un jaugeage avec cette date, ce type et cette heure existe déjà.')
    else:
        from datetime import date as _date
        form = JaugeageJourForm(initial={
            'date_jaugeage': _date.today(), 'operateur': request.user.nom_complet,
            'depot': 'SGDS SANKE', 'type_depot': 'Dépôt de droit',
        })
    return render(request, 'Jaugeage/jaugeage_form.html', {'form': form, 'action': 'Nouveau'})


@login_required
def jaugeage_update(request, pk):
    if _deny_marketeur(request):
        return redirect('jaugeage_detail', pk=pk)
    jaugeage = get_object_or_404(JaugeageJour, pk=pk)
    if request.method == 'POST':
        form = JaugeageJourForm(request.POST, instance=jaugeage)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Jaugeage modifié avec succès.')
                return redirect('jaugeage_detail', pk=pk)
            except IntegrityError:
                form.add_error(None, 'Un jaugeage avec cette date, ce type et cette heure existe déjà.')
    else:
        form = JaugeageJourForm(instance=jaugeage)
    return render(request, 'Jaugeage/jaugeage_form.html', {'form': form, 'action': 'Modifier', 'jaugeage': jaugeage})


@login_required
def jaugeage_delete(request, pk):
    if _deny_marketeur(request):
        return redirect('jaugeage_detail', pk=pk)
    jaugeage = get_object_or_404(JaugeageJour, pk=pk)
    if request.method == 'POST':
        label = str(jaugeage)
        jaugeage.delete()
        messages.success(request, f'Jaugeage « {label} » supprimé.')
        return redirect('jaugeage_list')
    return render(request, 'Jaugeage/jaugeage_confirm_delete.html', {'jaugeage': jaugeage})


@login_required
def jaugeage_saisie(request, pk):
    if _deny_marketeur(request):
        return redirect('jaugeage_detail', pk=pk)
    jaugeage = get_object_or_404(JaugeageJour, pk=pk)
    MesureCuveFormSet = modelformset_factory(MesureCuve, form=MesureCuveForm, extra=0)
    qs = jaugeage.mesures.select_related(
        'cuve', 'cuve__produit', 'cuve__produit__famille', 'cuve__parametre_jaugeage'
    ).order_by('cuve__numero')

    if request.method == 'POST':
        if jaugeage.est_valide:
            messages.error(request, "Ce jaugeage est validé et ne peut plus être modifié.")
            return redirect('jaugeage_detail', pk=pk)
        formset = MesureCuveFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Mesures enregistrées avec succès.')
            return redirect('jaugeage_saisie', pk=pk)
        else:
            messages.error(request, 'Des erreurs ont été détectées. Vérifiez les valeurs saisies.')
    else:
        formset = MesureCuveFormSet(queryset=qs)

    forms_with_mesures = list(zip(formset.forms, qs))
    from collections import OrderedDict
    pg_dict = OrderedDict()
    for form, mesure in forms_with_mesures:
        produit = mesure.cuve.produit
        key = produit.pk if produit else 0
        if key not in pg_dict:
            pg_dict[key] = {'produit': produit, 'cuves': [], 'count': 0}
        pg_dict[key]['cuves'].append((form, mesure))
        pg_dict[key]['count'] += 1
    product_groups = list(pg_dict.values())
    all_cuves = [(form, mesure) for pg in product_groups for form, mesure in pg['cuves']]
    totaux_groupes = []
    total_depot_val = 0.0
    total_v15c_val = 0.0
    has_any = False
    has_any_v15c = False
    for pg in product_groups:
        t = 0.0
        has_t = False
        t15 = 0.0
        has_t15 = False
        for _, m in pg['cuves']:
            v = m.volume_ambiant_depot
            if v is not None:
                t += float(v)
                has_t = True
                has_any = True
            v15 = m.volume_standard_15c_calcule
            if v15 is not None:
                t15 += float(v15)
                has_t15 = True
                has_any_v15c = True
        pg['total_vad'] = t if has_t else None
        pg['total_v15c'] = t15 if has_t15 else None
        totaux_groupes.append({'produit': pg['produit'], 'total': t if has_t else None, 'total_v15c': t15 if has_t15 else None})
        total_depot_val += t
        total_v15c_val += t15
    return render(request, 'Jaugeage/jaugeage_saisie.html', {
        'jaugeage': jaugeage, 'formset': formset,
        'forms_with_mesures': forms_with_mesures, 'product_groups': product_groups,
        'all_cuves': all_cuves, 'totaux_groupes': totaux_groupes,
        'total_depot': total_depot_val if has_any else None,
        'total_v15c_depot': total_v15c_val if has_any_v15c else None,
        'nb_cuves': len(all_cuves),
    })


@login_required
def valider_jaugeage(request, pk):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Réservé aux responsables dépôt.")
    if request.method != 'POST':
        return redirect('jaugeage_detail', pk=pk)
    jaugeage = get_object_or_404(JaugeageJour, pk=pk)
    if jaugeage.est_valide:
        messages.warning(request, "Ce jaugeage est déjà validé.")
        return redirect('jaugeage_detail', pk=pk)
    mesures_incompletes = []
    for mesure in jaugeage.mesures.select_related('cuve').all():
        champs_requis = [mesure.creux_mesure, mesure.t1, mesure.t2, mesure.t3,
                         mesure.temperature_obs, mesure.densite_moyenne]
        if any(v is None for v in champs_requis):
            mesures_incompletes.append(mesure.cuve.numero)
    if mesures_incompletes:
        messages.error(request, f"Impossible de valider : mesures incomplètes pour {', '.join(mesures_incompletes)}.")
        return redirect('jaugeage_saisie', pk=pk)
    from django.utils import timezone
    jaugeage.est_valide = True
    jaugeage.date_validation = timezone.now()
    jaugeage.valide_par = request.user
    jaugeage.save(update_fields=['est_valide', 'date_validation', 'valide_par'])
    Produit.mettre_a_jour_stocks(jaugeage)
    messages.success(request, f"Jaugeage du {jaugeage.date_jaugeage.strftime('%d/%m/%Y')} validé.")
    return redirect('jaugeage_detail', pk=pk)


@login_required
def devalider_jaugeage(request, pk):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Réservé aux responsables dépôt.")
    if request.method != 'POST':
        return redirect('jaugeage_detail', pk=pk)
    jaugeage = get_object_or_404(JaugeageJour, pk=pk)
    jaugeage.est_valide = False
    jaugeage.date_validation = None
    jaugeage.valide_par = None
    jaugeage.save(update_fields=['est_valide', 'date_validation', 'valide_par'])
    messages.info(request, f"Jaugeage du {jaugeage.date_jaugeage.strftime('%d/%m/%Y')} déverrouillé.")
    return redirect('jaugeage_saisie', pk=pk)


@login_required
def jaugeage_rapport(request, pk):
    jaugeage = get_object_or_404(
        JaugeageJour.objects.prefetch_related(
            'mesures__cuve__parametre_jaugeage', 'mesures__cuve__produit__famille',
        ), pk=pk,
    )
    from collections import OrderedDict
    groups_dict = OrderedDict()
    for m in jaugeage.mesures.select_related(
        'cuve__produit__famille', 'cuve__parametre_jaugeage'
    ).order_by('cuve__numero'):
        produit = m.cuve.produit
        key = produit.pk if produit else 0
        if key not in groups_dict:
            groups_dict[key] = {'produit': produit, 'mesures': []}
        groups_dict[key]['mesures'].append(m)
    product_groups = list(groups_dict.values())
    totaux_groupes = []
    total_depot_vad = 0.0
    total_depot_v15c = 0.0
    has_any_vad = False
    has_any_v15c = False
    for pg in product_groups:
        t_vad = t_v15c = 0.0
        has_vad = has_v15c = False
        for m in pg['mesures']:
            v_vad = m.volume_ambiant_depot
            v_v15c = m.volume_standard_15c_calcule
            if v_vad is not None:
                t_vad += float(v_vad); has_vad = True; has_any_vad = True
            if v_v15c is not None:
                t_v15c += float(v_v15c); has_v15c = True; has_any_v15c = True
        pg['total_vad'] = t_vad if has_vad else None
        pg['total_v15c'] = t_v15c if has_v15c else None
        totaux_groupes.append({
            'produit': pg['produit'],
            'total_vad': t_vad if has_vad else None,
            'total_v15c': t_v15c if has_v15c else None,
        })
        total_depot_vad += t_vad
        total_depot_v15c += t_v15c
    all_mesures = [m for pg in product_groups for m in pg['mesures']]
    return render(request, 'Jaugeage/jaugeage_rapport.html', {
        'jaugeage': jaugeage, 'product_groups': product_groups,
        'all_mesures': all_mesures, 'totaux_groupes': totaux_groupes,
        'total_depot': total_depot_vad if has_any_vad else None,
        'total_v15c': total_depot_v15c if has_any_v15c else None,
        'nb_cuves': len(all_mesures),
    })


@login_required
def parametres_metrologiques(request):
    from SGDS.petroleum_calc import K_SUPER, K_MIDDLE, K_HEAVY, A_AMB, B_AMB
    plages = [
        {'id': 'super', 'label': 'Produits légers', 'categorie': 'Super, essence sans plomb',
         'seuil': 'ρ ≤ 770 kg/m³', 'type': 'standard', 'k0': K_SUPER[0], 'k1': K_SUPER[1],
         'icone_couleur': '#E8760A', 'bg_couleur': '#fff7ed', 'border_couleur': '#fed7aa'},
        {'id': 'ambigue', 'label': 'Zone ambiguë',
         'categorie': 'Algorithme itératif spécial (point fixe)', 'seuil': '770 < ρ < 788 kg/m³',
         'type': 'ambiguous', 'a': A_AMB, 'b': B_AMB,
         'icone_couleur': '#3b82f6', 'bg_couleur': '#eff6ff', 'border_couleur': '#bfdbfe'},
        {'id': 'middle', 'label': 'Produits moyens', 'categorie': 'Gasoil, kérosène, jet-A1',
         'seuil': '788 ≤ ρ < 839 kg/m³', 'type': 'standard', 'k0': K_MIDDLE[0], 'k1': K_MIDDLE[1],
         'icone_couleur': '#16a34a', 'bg_couleur': '#f0fdf4', 'border_couleur': '#bbf7d0'},
        {'id': 'heavy', 'label': 'Produits lourds', 'categorie': 'Fuel-oil, résidus lourds',
         'seuil': 'ρ ≥ 839 kg/m³', 'type': 'standard', 'k0': K_HEAVY[0], 'k1': K_HEAVY[1],
         'icone_couleur': '#64748b', 'bg_couleur': '#f8fafc', 'border_couleur': '#e2e8f0'},
    ]
    norme = {
        'code': 'API MPMS Chapter 11.1 / ASTM D1250', 'date': 'Octobre 1995',
        'titre': 'Generalized Crude Oils, Refined Products and Lubricating Oils',
        'source_historique': r'J:\OPS\TRH_15.XLS / TVCF_15.XLS',
        'statut': "En vigueur dans l'industrie pétrolière de l'Afrique de l'Ouest",
        'iterations': 7,
    }
    return render(request, 'Jaugeage/parametres_metrologiques.html', {'plages': plages, 'norme': norme})


# ─────────────────────────────────────────────────────────────
#  MOUVEMENTS
# ─────────────────────────────────────────────────────────────

@login_required
def mouvement_liste(request):
    from django.core.paginator import Paginator
    qs = Mouvement.objects.select_related('produit', 'marketeur', 'camion').prefetch_related('lignes__cuve', 'acquittements').order_by('-date_mouvement', '-date_saisie')
    type_m = request.GET.get('type', '').strip()
    regime = request.GET.get('regime', '').strip()
    mkt_pk = request.GET.get('marketeur', '').strip()
    produit_pk = request.GET.get('produit', '').strip()
    date_debut = request.GET.get('date_debut', '').strip()
    date_fin = request.GET.get('date_fin', '').strip()
    q = request.GET.get('q', '').strip()
    if type_m:
        qs = qs.filter(type_mouvement=type_m)
    if regime:
        qs = qs.filter(regime_douanier=regime)
    if mkt_pk:
        qs = qs.filter(marketeur_id=mkt_pk)
    if produit_pk:
        qs = qs.filter(produit_id=produit_pk)
    if date_debut:
        qs = qs.filter(date_mouvement__gte=date_debut)
    if date_fin:
        qs = qs.filter(date_mouvement__lte=date_fin)
    if q:
        qs = qs.filter(
            Q(numero_enregistrement__icontains=q) | Q(camion__immatriculation__icontains=q) |
            Q(bl_expediteur__icontains=q) | Q(marketeur__raison_sociale__icontains=q)
        )
    nb_total = qs.count()
    paginator = Paginator(qs, 50)
    mouvements = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'mouvements/liste.html', {
        'mouvements': mouvements, 'nb_total': nb_total,
        'marketeurs': Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale'),
        'produits': Produit.objects.filter(statut='ACTIF').order_by('nom'),
        'filtres': {'type': type_m, 'regime': regime, 'marketeur': mkt_pk, 'produit': produit_pk,
                    'date_debut': date_debut, 'q': q, 'date_fin': date_fin},
        'type_choices': Mouvement.TYPE_CHOICES, 'regime_choices': Mouvement.REGIME_CHOICES,
    })


@login_required
def mouvement_creer(request):
    if _deny_marketeur(request):
        return redirect('mouvement_liste')
    if request.method == 'POST':
        form = MouvementForm(request.POST)
        lignes_formset = LigneMouvementFormSet(request.POST)
        if form.is_valid():
            mouvement = form.save(commit=False)
            mouvement.collaborateur = request.user.get_full_name() or request.user.username
            mouvement.save()
            lignes_formset.instance = mouvement
            if lignes_formset.is_valid():
                for ligne_form in lignes_formset:
                    if ligne_form.cleaned_data and not ligne_form.cleaned_data.get('DELETE'):
                        if ligne_form.cleaned_data.get('cuve') or ligne_form.cleaned_data.get('volume_ambiant'):
                            ligne = ligne_form.save(commit=False)
                            ligne.produit = mouvement.produit
                            ligne.save()
            messages.success(request, f"Mouvement {mouvement.numero_enregistrement} enregistré.")
            return redirect('mouvement_liste')
    else:
        form = MouvementForm()
        lignes_formset = LigneMouvementFormSet()
    camions = Camion.objects.select_related('marketeur').filter(statut='EN_SERVICE').order_by('immatriculation')
    cuves = Cuve.objects.select_related('produit').filter(statut='ACTIVE').order_by('numero')
    marketeurs = Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale')
    return render(request, 'mouvements/saisie.html', {
        'form': form, 'lignes_formset': lignes_formset, 'titre': 'Nouveau mouvement',
        'camions': camions, 'cuves': cuves, 'marketeurs': marketeurs, 'mode': 'creer',
    })


@login_required
def mouvement_modifier(request, pk):
    if _deny_marketeur(request):
        return redirect('mouvement_liste')
    mouvement = get_object_or_404(Mouvement, pk=pk)
    if request.method == 'POST':
        form = MouvementForm(request.POST, instance=mouvement)
        lignes_formset = LigneMouvementFormSet(request.POST, instance=mouvement)
        if form.is_valid() and lignes_formset.is_valid():
            mouvement = form.save()
            for ligne_form in lignes_formset:
                if ligne_form.cleaned_data:
                    if ligne_form.cleaned_data.get('DELETE'):
                        if ligne_form.instance.pk:
                            ligne_form.instance.delete()
                    elif ligne_form.cleaned_data.get('cuve') or ligne_form.cleaned_data.get('volume_ambiant'):
                        ligne = ligne_form.save(commit=False)
                        ligne.produit = mouvement.produit
                        ligne.save()
            # Synchroniser le produit dénormalisé sur toutes les lignes restantes
            LigneMouvement.objects.filter(mouvement=mouvement).update(produit=mouvement.produit)
            messages.success(request, f"Mouvement N° {mouvement.numero_enregistrement} modifié.")
            return redirect('mouvement_detail', pk=mouvement.pk)
    else:
        form = MouvementForm(instance=mouvement)
        lignes_formset = LigneMouvementFormSet(instance=mouvement)
    camions = Camion.objects.select_related('marketeur').filter(statut='EN_SERVICE').order_by('immatriculation')
    cuves = Cuve.objects.select_related('produit').filter(statut='ACTIVE').order_by('numero')
    marketeurs = Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale')
    return render(request, 'mouvements/saisie.html', {
        'form': form, 'lignes_formset': lignes_formset, 'mouvement': mouvement,
        'titre': f'Modifier — {mouvement.numero_enregistrement}',
        'camions': camions, 'cuves': cuves, 'marketeurs': marketeurs, 'mode': 'modification',
    })


@login_required
def mouvement_detail(request, pk):
    mouvement = get_object_or_404(
        Mouvement.objects.select_related(
            'marketeur', 'produit', 'camion', 'camion__marketeur',
            'chauffeur', 'cession_marketeur_destinataire',
        ).prefetch_related('lignes__cuve__produit'), pk=pk
    )
    return render(request, 'mouvements/detail.html', {'mouvement': mouvement})


@login_required
def mouvement_supprimer(request, pk):
    if not request.user.is_staff:
        messages.error(request, "La suppression de mouvements est réservée au staff.")
        return redirect('mouvement_liste')
    mouvement = get_object_or_404(Mouvement, pk=pk)
    if request.method == 'POST':
        mouvement.delete()
        messages.success(request, "Mouvement supprimé.")
        return redirect('mouvement_liste')
    return render(request, 'mouvements/confirmer_suppression.html', {'mouvement': mouvement})


# ─────────────────────────────────────────────────────────────
#  EXPORT PDF — MOUVEMENTS
# ─────────────────────────────────────────────────────────────

@login_required
def mouvement_detail_pdf(request, pk):
    """Télécharge la fiche détaillée d'un mouvement en PDF."""
    from django.utils import timezone
    from SGDS.services.export_pdf import render_to_pdf

    mouvement = get_object_or_404(
        Mouvement.objects.select_related(
            'marketeur', 'produit', 'camion', 'camion__marketeur',
            'chauffeur', 'cession_marketeur_destinataire',
        ).prefetch_related('lignes__cuve__produit'),
        pk=pk,
    )
    filename = f"MVT_{mouvement.numero_enregistrement}.pdf"
    return render_to_pdf(
        'mouvements/detail_pdf.html',
        {
            'mouvement':    mouvement,
            'generated_at': timezone.now().strftime('%d/%m/%Y à %H:%M'),
        },
        filename=filename,
    )


@login_required
def mouvements_liste_pdf(request):
    """Télécharge la liste filtrée des mouvements en PDF (max 500 lignes)."""
    from django.utils import timezone
    from SGDS.services.export_pdf import render_to_pdf

    qs = Mouvement.objects.select_related(
        'produit', 'marketeur', 'camion', 'cession_marketeur_destinataire',
    ).order_by('-date_mouvement', '-date_saisie')

    type_m     = request.GET.get('type', '').strip()
    regime     = request.GET.get('regime', '').strip()
    mkt_pk     = request.GET.get('marketeur', '').strip()
    produit_pk = request.GET.get('produit', '').strip()
    date_debut = request.GET.get('date_debut', '').strip()
    date_fin   = request.GET.get('date_fin', '').strip()
    q          = request.GET.get('q', '').strip()

    if type_m:      qs = qs.filter(type_mouvement=type_m)
    if regime:      qs = qs.filter(regime_douanier=regime)
    if mkt_pk:      qs = qs.filter(marketeur_id=mkt_pk)
    if produit_pk:  qs = qs.filter(produit_id=produit_pk)
    if date_debut:  qs = qs.filter(date_mouvement__gte=date_debut)
    if date_fin:    qs = qs.filter(date_mouvement__lte=date_fin)
    if q:
        qs = qs.filter(
            Q(numero_enregistrement__icontains=q) |
            Q(camion__immatriculation__icontains=q) |
            Q(bl_expediteur__icontains=q) |
            Q(marketeur__raison_sociale__icontains=q)
        )

    nb_total   = qs.count()
    mouvements = list(qs[:500])
    today      = timezone.now().strftime('%Y%m%d')

    return render_to_pdf(
        'mouvements/liste_pdf.html',
        {
            'mouvements':   mouvements,
            'nb_total':     nb_total,
            'generated_at': timezone.now().strftime('%d/%m/%Y à %H:%M'),
            'filtres': {
                'type': type_m, 'regime': regime, 'marketeur': mkt_pk,
                'produit': produit_pk, 'date_debut': date_debut,
                'date_fin': date_fin, 'q': q,
            },
        },
        filename=f"Mouvements_{today}.pdf",
    )


@login_required
@require_POST
def mouvement_calcul_preview(request):
    import json
    from SGDS import petroleum_calc as pc
    try:
        data = json.loads(request.body)
    except (ValueError, KeyError):
        return JsonResponse({'error': 'JSON invalide'}, status=400)

    def _f(key):
        v = data.get(key)
        try:
            return float(v) if v not in (None, '', 'null') else None
        except (ValueError, TypeError):
            return None

    result = {}
    type_mvt = data.get('type_mouvement', '')

    if type_mvt == 'ENTREE':
        v_amb_recu   = _f('volume_ambiant_recu')
        v_amb_expe   = _f('volume_ambiant_expediteur')
        temp_labo    = _f('temperature_labo')
        dens_obs     = _f('densite_observee_labo')
        temp_recept  = _f('temperature_reception')
        dens_expe    = _f('densite_15c_expediteur')

        if v_amb_recu is not None and v_amb_expe is not None:
            result['perte_gain_reception'] = round(v_amb_recu - v_amb_expe, 2)

        d15 = None
        if dens_obs is not None and temp_labo is not None:
            try:
                d15 = round(pc.density_at_15c(dens_obs, temp_labo), 2)
                result['densite_15c_calculee'] = d15
            except Exception:
                pass

        if d15 is not None and dens_expe is not None:
            result['ecart_densite_15c'] = round((d15 - dens_expe) / 1000, 4)

        vcf = None
        if d15 is not None and temp_recept is not None:
            try:
                vcf = round(pc.vcf_to_15c(d15, temp_recept), 4)
                result['coefficient_conversion_15c'] = vcf
            except Exception:
                pass

        if v_amb_recu is not None and vcf is not None:
            result['volume_15c_recu'] = round(v_amb_recu * vcf, 2)

        pg_recept = result.get('perte_gain_reception')
        if pg_recept is not None and vcf is not None:
            result['perte_gain_15c'] = round(pg_recept * vcf, 2)

        v15 = result.get('volume_15c_recu')
        if v15 is not None and d15 is not None:
            result['poids_kg'] = round(v15 * d15 / 1000, 2)

    elif type_mvt == 'SORTIE':
        v_amb_sortie   = _f('volume_ambiant_sortie')
        dens_15_sortie = _f('densite_15c_sortie')
        temp_sortie    = _f('temperature_sortie')

        vcf = None
        if dens_15_sortie is not None and temp_sortie is not None:
            try:
                vcf = round(pc.vcf_to_15c(dens_15_sortie, temp_sortie), 4)
                result['coefficient_conversion_sortie'] = vcf
            except Exception:
                pass

        if v_amb_sortie is not None and vcf is not None:
            result['volume_15c_sortie'] = round(v_amb_sortie * vcf, 2)
            if dens_15_sortie is not None:
                result['poids_sortie_kg'] = round(result['volume_15c_sortie'] * dens_15_sortie / 1000, 2)

    return JsonResponse(result)


