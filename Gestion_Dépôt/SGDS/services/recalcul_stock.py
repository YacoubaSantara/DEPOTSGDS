"""
Service de recalcul des stocks cuves et produits.

Règles régimes douaniers :
  - ENTREE  ACQUITTE    → s'ajoute au stock (vol positif)
  - ENTREE  SOUS_DOUANE → ne s'ajoute PAS au stock (marchandise sous contrôle douanier)
  - ACQUITTEMENT        → s'ajoute au stock (la douane libère le produit)
  - SORTIE              → soustrait du stock
  - CESSION             → mouvement comptable uniquement, pas de stock physique

Pour les inventaires initiaux marketeurs :
  - Régime ACQUITTE    → compté dans le stock de base
  - Régime SOUS_DOUANE → exclu du stock de base (en attente d'acquittement)
"""
from decimal import Decimal


def recalculer_stock_cuve(cuve):
    """
    Recalcule Cuve.niveau_actuel :
      1. Part du volume de la dernière MesureCuve (jaugeage physique).
      2. Ajoute les volumes ENTREE ACQUITTE et ACQUITTEMENT,
         soustrait les volumes SORTIE des LigneMouvement postérieures
         à ce jaugeage.
         Les ENTREE SOUS_DOUANE sont ignorées (stock non libéré par la douane).
    Si aucun jaugeage : base = somme des InventaireInitialMarketeur ACQUITTE
    associés à cette cuve.
    """
    from SGDS.models import MesureCuve, LigneMouvement

    # ── 1. Dernière mesure de jaugeage ────────────────────────
    mesure = (
        MesureCuve.objects
        .filter(cuve=cuve)
        .select_related('jaugeage', 'cuve__parametre_jaugeage')
        .order_by(
            '-jaugeage__date_jaugeage',
            '-jaugeage__heure_jaugeage',
            '-jaugeage__date_creation',
        )
        .first()
    )

    if mesure is None:
        # Aucun jaugeage : base = somme des inventaires initiaux ACQUITTÉS associés à cette cuve
        # Les inventaires SOUS_DOUANE sont exclus (en attente d'acquittement douanier)
        from SGDS.models import InventaireInitialMarketeur
        from django.db.models import Sum as _Sum
        inv_total = (
            InventaireInitialMarketeur.objects
            .filter(cuves=cuve, regime_douanier='ACQUITTE')
            .aggregate(s=_Sum('volume_ambiant'))['s']
        ) or Decimal('0')
        base_volume   = Decimal(str(inv_total))
        date_jaugeage = None
    else:
        v = mesure.volume_ambiant_depot  # @property calculée
        base_volume   = Decimal(str(v)) if v is not None else Decimal('0')
        date_jaugeage = mesure.jaugeage.date_jaugeage

    # ── 2. Mouvements depuis ce jaugeage ──────────────────────
    lignes_qs = (
        LigneMouvement.objects
        .filter(cuve=cuve)
        .select_related('mouvement')
    )
    if date_jaugeage is not None:
        # Mouvements STRICTEMENT postérieurs au jaugeage
        # (le jaugeage capture déjà l'état physique à cette date)
        lignes_qs = lignes_qs.filter(mouvement__date_mouvement__gt=date_jaugeage)

    delta = Decimal('0')
    for ligne in lignes_qs:
        vol      = Decimal(str(ligne.volume_ambiant)) if ligne.volume_ambiant is not None else Decimal('0')
        type_mvt = ligne.mouvement.type_mouvement
        regime   = ligne.mouvement.regime_douanier

        if type_mvt == 'ENTREE' and regime == 'ACQUITTE':
            # Entrée en régime acquitté → stock disponible immédiatement
            delta += vol
        elif type_mvt == 'ENTREE' and regime == 'SOUS_DOUANE':
            # Entrée sous douane → produit reçu physiquement mais stock bloqué
            # Le stock sera libéré uniquement lors de l'ACQUITTEMENT
            pass
        elif type_mvt == 'ACQUITTEMENT':
            # Acquittement → la douane libère le produit : s'ajoute au stock
            delta += vol
        elif type_mvt == 'SORTIE':
            delta -= vol
        # CESSION : mouvement comptable uniquement, pas d'impact stock physique

    cuve.niveau_actuel = base_volume + delta
    cuve.save(update_fields=['niveau_actuel'])


def recalculer_stock_produit(produit):
    """
    Recalcule Produit.stock_actuel :
      1. Σ niveau_actuel de toutes les cuves du produit (basé sur jaugeages + mouvements).
      2. Si aucune cuve n'a encore de jaugeage (total cuves = 0), on prend en base
         la somme des InventaireInitialMarketeur ACQUITTÉS pour ce produit.
         Les inventaires SOUS_DOUANE sont exclus (stock non libéré par la douane).
    Sauvegarde (update_fields=['stock_actuel', 'date_maj_stock']).
    """
    from django.db.models import Sum
    from django.utils import timezone
    from SGDS.models import Cuve, InventaireInitialMarketeur

    total_cuves = (
        Cuve.objects
        .filter(produit=produit)
        .aggregate(s=Sum('niveau_actuel'))['s']
    ) or Decimal('0')

    if total_cuves == Decimal('0'):
        # Aucun jaugeage physique enregistré → on utilise les inventaires initiaux
        # ACQUITTÉS des marketeurs comme stock de référence de départ.
        # Les inventaires SOUS_DOUANE ne sont pas comptabilisés ici :
        # ils seront ajoutés au stock lors de leur acquittement.
        total_inv = (
            InventaireInitialMarketeur.objects
            .filter(produit=produit, regime_douanier='ACQUITTE')
            .aggregate(s=Sum('volume_ambiant'))['s']
        ) or Decimal('0')
        total = Decimal(str(total_inv))
    else:
        total = Decimal(str(total_cuves))

    produit.stock_actuel   = total
    produit.date_maj_stock = timezone.now()
    produit.save(update_fields=['stock_actuel', 'date_maj_stock'])


def recalculer_tous_stocks():
    """
    Recalcule toutes les cuves puis tous les produits.
    Appelée après suppression d'un JaugeageJour ou d'un Mouvement massif.
    """
    from SGDS.models import Cuve, Produit

    for cuve in Cuve.objects.select_related('parametre_jaugeage').all():
        recalculer_stock_cuve(cuve)

    for produit in Produit.objects.all():
        recalculer_stock_produit(produit)
