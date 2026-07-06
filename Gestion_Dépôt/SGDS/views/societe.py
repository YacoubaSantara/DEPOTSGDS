"""
Vues — Fiche Société / Dépôt.

Accès piloté par les permissions RBAC voir_societe (lecture, societe_detail)
et modifier_societe (écriture, configuration_email + POST de societe_detail)
— voir SGDS/users/permissions_registry.py. La fiche est un singleton (pk=1).
Elle est créée automatiquement si absente.
"""
from django.shortcuts import render, redirect
from django.contrib import messages

from SGDS.users.decorators import voir_required


@voir_required('voir_societe')
def societe_detail(request):
    """
    Affiche et permet de modifier la fiche société.
    GET  → affiche le formulaire pré-rempli.
    POST → enregistre les modifications.
    """
    from SGDS.models import Societe
    from SGDS.forms import SocieteForm
    from SGDS.users.permissions import has_perm

    societe = Societe.get_instance()

    if request.method == 'POST' and not has_perm(request.user, 'modifier_societe'):
        messages.error(request, "Vous n'avez pas les droits pour modifier la fiche société.")
        return redirect('societe_detail')

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


@voir_required('modifier_societe')
def configuration_email(request):
    """
    Affiche et permet de modifier la configuration SMTP utilisée pour
    l'envoi des emails (notifications, états mensuels…).
    Le mot de passe n'est jamais ré-affiché en clair : un champ vide à
    l'enregistrement signifie « ne pas changer le mot de passe existant ».
    """
    from SGDS.models import ConfigurationEmail
    from SGDS.forms import ConfigurationEmailForm

    config = ConfigurationEmail.get_instance()

    if request.method == 'POST' and request.POST.get('action') == 'test':
        destinataire = request.POST.get('email_test', '').strip() or config.host_user
        if not destinataire:
            messages.error(request, "Indiquez une adresse de destination pour le test.")
        elif not config.host_user:
            messages.error(request, "Renseignez d'abord un utilisateur SMTP avant de tester l'envoi.")
        else:
            try:
                from django.core.mail import EmailMessage
                EmailMessage(
                    subject="[SGDS] Test de configuration email",
                    body="Cet email confirme que la configuration SMTP de SGDS fonctionne correctement.",
                    from_email=config.from_email,
                    to=[destinataire],
                    connection=config.get_connection(),
                ).send(fail_silently=False)
                messages.success(request, f"Email de test envoyé à {destinataire}.")
            except Exception as e:
                messages.error(request, f"Échec de l'envoi du test : {e}")
        return redirect('configuration_email')

    if request.method == 'POST':
        form = ConfigurationEmailForm(request.POST, instance=config)
        if form.is_valid():
            config = form.save(commit=False)
            nouveau_mdp = request.POST.get('host_password', '').strip()
            if nouveau_mdp:
                config.host_password = nouveau_mdp
            config.save()
            messages.success(request, "Configuration email mise à jour avec succès.")
            return redirect('configuration_email')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ConfigurationEmailForm(instance=config)

    return render(request, 'Parametres/configuration_email.html', {
        'config': config,
        'form':   form,
    })


@voir_required('voir_gabarit_email_etat_mensuel')
def gabarit_email_etat_mensuel(request):
    """
    Affiche et permet de modifier le gabarit (sujet/corps) de l'email envoyé
    à chaque marketeur à la clôture d'une période, avec le bundle d'états
    mensuels (stock ouverture/fermeture, coulage répartition, frais de
    passage) en pièces jointes Excel + PDF.
    """
    from SGDS.models import ModeleEmailEtatMensuel, ConfigurationEmail, Marketeur, PeriodeComptable, Societe
    from SGDS.forms import ModeleEmailEtatMensuelForm
    from SGDS.services.etat_mensuel_envoi import envoyer_etat_mensuel_marketeur

    gabarit = ModeleEmailEtatMensuel.get_instance()

    if request.method == 'POST' and request.POST.get('action') == 'test':
        periode_id   = request.POST.get('periode_id')
        marketeur_id = request.POST.get('marketeur_id')
        destinataire = request.POST.get('email_test', '').strip()
        periode      = PeriodeComptable.objects.filter(uuid=periode_id).first() if periode_id else None
        marketeur    = Marketeur.objects.filter(uuid=marketeur_id).first() if marketeur_id else None
        config       = ConfigurationEmail.get_instance()

        if not periode or not marketeur:
            messages.error(request, "Sélectionnez une période et un marketeur existants pour le test.")
        elif not destinataire:
            messages.error(request, "Indiquez une adresse de destination pour le test.")
        elif not config.host_user:
            messages.error(request, "Renseignez d'abord la configuration SMTP avant de tester l'envoi.")
        else:
            envoi = envoyer_etat_mensuel_marketeur(periode, marketeur, config, email_override=destinataire)
            if envoi.statut == 'SUCCES':
                messages.success(request, f"Email de test envoyé à {destinataire}.")
            else:
                messages.error(request, f"Échec de l'envoi du test : {envoi.message_erreur}")
        return redirect('gabarit_email_etat_mensuel')

    if request.method == 'POST':
        form = ModeleEmailEtatMensuelForm(request.POST, instance=gabarit)
        if form.is_valid():
            form.save()
            messages.success(request, "Gabarit d'email mis à jour avec succès.")
            return redirect('gabarit_email_etat_mensuel')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ModeleEmailEtatMensuelForm(instance=gabarit)

    return render(request, 'Parametres/gabarit_email_etat_mensuel.html', {
        'gabarit':   gabarit,
        'form':      form,
        'periodes':  PeriodeComptable.objects.order_by('-annee', '-mois')[:24],
        'marketeurs': Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale'),
        'societe':   Societe.get_instance(),
    })


@voir_required('voir_gabarit_email_mouvement')
def gabarit_email_mouvement(request):
    """
    Affiche et permet de modifier le gabarit (sujet/corps) de l'email envoyé
    immédiatement au marketeur à la création d'un mouvement (Entrée/Sortie/
    Cession/Acquittement), avec le PDF du mouvement en pièce jointe. Un seul
    gabarit générique, partagé par les 4 types.
    """
    from SGDS.models import ModeleEmailMouvement, ConfigurationEmail, Mouvement
    from SGDS.forms import ModeleEmailMouvementForm
    from SGDS.services.email_mouvement import envoyer_email_mouvement

    gabarit = ModeleEmailMouvement.get_instance()

    if request.method == 'POST' and request.POST.get('action') == 'test':
        mouvement_id = request.POST.get('mouvement_id')
        destinataire = request.POST.get('email_test', '').strip()
        mouvement    = Mouvement.objects.filter(uuid=mouvement_id).select_related('marketeur', 'produit').first() if mouvement_id else None
        config       = ConfigurationEmail.get_instance()

        if not mouvement:
            messages.error(request, "Sélectionnez un mouvement existant pour le test.")
        elif not destinataire:
            messages.error(request, "Indiquez une adresse de destination pour le test.")
        elif not config.host_user:
            messages.error(request, "Renseignez d'abord la configuration SMTP avant de tester l'envoi.")
        else:
            try:
                envoyer_email_mouvement(mouvement.marketeur, mouvement, config, email_override=destinataire)
                messages.success(request, f"Email de test envoyé à {destinataire}.")
            except Exception as e:
                messages.error(request, f"Échec de l'envoi du test : {e}")
        return redirect('gabarit_email_mouvement')

    if request.method == 'POST':
        form = ModeleEmailMouvementForm(request.POST, instance=gabarit)
        if form.is_valid():
            form.save()
            messages.success(request, "Gabarit d'email mis à jour avec succès.")
            return redirect('gabarit_email_mouvement')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ModeleEmailMouvementForm(instance=gabarit)

    return render(request, 'Parametres/gabarit_email_mouvement.html', {
        'gabarit':    gabarit,
        'form':       form,
        'mouvements': Mouvement.objects.select_related('marketeur', 'produit').order_by('-date_mouvement', '-pk')[:30],
    })
