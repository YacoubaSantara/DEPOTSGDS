"""
Vues du module Périodes comptables.
Ouverture contrôlée — aucune création implicite.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import ListView


class ListePeriodesView(LoginRequiredMixin, ListView):
    template_name = 'periode/liste.html'
    context_object_name = 'periodes'
    paginate_by = 24

    def get_queryset(self):
        from SGDS.models import PeriodeComptable
        return (
            PeriodeComptable.objects
            .select_related('cloture_par', 'cloture_coulage')
            .order_by('-annee', '-mois')
        )

    def get_context_data(self, **kwargs):
        from SGDS.models import PeriodeComptable
        from SGDS.services.periode_comptable import mois_suivant, verifier_peut_ouvrir_periode

        ctx = super().get_context_data(**kwargs)

        derniere = PeriodeComptable.objects.order_by('-annee', '-mois').first()
        peut_ouvrir = False
        mois_a_ouvrir = annee_a_ouvrir = None

        if derniere is None:
            # Aucune période — on peut ouvrir une première
            peut_ouvrir = self.request.user.is_staff
            from django.utils import timezone
            now = timezone.now()
            mois_a_ouvrir, annee_a_ouvrir = now.month, now.year
        elif derniere.statut == 'CLOTUREE':
            m, a = mois_suivant(derniere.mois, derniere.annee)
            try:
                verifier_peut_ouvrir_periode(m, a)
                peut_ouvrir = self.request.user.is_staff
                mois_a_ouvrir, annee_a_ouvrir = m, a
            except ValidationError:
                pass

        ctx['peut_ouvrir_suivante'] = peut_ouvrir
        ctx['mois_a_ouvrir']        = mois_a_ouvrir
        ctx['annee_a_ouvrir']       = annee_a_ouvrir
        ctx['premiere_periode']     = derniere is None
        return ctx


class OuvrirPeriodeView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        from SGDS.models import PeriodeComptable
        from SGDS.services.periode_comptable import mois_suivant

        derniere = PeriodeComptable.objects.order_by('-annee', '-mois').first()

        if derniere is None:
            from django.utils import timezone
            now = timezone.now()
            mois_propose, annee_propose = now.month, now.year
        else:
            mois_propose, annee_propose = mois_suivant(derniere.mois, derniere.annee)

        # Surcharge depuis les paramètres GET (première période)
        try:
            mois_propose  = int(request.GET.get('mois',  mois_propose))
            annee_propose = int(request.GET.get('annee', annee_propose))
        except (ValueError, TypeError):
            pass

        return render(request, 'periode/ouvrir_confirm.html', {
            'mois_propose':  mois_propose,
            'annee_propose': annee_propose,
            'premiere':      derniere is None,
        })

    def post(self, request):
        from SGDS.services.periode_comptable import ouvrir_periode

        try:
            mois  = int(request.POST.get('mois',  0))
            annee = int(request.POST.get('annee', 0))
        except (ValueError, TypeError):
            messages.error(request, "Mois ou année invalide.")
            return redirect('periode_liste')

        try:
            periode = ouvrir_periode(mois, annee, user=request.user)
            messages.success(
                request,
                f"Période {periode.libelle} ouverte avec succès. "
                "Les saisies (mouvements, jaugeages) sont maintenant actives."
            )
        except ValidationError as e:
            messages.error(request, e.message)

        return redirect('periode_liste')
