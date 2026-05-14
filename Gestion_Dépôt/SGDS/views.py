from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import modelformset_factory
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Marketeur, Camion, Chauffeur, Famille, Produit, Cuve, ParametreJaugeageCuve, JaugeageJour, MesureCuve, Mouvement, LigneMouvement
from .forms import (
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
    # Un marketeur est redirigé vers son propre profil
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
            Q(raison_sociale__icontains=q) |
            Q(sigle__icontains=q) |
            Q(ville__icontains=q) |
            Q(email__icontains=q) |
            Q(telephone__icontains=q)
        )
    if statut:
        qs = qs.filter(statut=statut)
    if ville:
        qs = qs.filter(ville__icontains=ville)

    villes = Marketeur.objects.values_list('ville', flat=True).distinct().order_by('ville')

    ctx = {
        'marketeurs': qs,
        'count':      qs.count(),
        'total':      Marketeur.objects.count(),
        'nb_actif':   Marketeur.objects.filter(statut='ACTIF').count(),
        'nb_suspendu':Marketeur.objects.filter(statut='SUSPENDU').count(),
        'nb_black':   Marketeur.objects.filter(statut='BLACKLIST').count(),
        'villes':     villes,
        'q':          q,
        'statut':     statut,
        'ville':      ville,
    }
    return render(request, 'Marketeur/marketeur_list.html', ctx)


@login_required
def marketeur_detail(request, pk):
    mkt = get_object_or_404(Marketeur, pk=pk)
    # Un marketeur ne peut voir que son propre profil
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

    # Filtrer par marketeur si rôle MARKETEUR
    if request.user.is_marketeur_role and request.user.marketeur:
        qs = qs.filter(marketeur=request.user.marketeur)

    q      = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '')
    type_p = request.GET.get('type_produit', '')

    if q:
        qs = qs.filter(
            Q(immatriculation__icontains=q) |
            Q(marque__icontains=q) |
            Q(modele__icontains=q) |
            Q(marketeur__raison_sociale__icontains=q)
        )
    if statut:
        qs = qs.filter(statut=statut)
    if type_p:
        qs = qs.filter(type_produit=type_p)

    ctx = {
        'camions':          qs,
        'total':            Camion.objects.count(),
        'nb_service':       Camion.objects.filter(statut='EN_SERVICE').count(),
        'nb_maintenance':   Camion.objects.filter(statut='EN_MAINTENANCE').count(),
        'nb_hors_service':  Camion.objects.filter(statut='HORS_SERVICE').count(),
        'type_choices':     Camion.TYPE_PRODUIT_CHOICES,
        'statut_choices':   Camion.STATUT_CHOICES,
        'q':        q,
        'statut':   statut,
        'type_produit': type_p,
    }
    return render(request, 'Camion/camion_list.html', ctx)


@login_required
def camion_detail(request, pk):
    camion = get_object_or_404(Camion, pk=pk)
    # Vérification accès marketeur
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

    # Filtrer par marketeur si rôle MARKETEUR
    if request.user.is_marketeur_role and request.user.marketeur:
        qs = qs.filter(marketeur=request.user.marketeur)

    q      = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '')

    if q:
        qs = qs.filter(
            Q(nom__icontains=q) |
            Q(prenom__icontains=q) |
            Q(telephone__icontains=q) |
            Q(numero_permis__icontains=q) |
            Q(marketeur__raison_sociale__icontains=q)
        )
    if statut:
        qs = qs.filter(statut=statut)

    ctx = {
        'chauffeurs':    qs,
        'total':         Chauffeur.objects.count(),
        'nb_actif':      Chauffeur.objects.filter(statut='ACTIF').count(),
        'nb_inactif':    Chauffeur.objects.filter(statut='INACTIF').count(),
        'nb_suspendu':   Chauffeur.objects.filter(statut='SUSPENDU').count(),
        'q':      q,
        'statut': statut,
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
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(badge_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E3A5F", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return render(request, 'Chauffeur/chauffeur_badge.html', {
        'chauffeur': chauffeur,
        'qr_b64': qr_b64,
    })


# ─────────────────────────────────────────────────────────────
#  FAMILLE
# ─────────────────────────────────────────────────────────────

@login_required
def famille_list(request):
    qs = Famille.objects.all()
    q      = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '')

    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(code__icontains=q) | Q(description__icontains=q))
    if statut:
        qs = qs.filter(statut=statut)

    ctx = {
        'familles':  qs,
        'total':     Famille.objects.count(),
        'nb_actif':  Famille.objects.filter(statut='ACTIF').count(),
        'nb_inactif':Famille.objects.filter(statut='INACTIF').count(),
        'q':     q,
        'statut':statut,
    }
    return render(request, 'Famille/famille_list.html', ctx)


@login_required
def famille_detail(request, pk):
    famille = get_object_or_404(Famille, pk=pk)
    produits = famille.produits.all()
    return render(request, 'Famille/famille_detail.html', {'famille': famille, 'produits': produits})


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
    q          = request.GET.get('q', '').strip()
    statut     = request.GET.get('statut', '')
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
        'produits':      qs,
        'total':         Produit.objects.count(),
        'nb_actif':      Produit.objects.filter(statut='ACTIF').count(),
        'nb_inactif':    Produit.objects.filter(statut='INACTIF').count(),
        'nb_discontinue':Produit.objects.filter(statut='DISCONTINUE').count(),
        'familles':      Famille.objects.filter(statut='ACTIF'),
        'q':         q,
        'statut':    statut,
        'famille_id':famille_id,
    }
    return render(request, 'Produit/produit_list.html', ctx)


@login_required
def produit_detail(request, pk):
    produit = get_object_or_404(Produit.objects.select_related('famille'), pk=pk)
    cuves = produit.cuves.all()
    return render(request, 'Produit/produit_detail.html', {'produit': produit, 'cuves': cuves})


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
    q          = request.GET.get('q', '').strip()
    statut     = request.GET.get('statut', '')
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
        'cuves':           qs,
        'total':           Cuve.objects.count(),
        'nb_active':       Cuve.objects.filter(statut='ACTIVE').count(),
        'nb_maintenance':  Cuve.objects.filter(statut='EN_MAINTENANCE').count(),
        'nb_hors_service': Cuve.objects.filter(statut='HORS_SERVICE').count(),
        'nb_inactive':     Cuve.objects.filter(statut='INACTIVE').count(),
        'produits':        Produit.objects.filter(statut='ACTIF'),
        'statut_choices':  Cuve.STATUT_CHOICES,
        'q':          q,
        'statut':     statut,
        'produit_id': produit_id,
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
        'cuves':         cuves,
        'total_cuves':   cuves.count(),
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
    qs = JaugeageJour.objects.prefetch_related(
        'mesures__cuve__parametre_jaugeage'
    ).all()
    q      = request.GET.get('q', '').strip()
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

    # Calcul du volume total @15°C par jaugeage (propriétés Python, non annotables SQL)
    # On passe une liste de tuples (jaugeage, total_ou_None) pour un accès simple en template
    jaugeages_list = list(qs)
    jaugeages_with_totals = []
    for j in jaugeages_list:
        mesures = list(j.mesures.all())
        total = sum(float(m.volume_standard_15c_calcule or 0) for m in mesures)
        total_vad = sum(float(m.volume_ambiant_depot or 0) for m in mesures)
        jaugeages_with_totals.append((j, total if total > 0 else None, total_vad if total_vad > 0 else None))

    # Stocks produits pour le bandeau récapitulatif
    from django.db.models import Max
    stocks_produits = Produit.objects.filter(statut='ACTIF').order_by('famille', 'nom')
    date_derniere_maj = stocks_produits.aggregate(Max('date_maj_stock'))['date_maj_stock__max']

    ctx = {
        'jaugeages':              jaugeages_list,
        'jaugeages_with_totals':  jaugeages_with_totals,
        'total':          JaugeageJour.objects.count(),
        'nb_avr':         JaugeageJour.objects.filter(type_jaugeage='AVR').count(),
        'nb_apr':         JaugeageJour.objects.filter(type_jaugeage='APR').count(),
        'nb_j':           JaugeageJour.objects.filter(type_jaugeage='J').count(),
        'type_choices':   JaugeageJour.TYPE_CHOICES,
        'q':              q,
        'type_jaugeage':  type_j,
        'date_debut':     date_d,
        'date_fin':       date_f,
        'stocks_produits':    stocks_produits,
        'date_derniere_maj':  date_derniere_maj,
    }
    return render(request, 'Jaugeage/jaugeage_list.html', ctx)


@login_required
def jaugeage_detail(request, pk):
    jaugeage = get_object_or_404(
        JaugeageJour.objects.prefetch_related('mesures__cuve__parametre_jaugeage'),
        pk=pk
    )
    # ── Totaux volumes pour le tfoot ─────────────────────────────
    mesures = list(jaugeage.mesures.all())
    def _sum(attr):
        vals = [float(getattr(m, attr)) for m in mesures if getattr(m, attr) is not None]
        return sum(vals) if vals else None

    return render(request, 'Jaugeage/jaugeage_detail.html', {
        'jaugeage':     jaugeage,
        'total_vab':    _sum('volume_ambiant_bac'),
        'total_vad':    _sum('volume_ambiant_depot'),
        'total_v15c':   _sum('volume_standard_15c'),
        'total_vdispo': _sum('volume_disponible'),
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
            'date_jaugeage': _date.today(),
            'operateur':     request.user.nom_complet,
            'depot':         'SGDS SANKE',
            'type_depot':    'Dépôt de droit',
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
        # Recalcul explicite après suppression (ceinture + bretelles en plus du signal)
        from .services.recalcul_stock import recalculer_tous_stocks
        recalculer_tous_stocks()
        messages.success(request, f'Jaugeage « {label} » supprimé. Stocks recalculés.')
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
        # Refus de modification si le jaugeage est validé
        if jaugeage.est_valide:
            messages.error(
                request,
                "Ce jaugeage est validé et ne peut plus être modifié. "
                "Demandez au chef de dépôt de le déverrouiller."
            )
            return redirect('jaugeage_detail', pk=pk)
        formset = MesureCuveFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Mesures enregistrées avec succès.')
            return redirect('jaugeage_saisie', pk=pk)   # rester sur la saisie pour voir les calculs
        else:
            messages.error(request, 'Des erreurs ont été détectées. Vérifiez les valeurs saisies.')
    else:
        formset = MesureCuveFormSet(queryset=qs)

    # Associer chaque form à sa mesure
    forms_with_mesures = list(zip(formset.forms, qs))

    # ── Grouper par produit pour le layout colonne-par-cuve ──────
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

    # Liste plate dans le même ordre (pour forloop.counter0 global en template)
    all_cuves = [(form, mesure) for pg in product_groups for form, mesure in pg['cuves']]

    # ── Totaux volumes ambiant dépôt (calculés après le dernier save) ────
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
        'jaugeage':          jaugeage,
        'formset':           formset,
        'forms_with_mesures': forms_with_mesures,
        'product_groups':    product_groups,
        'all_cuves':         all_cuves,
        'totaux_groupes':    totaux_groupes,
        'total_depot':       total_depot_val if has_any else None,
        'total_v15c_depot':  total_v15c_val if has_any_v15c else None,
        'nb_cuves':          len(all_cuves),
    })


# ─────────────────────────────────────────────────────────────
#  VALIDATION / DÉVALIDATION D'UN JAUGEAGE
# ─────────────────────────────────────────────────────────────

@login_required
def valider_jaugeage(request, pk):
    """Valide un jaugeage (POST, staff uniquement)."""
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Réservé aux responsables dépôt.")
    if request.method != 'POST':
        return redirect('jaugeage_detail', pk=pk)

    jaugeage = get_object_or_404(JaugeageJour, pk=pk)

    if jaugeage.est_valide:
        messages.warning(request, "Ce jaugeage est déjà validé.")
        return redirect('jaugeage_detail', pk=pk)

    # Vérifier que toutes les mesures sont complètes
    mesures_incompletes = []
    for mesure in jaugeage.mesures.select_related('cuve').all():
        champs_requis = [
            mesure.creux_mesure, mesure.v_a_saisi,
            mesure.t1, mesure.t2, mesure.t3,
            mesure.temperature_obs, mesure.densite_moyenne,
        ]
        if any(v is None for v in champs_requis):
            mesures_incompletes.append(mesure.cuve.numero)

    if mesures_incompletes:
        cuves_str = ', '.join(mesures_incompletes)
        messages.error(
            request,
            f"Impossible de valider : les mesures des cuves {cuves_str} sont incomplètes."
        )
        return redirect('jaugeage_saisie', pk=pk)

    from django.utils import timezone
    jaugeage.est_valide = True
    jaugeage.date_validation = timezone.now()
    jaugeage.valide_par = request.user
    jaugeage.save(update_fields=['est_valide', 'date_validation', 'valide_par'])

    # Mise à jour automatique des stocks produits
    Produit.mettre_a_jour_stocks(jaugeage)

    messages.success(
        request,
        f"Jaugeage du {jaugeage.date_jaugeage.strftime('%d/%m/%Y')} validé avec succès."
    )
    return redirect('jaugeage_detail', pk=pk)


@login_required
def devalider_jaugeage(request, pk):
    """Déverrouille un jaugeage validé (POST, staff uniquement)."""
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

    # Recalcul des stocks : reprend le jaugeage précédent s'il existe
    from .services.recalcul_stock import recalculer_tous_stocks
    recalculer_tous_stocks()

    messages.info(
        request,
        f"Jaugeage du {jaugeage.date_jaugeage.strftime('%d/%m/%Y')} déverrouillé. Stocks recalculés."
    )
    return redirect('jaugeage_saisie', pk=pk)


# ─────────────────────────────────────────────────────────────
#  RAPPORT D'IMPRESSION — Vue A4 du jaugeage
# ─────────────────────────────────────────────────────────────

@login_required
def jaugeage_rapport(request, pk):
    """Vue d'impression A4 du Rapport de Jaugeage Journalier (RJJ)."""
    jaugeage = get_object_or_404(
        JaugeageJour.objects.prefetch_related(
            'mesures__cuve__parametre_jaugeage',
            'mesures__cuve__produit__famille',
        ),
        pk=pk,
    )

    # Grouper les mesures par produit (même ordre que la saisie)
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

    # Totaux par groupe : volume_ambiant_depot (primaire, comme saisie) + @15°C (secondaire)
    totaux_groupes = []
    total_depot_vad = 0.0
    total_depot_v15c = 0.0
    has_any_vad = False
    has_any_v15c = False
    for pg in product_groups:
        t_vad = 0.0
        t_v15c = 0.0
        has_vad = False
        has_v15c = False
        for m in pg['mesures']:
            v_vad = m.volume_ambiant_depot
            v_v15c = m.volume_standard_15c_calcule
            if v_vad is not None:
                t_vad += float(v_vad)
                has_vad = True
                has_any_vad = True
            if v_v15c is not None:
                t_v15c += float(v_v15c)
                has_v15c = True
                has_any_v15c = True
        pg['total_vad'] = t_vad if has_vad else None
        pg['total_v15c'] = t_v15c if has_v15c else None
        totaux_groupes.append({
            'produit':    pg['produit'],
            'total_vad':  t_vad if has_vad else None,
            'total_v15c': t_v15c if has_v15c else None,
        })
        total_depot_vad += t_vad
        total_depot_v15c += t_v15c

    # Liste plate des mesures (pour colonnes du tableau rapport)
    all_mesures = [m for pg in product_groups for m in pg['mesures']]

    return render(request, 'Jaugeage/jaugeage_rapport.html', {
        'jaugeage':       jaugeage,
        'product_groups': product_groups,
        'all_mesures':    all_mesures,
        'totaux_groupes': totaux_groupes,
        'total_depot':    total_depot_vad if has_any_vad else None,
        'total_v15c':     total_depot_v15c if has_any_v15c else None,
        'nb_cuves':       len(all_mesures),
    })


# ─────────────────────────────────────────────────────────────
#  PARAMÈTRES MÉTROLOGIQUES — Fiche normative API MPMS
# ─────────────────────────────────────────────────────────────

@login_required
def parametres_metrologiques(request):
    """
    Écran informatif en lecture seule : présente les constantes et l'algorithme
    API MPMS Chapter 11.1 / ASTM D1250 (Octobre 1995) utilisés dans petroleum_calc.py.
    """
    from .petroleum_calc import K_SUPER, K_MIDDLE, K_HEAVY, A_AMB, B_AMB

    plages = [
        {
            'id': 'super',
            'label': 'Produits légers',
            'categorie': 'Super, essence sans plomb',
            'seuil': 'ρ ≤ 770 kg/m³',
            'type': 'standard',
            'k0': K_SUPER[0],
            'k1': K_SUPER[1],
            'icone_couleur': '#E8760A',
            'bg_couleur': '#fff7ed',
            'border_couleur': '#fed7aa',
        },
        {
            'id': 'ambigue',
            'label': 'Zone ambiguë',
            'categorie': 'Algorithme itératif spécial (point fixe, démarrage à 778,84 kg/m³)',
            'seuil': '770 < ρ < 788 kg/m³',
            'type': 'ambiguous',
            'a': A_AMB,
            'b': B_AMB,
            'icone_couleur': '#3b82f6',
            'bg_couleur': '#eff6ff',
            'border_couleur': '#bfdbfe',
        },
        {
            'id': 'middle',
            'label': 'Produits moyens',
            'categorie': 'Gasoil, kérosène, jet-A1',
            'seuil': '788 ≤ ρ < 839 kg/m³',
            'type': 'standard',
            'k0': K_MIDDLE[0],
            'k1': K_MIDDLE[1],
            'icone_couleur': '#16a34a',
            'bg_couleur': '#f0fdf4',
            'border_couleur': '#bbf7d0',
        },
        {
            'id': 'heavy',
            'label': 'Produits lourds',
            'categorie': 'Fuel-oil, résidus lourds',
            'seuil': 'ρ ≥ 839 kg/m³',
            'type': 'standard',
            'k0': K_HEAVY[0],
            'k1': K_HEAVY[1],
            'icone_couleur': '#64748b',
            'bg_couleur': '#f8fafc',
            'border_couleur': '#e2e8f0',
        },
    ]

    norme = {
        'code': 'API MPMS Chapter 11.1 / ASTM D1250',
        'titre': (
            'Generalized Crude Oils, Refined Products and Lubricating Oils — '
            'Correction of observed density to density at 15°C'
        ),
        'date': 'Octobre 1995',
        'source_historique': r'J:\OPS\TRH_15.XLS / TVCF_15.XLS',
        'statut': "En vigueur dans l'industrie pétrolière de l'Afrique de l'Ouest",
        'iterations': 7,
    }

    return render(request, 'Jaugeage/parametres_metrologiques.html', {
        'plages': plages,
        'norme': norme,
    })


# ─────────────────────────────────────────────────────────────
#  MOUVEMENTS (entrée / sortie / cession / acquittement)
# ─────────────────────────────────────────────────────────────

@login_required
def mouvement_liste(request):
    """Liste paginée de tous les mouvements avec filtres GET."""
    from django.core.paginator import Paginator
    from django.db.models import Sum, Count

    qs = Mouvement.objects.select_related('produit', 'marketeur', 'camion').prefetch_related('lignes__cuve').order_by('-date_mouvement', '-date_saisie')

    # ── Filtres ──
    type_m      = request.GET.get('type', '').strip()
    regime      = request.GET.get('regime', '').strip()
    mkt_pk      = request.GET.get('marketeur', '').strip()
    produit_pk  = request.GET.get('produit', '').strip()
    date_debut  = request.GET.get('date_debut', '').strip()
    date_fin    = request.GET.get('date_fin', '').strip()
    q           = request.GET.get('q', '').strip()

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
            Q(numero_enregistrement__icontains=q) |
            Q(camion__immatriculation__icontains=q) |
            Q(bl_expediteur__icontains=q) |
            Q(marketeur__raison_sociale__icontains=q)
        )

    # ── Totaux sur le queryset filtré (avant pagination) ──
    nb_total   = qs.count()

    # Pagination
    paginator  = Paginator(qs, 50)
    page_num   = request.GET.get('page', 1)
    mouvements = paginator.get_page(page_num)

    marketeurs = Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale')
    produits   = Produit.objects.filter(statut='ACTIF').order_by('nom')

    return render(request, 'mouvements/liste.html', {
        'mouvements':  mouvements,
        'marketeurs':  marketeurs,
        'produits':    produits,
        'nb_total':    nb_total,
        'filtres': {
            'type':       type_m,
            'regime':     regime,
            'marketeur':  mkt_pk,
            'produit':    produit_pk,
            'date_debut': date_debut,
            'q':          q,
            'date_fin':   date_fin,
        },
        'type_choices':   Mouvement.TYPE_CHOICES,
        'regime_choices': Mouvement.REGIME_CHOICES,
    })


@login_required
def mouvement_creer(request):
    """Formulaire de création d'un nouveau mouvement."""
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
                messages.success(request, f"Mouvement {mouvement.numero_enregistrement} enregistré avec succès.")
                return redirect('mouvement_liste')
    else:
        form = MouvementForm()
        lignes_formset = LigneMouvementFormSet()

    camions    = Camion.objects.select_related('marketeur').filter(statut='EN_SERVICE').order_by('immatriculation')
    cuves      = Cuve.objects.select_related('produit').filter(statut='ACTIVE').order_by('numero')
    marketeurs = Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale')

    return render(request, 'mouvements/saisie.html', {
        'form':            form,
        'lignes_formset':  lignes_formset,
        'titre':           'Nouveau mouvement',
        'camions':         camions,
        'cuves':           cuves,
        'marketeurs':      marketeurs,
        'mode':            'creer',
    })


@login_required
def mouvement_modifier(request, pk):
    """Formulaire d'édition d'un mouvement existant."""
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
            messages.success(
                request,
                f"Mouvement N° {mouvement.numero_enregistrement} modifié avec succès. "
                f"Les calculs automatiques ont été actualisés."
            )
            return redirect('mouvement_modifier', pk=mouvement.pk)
    else:
        form = MouvementForm(instance=mouvement)
        lignes_formset = LigneMouvementFormSet(instance=mouvement)

    camions    = Camion.objects.select_related('marketeur').filter(statut='EN_SERVICE').order_by('immatriculation')
    cuves      = Cuve.objects.select_related('produit').filter(statut='ACTIVE').order_by('numero')
    marketeurs = Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale')

    return render(request, 'mouvements/saisie.html', {
        'form':            form,
        'lignes_formset':  lignes_formset,
        'mouvement':       mouvement,
        'titre':           f'Modifier — {mouvement.numero_enregistrement}',
        'camions':         camions,
        'cuves':           cuves,
        'marketeurs':      marketeurs,
        'mode':            'modification',
    })


@login_required
@require_POST
def mouvement_calcul_preview(request):
    """
    Endpoint AJAX : retourne les calculs petroleum_calc pour la section
    "Contrôle final avant déchargement" sans enregistrer de mouvement.
    Entrée : JSON (type_mouvement='ENTREE' ou 'SORTIE' + champs numériques).
    Sortie : JSON avec les valeurs calculées.
    """
    import json
    from . import petroleum_calc as pc
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

        # P/G réception (col. AC) — simple soustraction
        if v_amb_recu is not None and v_amb_expe is not None:
            result['perte_gain_reception'] = round(v_amb_recu - v_amb_expe, 2)

        # D@15°C calculée (col. AG) via API MPMS TRH_15
        d15 = None
        if dens_obs is not None and temp_labo is not None:
            try:
                d15 = round(pc.density_at_15c(dens_obs, temp_labo), 2)
                result['densite_15c_calculee'] = d15
            except Exception:
                pass

        # Écart densité (col. AH)
        if d15 is not None and dens_expe is not None:
            result['ecart_densite_15c'] = round((d15 - dens_expe) / 1000, 4)

        # Vcf @15°C (col. AI) via API MPMS TVCF_15
        vcf = None
        if d15 is not None and temp_recept is not None:
            try:
                vcf = round(pc.vcf_to_15c(d15, temp_recept), 4)
                result['coefficient_conversion_15c'] = vcf
            except Exception:
                pass

        # Volume @15°C reçu (col. AJ)
        if v_amb_recu is not None and vcf is not None:
            result['volume_15c_recu'] = round(v_amb_recu * vcf, 2)

        # P/G @15°C (col. AK)
        pg_recept = result.get('perte_gain_reception')
        if pg_recept is not None and vcf is not None:
            result['perte_gain_15c'] = round(pg_recept * vcf, 2)

        # Poids (col. AL)
        v15 = result.get('volume_15c_recu')
        if v15 is not None and d15 is not None:
            result['poids_kg'] = round(v15 * d15 / 1000, 2)

    elif type_mvt == 'SORTIE':
        v_amb_sortie = _f('volume_ambiant_sortie')
        dens_15_sortie = _f('densite_15c_sortie')
        temp_sortie  = _f('temperature_sortie')

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


@login_required
def mouvement_detail(request, pk):
    """Fiche de détail d'un mouvement — lecture seule."""
    mouvement = get_object_or_404(
        Mouvement.objects.select_related(
            'marketeur', 'produit', 'camion', 'camion__marketeur',
            'chauffeur', 'cession_marketeur_destinataire',
        ).prefetch_related('lignes__cuve__produit'),
        pk=pk
    )
    return render(request, 'mouvements/detail.html', {'mouvement': mouvement})


@login_required
def mouvement_supprimer(request, pk):
    """Suppression d'un mouvement — réservée au staff."""
    if not request.user.is_staff:
        messages.error(request, "La suppression de mouvements est réservée au staff.")
        return redirect('mouvement_liste')

    mouvement = get_object_or_404(Mouvement, pk=pk)

    if request.method == 'POST':
        mouvement.delete()
        messages.success(request, "Mouvement supprimé.")
        return redirect('mouvement_liste')

    return render(request, 'mouvements/confirmer_suppression.html', {'mouvement': mouvement})


# ═════════════════════════════════════════════════════════════
#  PÉRIODES COMPTABLES
# ═════════════════════════════════════════════════════════════

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView


class ListePeriodesView(LoginRequiredMixin, ListView):
    """Liste chronologique des périodes comptables + bouton d'ouverture."""
    template_name   = 'periode/liste.html'
    context_object_name = 'periodes'
    paginate_by     = 24
    ordering        = ['-annee', '-mois']

    def get_queryset(self):
        from .models import PeriodeComptable
        return PeriodeComptable.objects.all().order_by('-annee', '-mois')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import PeriodeComptable
        from .services.periode_comptable import mois_suivant

        derniere = PeriodeComptable.objects.order_by('-annee', '-mois').first()

        if derniere is None:
            # Aucune période : proposer le mois courant comme première
            from django.utils import timezone
            aujourd_hui = timezone.now().date()
            ctx['peut_ouvrir_suivante'] = True
            ctx['premiere_periode']     = True
            ctx['mois_a_ouvrir']        = aujourd_hui.month
            ctx['annee_a_ouvrir']       = aujourd_hui.year
        elif derniere.statut == 'CLOTUREE':
            m, a = mois_suivant(derniere.mois, derniere.annee)
            ctx['peut_ouvrir_suivante'] = True
            ctx['premiere_periode']     = False
            ctx['mois_a_ouvrir']        = m
            ctx['annee_a_ouvrir']       = a
        else:
            ctx['peut_ouvrir_suivante'] = False
            ctx['premiere_periode']     = False
            ctx['mois_a_ouvrir']        = None
            ctx['annee_a_ouvrir']       = None

        return ctx


class OuvrirPeriodeView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Confirmation et exécution de l'ouverture d'une période."""

    def test_func(self):
        return self.request.user.is_staff

    def _get_mois_annee(self, request):
        from django.utils import timezone
        from .models import PeriodeComptable
        from .services.periode_comptable import mois_suivant

        # Paramètres GET ou POST
        source = request.GET if request.method == 'GET' else request.POST
        try:
            mois  = int(source.get('mois', 0))
            annee = int(source.get('annee', 0))
            if not (1 <= mois <= 12 and 2020 <= annee <= 2100):
                raise ValueError
        except (ValueError, TypeError):
            # Fallback : calculer depuis la dernière période
            derniere = PeriodeComptable.objects.order_by('-annee', '-mois').first()
            if derniere is None:
                aujourd_hui = timezone.now().date()
                mois, annee = aujourd_hui.month, aujourd_hui.year
            else:
                mois, annee = mois_suivant(derniere.mois, derniere.annee)
        return mois, annee

    def get(self, request):
        from .models import PeriodeComptable
        mois, annee   = self._get_mois_annee(request)
        premiere      = not PeriodeComptable.objects.exists()
        return render(request, 'periode/ouvrir_confirm.html', {
            'mois_propose':  mois,
            'annee_propose': annee,
            'premiere':      premiere,
        })

    def post(self, request):
        from django.core.exceptions import ValidationError
        from .services.periode_comptable import ouvrir_periode
        mois, annee = self._get_mois_annee(request)
        try:
            ouvrir_periode(mois, annee, user=request.user)
            messages.success(request, f"Période {mois}/{annee} ouverte avec succès.")
            return redirect('periode_liste')
        except ValidationError as exc:
            messages.error(request, exc.message)
            from .models import PeriodeComptable
            premiere = not PeriodeComptable.objects.exists()
            return render(request, 'periode/ouvrir_confirm.html', {
                'mois_propose':  mois,
                'annee_propose': annee,
                'premiere':      premiere,
            })


# ═════════════════════════════════════════════════════════════
#  COULAGE — RÉPARTITION MENSUELLE
# ═════════════════════════════════════════════════════════════

def _rapport_depuis_snapshot(cloture):
    """
    Reconstruit le dict rapport compatible avec repartition.html
    depuis la snapshot DB (ClotureCoulageMensuel).
    """
    from decimal import Decimal
    from collections import defaultdict

    D0 = Decimal('0')

    produits_list = [
        cp.produit
        for cp in cloture.produits_coulage
            .select_related('produit')
            .order_by('produit__nom')
    ]

    coefficients = {}
    pertes_gains = {}
    cumuls       = {}
    for cp in cloture.produits_coulage.all():
        pk = cp.produit_id
        coefficients[pk] = cp.coefficient
        pertes_gains[pk] = cp.pertes_gains
        cumuls[pk] = {
            'brut_entree': cp.cumul_entree,
            'coul_entree': D0,
            'entree':      cp.cumul_entree,
            'sortie':      cp.cumul_sortie,
        }

    # Grouper les lignes par marketeur
    mkt_map = defaultdict(dict)
    mkt_meta = {}
    for ligne in cloture.lignes.select_related('marketeur', 'produit').all():
        mkt = ligne.marketeur
        mkt_meta[mkt.pk] = {
            'obj':          mkt,
            'motif':        ligne.motif,
            'prix_unitaire': ligne.prix_unitaire,
        }
        if ligne.produit_id is not None:
            mkt_map[mkt.pk][ligne.produit_id] = {
                'brut_entree':  ligne.brut_entree,
                'coul_entree':  ligne.coul_entree,
                'entree_nette': ligne.entree_nette,
                'sortie':       ligne.sortie,
                'base_qp_coul': ligne.base_qp_coul,
                'coef_qp_coul': ligne.coef_qp_coul,
                'qp_coul':      ligne.qp_coul,
                'volume_sorti': ligne.volume_sorti,
            }

    lignes = []
    for mkt_pk, par_produit in mkt_map.items():
        meta  = mkt_meta[mkt_pk]
        v_tot = sum((pp.get('volume_sorti', D0) for pp in par_produit.values()), D0)
        m_tot = sum(
            (pp.get('volume_sorti', D0) * meta['prix_unitaire']
             for pp in par_produit.values()), D0
        )
        lignes.append({
            'marketeur':          meta['obj'],
            'par_produit':        par_produit,
            'volume_global_sorti': v_tot,
            'motif':              meta['motif'],
            'prix_unitaire':      meta['prix_unitaire'],
            'montant':            m_tot,
        })
    # Trier par raison sociale pour un affichage stable
    lignes.sort(key=lambda x: x['marketeur'].raison_sociale)

    # Totaux agrégés
    totaux_par_produit = {}
    for produit in produits_list:
        pk = produit.pk
        def _s(field):
            return sum((l['par_produit'].get(pk, {}).get(field, D0) for l in lignes), D0)
        totaux_par_produit[pk] = {
            'brut_entree':  _s('brut_entree'),
            'coul_entree':  _s('coul_entree'),
            'entree_nette': _s('entree_nette'),
            'sortie':       _s('sortie'),
            'base_qp_coul': _s('base_qp_coul'),
            'coef_qp_coul': coefficients.get(pk, D0),
            'qp_coul':      _s('qp_coul'),
            'volume_sorti': _s('volume_sorti'),
        }

    totaux = {
        'par_produit':         totaux_par_produit,
        'volume_global_sorti': sum((l['volume_global_sorti'] for l in lignes), D0),
        'motif':               cloture.motif,
        'prix_unitaire':       cloture.prix_unitaire_passage,
        'montant':             cloture.total_montant,
    }

    return {
        'periode':      cloture.periode,
        'produits':     produits_list,
        'coefficients': coefficients,
        'pertes_gains': pertes_gains,
        'cumuls':       cumuls,
        'lignes':       lignes,
        'totaux':       totaux,
        'parametres': {
            'prix_unitaire_passage': cloture.prix_unitaire_passage,
            'motif':                 cloture.motif,
        },
    }


class ListePeriodesCoulageView(LoginRequiredMixin, ListView):
    """Liste des périodes avec leur statut de coulage."""
    template_name        = 'coulage/liste_periodes.html'
    context_object_name  = 'object_list'
    paginate_by          = 24

    def get_queryset(self):
        from .models import PeriodeComptable
        return (
            PeriodeComptable.objects
            .select_related('cloture_coulage')
            .order_by('-annee', '-mois')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['produits_actifs_list'] = list(
            Produit.objects.filter(statut='ACTIF').order_by('nom')
        )
        return ctx


class RepartitionCoulageView(LoginRequiredMixin, View):
    """Affiche la répartition du coulage d'une période (live ou snapshot)."""

    def get(self, request, periode_id):
        from .models import PeriodeComptable
        from .services.coulage_repartition import calculer_repartition_coulage

        periode = get_object_or_404(PeriodeComptable, pk=periode_id)

        if periode.statut == 'CLOTUREE':
            try:
                cloture = periode.cloture_coulage
                rapport = _rapport_depuis_snapshot(cloture)
                source  = 'SNAPSHOT'
            except Exception:
                rapport = calculer_repartition_coulage(periode)
                source  = 'LIVE'
        else:
            rapport = calculer_repartition_coulage(periode)
            source  = 'LIVE'

        peut_cloturer = (
            periode.statut == 'OUVERTE'
            and request.user.is_staff
            and not hasattr(periode, 'cloture_coulage')
        )
        # Vérification plus fiable :
        try:
            periode.cloture_coulage
            deja_cloture = True
        except Exception:
            deja_cloture = False
        peut_cloturer = periode.statut == 'OUVERTE' and request.user.is_staff

        return render(request, 'coulage/repartition.html', {
            'periode':       periode,
            'rapport':       rapport,
            'source':        source,
            'peut_cloturer': peut_cloturer,
        })


class ClotureCoulageView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Clôture une période comptable (POST)."""

    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, periode_id):
        from .models import PeriodeComptable
        from .services.periode_comptable import cloturer_periode
        from django.core.exceptions import ValidationError

        periode = get_object_or_404(PeriodeComptable, pk=periode_id)
        notes   = request.POST.get('notes', '').strip() or None

        try:
            cloturer_periode(periode, user=request.user, notes=notes)
            from .services.periode_comptable import mois_suivant
            m, a = mois_suivant(periode.mois, periode.annee)
            messages.success(
                request,
                f"Période {periode.libelle} clôturée. "
                f"Pour commencer le mois suivant, ouvrez la période {m}/{a} "
                f"depuis la liste des périodes."
            )
        except ValidationError as exc:
            messages.error(request, exc.message)

        return redirect('coulage_detail', periode_id=periode_id)

    def get(self, request, periode_id):
        return redirect('coulage_detail', periode_id=periode_id)


class ExportCoulageExcelView(LoginRequiredMixin, View):
    """Export Excel de la répartition du coulage."""

    def get(self, request, periode_id):
        from .models import PeriodeComptable
        from .services.coulage_repartition import calculer_repartition_coulage
        from django.http import HttpResponse
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter

        periode = get_object_or_404(PeriodeComptable, pk=periode_id)

        if periode.statut == 'CLOTUREE':
            try:
                rapport = _rapport_depuis_snapshot(periode.cloture_coulage)
            except Exception:
                rapport = calculer_repartition_coulage(periode)
        else:
            rapport = calculer_repartition_coulage(periode)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Coulage {periode.libelle}"

        navy_fill = PatternFill('solid', fgColor='1E3A5F')
        navy_font = Font(color='FFFFFF', bold=True, size=10)
        header_font = Font(bold=True, size=10)
        normal_font = Font(size=9)
        center     = Alignment(horizontal='center', vertical='center')
        right_al   = Alignment(horizontal='right')
        thin_side  = Side(style='thin')
        thin_border = Border(left=thin_side, right=thin_side,
                             bottom=thin_side, top=thin_side)
        num_fmt = '#,##0'
        coef_fmt = '0.00000000'

        produits = rapport['produits']

        # ── Titre ────────────────────────────────────────────────
        ws.merge_cells(f'A1:{get_column_letter(6 + len(produits) * 7)}1')
        titre_cell = ws['A1']
        titre_cell.value = f"Répartition du coulage — {periode.libelle}"
        titre_cell.font  = Font(bold=True, size=14, color='1E3A5F')
        ws.row_dimensions[1].height = 24

        # ── En-têtes ─────────────────────────────────────────────
        row = 3
        ws.cell(row=row, column=1, value='Code').font       = navy_font
        ws.cell(row=row, column=1).fill                     = navy_fill
        ws.cell(row=row, column=1).alignment                = center
        ws.cell(row=row, column=2, value='Marketeur').font  = navy_font
        ws.cell(row=row, column=2).fill                     = navy_fill

        col = 3
        for produit in produits:
            for sub in [f'Brut Entrée {produit.code}',
                        f'Coul. Entrée {produit.code}',
                        f'Nette {produit.code}']:
                c = ws.cell(row=row, column=col, value=sub)
                c.font = navy_font; c.fill = navy_fill; c.alignment = center
                col += 1

        for produit in produits:
            c = ws.cell(row=row, column=col, value=f'Sortie {produit.code}')
            c.font = navy_font; c.fill = navy_fill; c.alignment = center
            col += 1

        for produit in produits:
            for sub in [f'Base QP {produit.code}',
                        f'Coef. {produit.code}',
                        f'QP Coul. {produit.code}']:
                c = ws.cell(row=row, column=col, value=sub)
                c.font = navy_font; c.fill = navy_fill; c.alignment = center
                col += 1

        for hdr in ['Vol. global sorti', 'PU/L', 'Montant FCFA']:
            c = ws.cell(row=row, column=col, value=hdr)
            c.font = navy_font; c.fill = navy_fill; c.alignment = center
            col += 1

        # ── Données ───────────────────────────────────────────────
        for ligne in rapport['lignes']:
            row += 1
            ws.cell(row=row, column=1,
                    value=f"MK{ligne['marketeur'].pk:03d}").font = normal_font
            ws.cell(row=row, column=2,
                    value=ligne['marketeur'].sigle or ligne['marketeur'].raison_sociale)

            col = 3
            for produit in produits:
                pp = ligne['par_produit'].get(produit.pk, {})
                for field in ['brut_entree', 'coul_entree', 'entree_nette']:
                    c = ws.cell(row=row, column=col, value=float(pp.get(field, 0)))
                    c.number_format = num_fmt; c.alignment = right_al
                    col += 1

            for produit in produits:
                pp = ligne['par_produit'].get(produit.pk, {})
                c = ws.cell(row=row, column=col, value=float(pp.get('sortie', 0)))
                c.number_format = num_fmt; c.alignment = right_al
                col += 1

            for produit in produits:
                pp = ligne['par_produit'].get(produit.pk, {})
                c1 = ws.cell(row=row, column=col, value=float(pp.get('base_qp_coul', 0)))
                c1.number_format = num_fmt; c1.alignment = right_al; col += 1
                c2 = ws.cell(row=row, column=col, value=float(pp.get('coef_qp_coul', 0)))
                c2.number_format = coef_fmt; c2.alignment = right_al; col += 1
                c3 = ws.cell(row=row, column=col, value=float(pp.get('qp_coul', 0)))
                c3.number_format = num_fmt; c3.alignment = right_al; col += 1

            c = ws.cell(row=row, column=col, value=float(ligne['volume_global_sorti']))
            c.number_format = num_fmt; c.alignment = right_al; col += 1
            ws.cell(row=row, column=col, value=float(ligne['prix_unitaire'])); col += 1
            c = ws.cell(row=row, column=col, value=float(ligne['montant']))
            c.number_format = num_fmt; c.alignment = right_al; col += 1

        # ── Ligne totaux ──────────────────────────────────────────
        row += 1
        c = ws.cell(row=row, column=1, value='TOTAUX')
        c.font = header_font
        c = ws.cell(row=row, column=col - 1,  # Montant
                    value=float(rapport['totaux']['montant']))
        c.number_format = num_fmt; c.alignment = right_al
        c.font = Font(bold=True)

        # Largeurs colonnes
        ws.column_dimensions['A'].width = 8
        ws.column_dimensions['B'].width = 22
        for i in range(3, col):
            ws.column_dimensions[get_column_letter(i)].width = 13

        # Réponse HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="coulage_{periode.libelle.replace(" ", "_")}.xlsx"'
        )
        wb.save(response)
        return response


# ═════════════════════════════════════════════════════════════
#  SUIVI ÉVOLUTION JOURNALIER
# ═════════════════════════════════════════════════════════════

class SuiviEvolutionView(LoginRequiredMixin, View):
    """Tableau journalier stock/mouvements pour un produit sur une période."""

    def get(self, request, periode_id, produit_id):
        from .models import PeriodeComptable, Produit
        from .services.suivi_evolution import calculer_suivi_evolution

        periode  = get_object_or_404(PeriodeComptable, pk=periode_id)
        produit  = get_object_or_404(Produit, pk=produit_id)
        produits = list(Produit.objects.filter(statut='ACTIF').order_by('nom'))
        rapport  = calculer_suivi_evolution(periode, produit)

        return render(request, 'coulage/suivi_evolution.html', {
            'periode':  periode,
            'produit':  produit,
            'produits': produits,
            'rapport':  rapport,
        })


class ExportSuiviExcelView(LoginRequiredMixin, View):
    """Export Excel du suivi évolution journalier."""

    def get(self, request, periode_id, produit_id):
        from .models import PeriodeComptable, Produit
        from .services.suivi_evolution import calculer_suivi_evolution
        from .services.export_excel import exporter_suivi_xlsx
        from django.http import HttpResponse

        periode = get_object_or_404(PeriodeComptable, pk=periode_id)
        produit = get_object_or_404(Produit, pk=produit_id)
        rapport = calculer_suivi_evolution(periode, produit)

        contenu = exporter_suivi_xlsx(rapport)
        response = HttpResponse(
            contenu,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        nom = f"suivi_{produit.code}_{periode.libelle.replace(' ', '_')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{nom}"'
        return response


# ═════════════════════════════════════════════════════════════
#  FRAIS DE PASSAGE
# ═════════════════════════════════════════════════════════════

class FraisPassageView(LoginRequiredMixin, View):
    """Document de facturation mensuel — frais de passage par marketeur."""

    def get(self, request, periode_id):
        from .models import PeriodeComptable
        from .services.frais_passage import calculer_frais_passage

        periode = get_object_or_404(PeriodeComptable, pk=periode_id)
        rapport = calculer_frais_passage(periode)

        return render(request, 'coulage/frais_passage.html', {
            'periode': periode,
            'rapport': rapport,
        })


class ExportFraisPassageExcelView(LoginRequiredMixin, View):
    """Export Excel des frais de passage."""

    def get(self, request, periode_id):
        from .models import PeriodeComptable
        from .services.frais_passage import calculer_frais_passage
        from .services.export_excel import exporter_frais_passage_xlsx
        from django.http import HttpResponse

        periode = get_object_or_404(PeriodeComptable, pk=periode_id)
        rapport = calculer_frais_passage(periode)

        contenu = exporter_frais_passage_xlsx(rapport)
        response = HttpResponse(
            contenu,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        nom = f"frais_passage_{periode.libelle.replace(' ', '_')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{nom}"'
        return response
