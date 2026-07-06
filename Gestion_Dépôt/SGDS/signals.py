"""
Signaux Django pour mise à jour automatique des stocks cuves/produits.
Chargés via SgdsConfig.ready() dans apps.py.
"""
from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
from django.dispatch import receiver

from SGDS.models import JaugeageJour, MesureCuve, Mouvement, LigneMouvement, InventaireInitialMarketeur
from SGDS.services.recalcul_stock import (
    recalculer_stock_cuve,
    recalculer_stock_produit,
    recalculer_tous_stocks,
)



# ── JaugeageJour ────────────────────────────────────────────

@receiver(post_save, sender=JaugeageJour)
def on_jaugeage_saved(sender, instance, **kwargs):
    """
    Recalcule les cuves et produits dès que le statut du jaugeage change
    (validation ou dévalidation). Sans ce signal, le passage est_valide=True
    via jaugeage.save(update_fields=[...]) ne déclenchait aucun recalcul
    automatique des Cuve.niveau_actuel ni de Produit.stock_actuel.
    """
    produits_touches = set()
    for mesure in instance.mesures.select_related('cuve__produit').all():
        recalculer_stock_cuve(mesure.cuve)
        if mesure.cuve.produit:
            produits_touches.add(mesure.cuve.produit)
    for produit in produits_touches:
        recalculer_stock_produit(produit)

def _recalculer_cuves(cuves_set):
    """Recalcule le stock pour un ensemble de cuves et leurs produits."""
    produits_touches = set()
    for cuve in cuves_set:
        recalculer_stock_cuve(cuve)
        if cuve.produit:
            produits_touches.add(cuve.produit)
    for produit in produits_touches:
        recalculer_stock_produit(produit)


# ── Jaugeage ────────────────────────────────────────────────

@receiver(post_save, sender=MesureCuve)
def on_mesure_saved(sender, instance, created, **kwargs):
    """Met à jour niveau_actuel de la cuve + stock_actuel du produit."""
    recalculer_stock_cuve(instance.cuve)
    if instance.cuve.produit:
        recalculer_stock_produit(instance.cuve.produit)


@receiver(post_delete, sender=MesureCuve)
def on_mesure_deleted(sender, instance, **kwargs):
    try:
        with transaction.atomic():
            recalculer_stock_cuve(instance.cuve)
            if instance.cuve.produit:
                recalculer_stock_produit(instance.cuve.produit)
    except Exception:
        pass


@receiver(post_delete, sender=JaugeageJour)
def on_jaugeage_deleted(sender, instance, **kwargs):
    """Recalcul global après suppression d'un jaugeage entier."""
    recalculer_tous_stocks()


# ── Mouvements ──────────────────────────────────────────────

@receiver(post_save, sender=LigneMouvement)
@receiver(post_delete, sender=LigneMouvement)
def on_ligne_mouvement_changed(sender, instance, **kwargs):
    """
    Met à jour le stock de la cuve affectée par la ligne de mouvement.
    Couvre : création, modification et suppression d'une ligne.
    Si la ligne n'a pas de cuve, on recalcule directement le stock produit
    (les mouvements sans cuve sont intégrés au niveau produit).
    """
    if instance.cuve:
        recalculer_stock_cuve(instance.cuve)
        if instance.cuve.produit:
            recalculer_stock_produit(instance.cuve.produit)
    elif instance.produit_id:
        # Mouvement sans cuve : recalcul direct du stock produit
        recalculer_stock_produit(instance.produit)


# ── Inventaire Initial Marketeur ────────────────────────────

@receiver(post_save, sender=InventaireInitialMarketeur)
def on_inventaire_initial_saved(sender, instance, **kwargs):
    """
    Recalcule Produit.stock_actuel dès qu'un inventaire initial est saisi ou modifié.
    On recalcule TOUTES les cuves du produit (pas seulement celles liées à cet
    inventaire via M2M) pour éviter que des cuves non liées conservent une valeur
    niveau_actuel périmée, ce qui bloquerait le stock produit sur l'ancienne valeur.
    """
    for cuve in instance.produit.cuves.all():
        recalculer_stock_cuve(cuve)
    recalculer_stock_produit(instance.produit)


@receiver(post_delete, sender=InventaireInitialMarketeur)
def on_inventaire_initial_deleted(sender, instance, **kwargs):
    """Recalcule Produit.stock_actuel et toutes les cuves du produit après suppression."""
    try:
        with transaction.atomic():
            for cuve in instance.produit.cuves.all():
                recalculer_stock_cuve(cuve)
            recalculer_stock_produit(instance.produit)
    except Exception:
        pass


@receiver(m2m_changed, sender=InventaireInitialMarketeur.cuves.through)
def on_inventaire_cuves_changed(sender, instance, action, pk_set, **kwargs):
    """
    Quand les cuves associées à un inventaire initial changent (ajout / retrait),
    recalculer le niveau_actuel de chaque cuve touchée puis le stock_actuel du produit.
    """
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    try:
        with transaction.atomic():
            # Recalculer TOUTES les cuves du produit pour éviter toute valeur périmée
            for cuve in instance.produit.cuves.all():
                recalculer_stock_cuve(cuve)
            recalculer_stock_produit(instance.produit)
    except Exception:
        pass


@receiver(post_save, sender=Mouvement)
def on_mouvement_saved(sender, instance, **kwargs):
    """
    Recalcule les cuves impactées quand l'entête d'un mouvement change
    (ex : changement de type_mouvement ENTREE→SORTIE sans toucher les lignes).
    """
    cuves = {
        ligne.cuve
        for ligne in instance.lignes.select_related('cuve__produit').all()
        if ligne.cuve
    }
    if cuves:
        _recalculer_cuves(cuves)


@receiver(post_delete, sender=Mouvement)
def on_mouvement_deleted(sender, instance, **kwargs):
    """
    Recalcule le stock après suppression d'un mouvement.
    Les LigneMouvement sont déjà supprimées en cascade à ce stade, donc on
    recalcule toutes les cuves du produit concerné pour garantir la cohérence.
    """
    try:
        with transaction.atomic():
            produit = instance.produit
            for cuve in produit.cuves.select_related('parametre_jaugeage').all():
                recalculer_stock_cuve(cuve)
            recalculer_stock_produit(produit)
    except Exception:
        pass


# ── Notifications Marketeur ──────────────────────────────────

@receiver(post_save, sender=Mouvement)
def on_mouvement_created_notif(sender, instance, created, **kwargs):
    """Crée les notifications marketeur uniquement à la création d'un mouvement."""
    if not created:
        return

    from SGDS.models import Notification

    m = instance
    type_mv = m.type_mouvement

    if type_mv == 'ENTREE':
        titre = f"Entrée — {m.produit} — N° {m.numero_enregistrement}"
        message = (
            f"Vous avez une entrée enregistrée à la date du {m.date_mouvement:%d/%m/%Y}, "
            f"en provenance de {m.provenance or 'N/A'} (dépôt chargeur), "
            f"chargement le {m.date_chargement.strftime('%d/%m/%Y') if m.date_chargement else 'N/A'}, "
            f"régime : {m.get_regime_douanier_display()}. "
            f"Volume reçu : {m.volume_15c_recu or '—'} L @15°C. "
            f"N° BL chargeur : {m.bl_expediteur or '—'}."
        )
        Notification.objects.create(
            marketeur=m.marketeur, type_notif='ENTREE', mouvement=m,
            titre=titre, message=message,
        )
        _envoyer_email_mouvement(m.marketeur, m)

    elif type_mv == 'SORTIE':
        titre = f"Sortie — {m.produit} — N° {m.numero_enregistrement}"
        message = (
            f"Une sortie a été enregistrée le {m.date_mouvement:%d/%m/%Y} "
            f"à destination de {m.destination or 'N/A'}. "
            f"Volume sorti : {m.volume_15c_sortie or '—'} L @15°C. "
            f"Régime : {m.get_regime_douanier_display()}."
        )
        Notification.objects.create(
            marketeur=m.marketeur, type_notif='SORTIE', mouvement=m,
            titre=titre, message=message,
        )
        _envoyer_email_mouvement(m.marketeur, m)

    elif type_mv == 'CESSION':
        titre_emise = f"Cession émise — {m.produit} — N° {m.numero_enregistrement}"
        message_emise = (
            f"Une cession de {m.cession_volume_15c or '—'} L @15°C de {m.produit} "
            f"a été émise le {m.date_mouvement:%d/%m/%Y} "
            f"vers {m.cession_marketeur_destinataire}."
        )
        Notification.objects.create(
            marketeur=m.marketeur, type_notif='CESSION_EMISE', mouvement=m,
            titre=titre_emise, message=message_emise,
        )
        _envoyer_email_mouvement(m.marketeur, m)

        if m.cession_marketeur_destinataire:
            titre_recue = f"Cession reçue — {m.produit} — N° {m.numero_enregistrement}"
            message_recue = (
                f"Vous avez reçu une cession de {m.cession_volume_15c or '—'} L @15°C "
                f"de {m.produit} le {m.date_mouvement:%d/%m/%Y}, "
                f"en provenance de {m.marketeur}. "
                f"Motif : {m.cession_motif or 'Non précisé'}."
            )
            Notification.objects.create(
                marketeur=m.cession_marketeur_destinataire, type_notif='CESSION_RECUE', mouvement=m,
                titre=titre_recue, message=message_recue,
            )
            _envoyer_email_mouvement(m.cession_marketeur_destinataire, m)

    elif type_mv == 'ACQUITTEMENT':
        titre = f"Acquittement — {m.produit} — N° {m.numero_enregistrement}"
        message = (
            f"Un acquittement douanier de {m.acquittement_volume_15c or '—'} L @15°C "
            f"de {m.produit} a été effectué le {m.date_mouvement:%d/%m/%Y}. "
            f"Réf. déclaration : {m.acquittement_reference_declaration or 'N/A'}. "
            f"Date déclaration : "
            f"{m.acquittement_date_declaration.strftime('%d/%m/%Y') if m.acquittement_date_declaration else 'N/A'}."
        )
        Notification.objects.create(
            marketeur=m.marketeur, type_notif='ACQUITTEMENT', mouvement=m,
            titre=titre, message=message,
        )
        _envoyer_email_mouvement(m.marketeur, m)


def _envoyer_email_mouvement(marketeur, mouvement):
    """Envoi (PDF en pièce jointe) du document d'un mouvement, dès sa
    création, via le gabarit ModeleEmailMouvement + la configuration SMTP
    stockée en base. Best-effort : ne lève jamais — un échec ici ne doit
    jamais empêcher la création du mouvement.
    L'envoi (rendu PDF navigateur + SMTP, plusieurs secondes) est différé
    après commit de la transaction — pour ne jamais envoyer l'email d'un
    mouvement rollbacké — puis exécuté dans un thread pour ne pas bloquer
    la requête de l'opérateur."""
    import logging
    import threading

    def _envoyer():
        from SGDS.models import ConfigurationEmail
        from SGDS.services.email_mouvement import envoyer_email_mouvement

        try:
            config = ConfigurationEmail.get_instance()
            if not config.actif or not config.host_user:
                return
            envoyer_email_mouvement(marketeur, mouvement, config)
        except Exception:
            logging.getLogger(__name__).exception(
                "Échec de l'envoi de l'email pour le mouvement %s", getattr(mouvement, 'numero_enregistrement', mouvement.pk)
            )

    transaction.on_commit(
        lambda: threading.Thread(target=_envoyer, daemon=True).start()
    )


# ── Notifications États Mensuels ─────────────────────────────

@receiver(pre_save, sender='SGDS.PeriodeComptable')
def on_periode_pre_save(sender, instance, **kwargs):
    """Mémorise l'ancien statut pour détecter le passage à CLOTUREE."""
    if instance.pk:
        try:
            from SGDS.models import PeriodeComptable
            old = PeriodeComptable.objects.filter(pk=instance.pk).values('statut').first()
            instance._statut_precedent = old['statut'] if old else None
        except Exception:
            instance._statut_precedent = None
    else:
        instance._statut_precedent = None


@receiver(post_save, sender='SGDS.PeriodeComptable')
def on_periode_cloturee_notif(sender, instance, created, **kwargs):
    """
    Quand une PériodeComptable passe à CLOTUREE, crée une notification
    ETAT_MENSUEL_DISPONIBLE pour chaque marketeur actif ayant eu des mouvements
    sur cette période.
    """
    if created:
        return
    statut_prec = getattr(instance, '_statut_precedent', None)
    if statut_prec == 'CLOTUREE' or instance.statut != 'CLOTUREE':
        return

    try:
        from SGDS.models import Notification, Marketeur, Mouvement

        date_debut = instance.date_debut
        date_fin = instance.date_fin

        marketeur_ids = (
            Mouvement.objects
            .filter(depot=instance.depot,
                    date_mouvement__gte=date_debut, date_mouvement__lte=date_fin)
            .values_list('marketeur_id', flat=True)
            .distinct()
        )
        marketeurs = list(Marketeur.objects.filter(pk__in=marketeur_ids, statut='ACTIF'))

        from django.urls import reverse
        lien = (
            f"{reverse('client_mensuel_stock_15')}?mois={instance.mois}&annee={instance.annee}"
        )
        titre = f"États mensuels disponibles — {instance.mois:02d}/{instance.annee}"
        message = (
            f"Les états mensuels pour la période {instance.libelle} sont maintenant "
            f"disponibles : stock mensuel, répartition du coulage et frais de passage."
        )

        # Savepoint dédié : une erreur DB ici (ex. contrainte) ne doit pas
        # casser la transaction englobante (ex. cloturer_periode()).
        with transaction.atomic():
            for mkt in marketeurs:
                Notification.objects.create(
                    marketeur=mkt,
                    type_notif='ETAT_MENSUEL_DISPONIBLE',
                    titre=titre,
                    message=message,
                    lien=lien,
                )

        # Email optionnel si backend SMTP configuré
        _envoyer_email_etats_mensuels(marketeurs, instance, titre, message)

    except Exception:
        pass


def _envoyer_email_etats_mensuels(marketeurs, periode, sujet_notif, message_notif):
    """Envoi du bundle d'états mensuels (stock ouverture/fermeture, coulage
    répartition, frais de passage) en pièces jointes Excel + PDF, via
    SGDS.services.etat_mensuel_envoi. Chaque marketeur a sa propre gestion
    d'erreur interne (EnvoiEtatMensuel) — ne dépend pas du try/except
    englobant de on_periode_cloturee_notif.
    Différé après commit de la clôture puis exécuté dans un thread : la
    génération (M marketeurs × ~12 pièces jointes PDF/Excel + SMTP) prend
    plusieurs minutes et ne doit pas bloquer la requête de clôture."""
    import threading

    def _envoyer():
        from SGDS.models import ConfigurationEmail
        from SGDS.services.etat_mensuel_envoi import envoyer_etat_mensuel_marketeur

        config = ConfigurationEmail.get_instance()
        if not config.actif or not config.host_user:
            return
        for mkt in marketeurs:
            envoyer_etat_mensuel_marketeur(periode, mkt, config)

    transaction.on_commit(
        lambda: threading.Thread(target=_envoyer, daemon=True).start()
    )
