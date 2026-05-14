"""
Vues — Fiche Société / Dépôt.

Accès réservé : SUPERADMIN et CHEF_DEPOT (décorateur chef_depot_required).
La fiche est un singleton (pk=1). Elle est créée automatiquement si absente.
"""
from django.shortcuts import render, redirect
from django.contrib import messages

from SGDS.users.decorators import chef_depot_required


@chef_depot_required
def societe_detail(request):
    """
    Affiche et permet de modifier la fiche société.
    GET  → affiche le formulaire pré-rempli.
    POST → enregistre les modifications.
    """
    from SGDS.models import Societe
    from SGDS.forms import SocieteForm

    societe = Societe.get_instance()

    if request.method == 'POST':
        form = SocieteForm(request.POST, request.FILES, instance=societe)
        if form.is_valid():
            form.save()
            messages.success(request, "Fiche société mise à jour avec succès.")
            return redirect('societe_detail')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = SocieteForm(instance=societe)

    ctx = {
        'societe': societe,
        'form':    form,
    }
    return render(request, 'Societe/detail.html', ctx)
