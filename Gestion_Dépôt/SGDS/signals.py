"""
Signaux Django pour mise à jour automatique des stocks cuves/produits.
Chargés via SgdsConfig.ready() dans apps.py.
"""
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from SGDS.models import JaugeageJour, MesureCuve, Mouvement, LigneMouvement, InventaireInitialMarketeur
from SGDS.services.recalcul_stock import (
    recalculer_stock_cuve,
    recalculer_stock_produit,
    recalculer_tous_stocks,
)


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
    """
    if instance.cuve:
        recalculer_stock_cuve(instance.cuve)
        if instance.cuve.produit:
            recalculer_stock_produit(instance.cuve.produit)


# ── Inventaire Initial Marketeur ────────────────────────────

@receiver(post_save, sender=InventaireInitialMarketeur)
def on_inventaire_initial_saved(sender, instance, **kwargs):
    """
    Recalcule Produit.stock_actuel dès qu'un inventaire initial est saisi ou modifié.
    Les cuves associées sont recalculées via le signal m2m_changed (ci-dessous).
    """
    recalculer_stock_produit(instance.produit)


@receiver(post_delete, sender=InventaireInitialMarketeur)
def on_inventaire_initial_deleted(sender, instance, **kwargs):
    """Recalcule Produit.stock_actuel et les cuves associées après suppression."""
    try:
        for cuve in instance.cuves.all():
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
        from SGDS.models import Cuve
        # Recalculer les cuves actuellement liées
        for cuve in instance.cuves.all():
            recalculer_stock_cuve(cuve)
        # Recalculer également les cuves qui viennent d'être retirées (pk_set)
        if pk_set:
            for cuve in Cuve.objects.filter(pk__in=pk_set):
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
