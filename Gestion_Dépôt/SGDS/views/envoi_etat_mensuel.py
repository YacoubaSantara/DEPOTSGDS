"""
Historique des envois du bundle d'états mensuels (Excel + PDF) aux
marketeurs, avec possibilité de renvoi manuel en cas d'échec SMTP.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator

from SGDS.users.decorators import voir_required


@voir_required('voir_historique_envoi_etat_mensuel')
def historique_envoi_etat_mensuel(request):
    from SGDS.models import EnvoiEtatMensuel, PeriodeComptable, Marketeur

    qs = EnvoiEtatMensuel.objects.select_related('periode', 'marketeur', 'declenche_par')

    periode_id   = request.GET.get('periode_id', '').strip()
    marketeur_id = request.GET.get('marketeur_id', '').strip()
    statut       = request.GET.get('statut', '').strip()

    if periode_id:
        qs = qs.filter(periode__uuid=periode_id)
    if marketeur_id:
        qs = qs.filter(marketeur__uuid=marketeur_id)
    if statut in ('SUCCES', 'ECHEC'):
        qs = qs.filter(statut=statut)

    page = Paginator(qs, 50).get_page(request.GET.get('page'))

    return render(request, 'Parametres/historique_envoi_etat_mensuel.html', {
        'page':        page,
        'periodes':    PeriodeComptable.objects.order_by('-annee', '-mois')[:24],
        'marketeurs':  Marketeur.objects.order_by('raison_sociale'),
        'periode_id':  periode_id,
        'marketeur_id': marketeur_id,
        'statut':      statut,
    })


@voir_required('voir_historique_envoi_etat_mensuel')
def renvoyer_etat_mensuel(request, pk):
    from SGDS.models import EnvoiEtatMensuel, ConfigurationEmail
    from SGDS.services.etat_mensuel_envoi import envoyer_etat_mensuel_marketeur

    if request.method != 'POST':
        return redirect('historique_envoi_etat_mensuel')

    envoi_existant = get_object_or_404(EnvoiEtatMensuel, pk=pk)
    config = ConfigurationEmail.get_instance()
    if not config.host_user:
        messages.error(request, "Renseignez d'abord la configuration SMTP avant de renvoyer.")
        return redirect('historique_envoi_etat_mensuel')

    nouvel_envoi = envoyer_etat_mensuel_marketeur(
        envoi_existant.periode, envoi_existant.marketeur, config,
        declenche_par=request.user,
    )
    if nouvel_envoi.statut == 'SUCCES':
        messages.success(request, f"État mensuel renvoyé avec succès à {nouvel_envoi.email_destinataire}.")
    else:
        messages.error(request, f"Échec du renvoi : {nouvel_envoi.message_erreur}")
    return redirect('historique_envoi_etat_mensuel')
