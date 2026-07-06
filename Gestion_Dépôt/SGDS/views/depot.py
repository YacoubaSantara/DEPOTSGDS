"""
Vues — Gestion des dépôts (sites physiques de stockage).

Accès piloté par la permission RBAC gerer_depot (voir
SGDS/users/permissions_registry.py) — par défaut accordée uniquement à
SUPERADMIN (gérer la liste des dépôts est une action globale, à la
différence de la fiche société qui reste accessible au CHEF_DEPOT), mais
ajustable depuis l'écran Rôles sans toucher au code.
"""
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from SGDS.users.decorators import voir_required
from SGDS.models import Depot
from SGDS.forms import DepotForm


@voir_required('gerer_depot')
def depot_liste(request):
    tous_depots = Depot.objects.all()
    q = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '')
    depots = tous_depots
    if q:
        depots = depots.filter(
            Q(code__icontains=q) | Q(nom__icontains=q) | Q(ville__icontains=q)
        )
    if statut:
        depots = depots.filter(statut=statut)
    paginator = Paginator(depots.order_by('code'), 25)
    page_depots = paginator.get_page(request.GET.get('page'))
    ctx = {
        'depots': page_depots,
        'filtres': {'q': q, 'statut': statut},
        'total': tous_depots.count(),
        'nb_actifs': tous_depots.filter(statut='ACTIF').count(),
        'nb_inactifs': tous_depots.filter(statut='INACTIF').count(),
        'nb_villes': tous_depots.exclude(ville__isnull=True).exclude(ville='').values('ville').distinct().count(),
        'q': q, 'statut': statut,
    }
    return render(request, 'Parametres/depots_liste.html', ctx)


@voir_required('gerer_depot')
def depot_create(request):
    if request.method == 'POST':
        form = DepotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Dépôt créé avec succès.")
            return redirect('depot_liste')
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = DepotForm()
    return render(request, 'Parametres/depot_form.html', {'form': form, 'depot': None})


@voir_required('gerer_depot')
def depot_update(request, uuid, slug):
    depot = get_object_or_404(Depot, uuid=uuid)
    if request.method == 'POST':
        form = DepotForm(request.POST, instance=depot)
        if form.is_valid():
            form.save()
            messages.success(request, "Dépôt mis à jour avec succès.")
            return redirect('depot_liste')
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = DepotForm(instance=depot)
    return render(request, 'Parametres/depot_form.html', {'form': form, 'depot': depot})


@login_required
def changer_depot_actif(request):
    """
    Bascule le dépôt actif — stocké en session.
    SUPERADMIN : peut choisir n'importe quel dépôt actif, ou 'TOUS' (vue
    consolidée). Autres rôles (CHEF_DEPOT/OPERATEUR/COMPTABLE) : uniquement
    parmi leurs dépôts assignés, jamais 'TOUS'.
    """
    if request.method == 'POST':
        valeur = request.POST.get('depot_id', '').strip()
        profil = getattr(request.user, 'profile', None)
        if profil and profil.est_superadmin:
            if valeur == 'TOUS':
                request.session['depot_actif_id'] = 'TOUS'
            elif Depot.objects.filter(pk=valeur, statut='ACTIF').exists():
                request.session['depot_actif_id'] = valeur
        elif profil and profil.depots.filter(pk=valeur, statut='ACTIF').exists():
            request.session['depot_actif_id'] = valeur
    from django.utils.http import url_has_allowed_host_and_scheme
    suivant = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
    if not url_has_allowed_host_and_scheme(
        suivant, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        suivant = '/'
    return redirect(suivant)
