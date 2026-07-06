"""
Vues du module Exercices comptables.
Ouverture automatique (via ouvrir_periode) — clôture manuelle uniquement.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from SGDS.services.depot_scope import depot_scope, depot_requis
from SGDS.users.decorators import VoirRequiredMixin


class ListeExercicesView(LoginRequiredMixin, VoirRequiredMixin, ListView):
    permission_codename = 'voir_exercice'
    template_name = 'exercice/liste.html'
    context_object_name = 'exercices'
    paginate_by = 12

    def get_queryset(self):
        from SGDS.models import Exercice
        return depot_scope(
            self.request,
            Exercice.objects.select_related('cloture_par'),
        ).order_by('-annee')


class ClotureExerciceView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, annee):
        from SGDS.models import Exercice
        from SGDS.services.exercice import verifier_peut_cloturer_exercice

        if depot_requis(request):
            return redirect('exercice_liste')

        exercice = get_object_or_404(Exercice, depot=request.depot, annee=annee)
        peut_cloturer = True
        erreur = None
        try:
            verifier_peut_cloturer_exercice(exercice)
        except ValidationError as e:
            peut_cloturer = False
            erreur = e.message

        return render(request, 'exercice/cloturer_confirm.html', {
            'exercice':      exercice,
            'peut_cloturer': peut_cloturer,
            'erreur':        erreur,
        })

    def post(self, request, annee):
        from SGDS.models import Exercice
        from SGDS.services.exercice import cloturer_exercice

        if depot_requis(request):
            return redirect('exercice_liste')

        exercice = get_object_or_404(Exercice, depot=request.depot, annee=annee)
        notes = request.POST.get('notes', '').strip() or None

        try:
            cloturer_exercice(exercice, user=request.user, notes=notes)
            messages.success(request, f"{exercice.libelle} clôturé avec succès.")
        except ValidationError as e:
            messages.error(request, e.message)

        return redirect('exercice_liste')
