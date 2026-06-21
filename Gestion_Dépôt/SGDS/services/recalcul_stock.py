"""
Service de recalcul des stocks cuves et produits.

DEUX MÉTRIQUES DISTINCTES :
  - Cuve.niveau_actuel   : STOCK PHYSIQUE  = dernier jaugeage validé + mouvements après.
                           Sert à l'affichage par cuve et au calcul des Pertes/Gains.
  - Produit.stock_actuel : STOCK COMPTABLE = inventaire_initial + Σ(ENTREE) − Σ(SORTIE).
                           Utilise Mouvement.volume_ambiant_recu / volume_ambiant_sortie,
                           même source que _calculer_stock_global (carte de stock global).
                           ACQUITTEMENT et CESSION n'ont pas d'impact physique global.

Règles du stock comptable (Produit.stock_actuel) :
  - ENTREE      → +volume_ambiant_recu
  - SORTIE      → −volume_ambiant_sortie
  - ACQUITTEMENT→ 0  (transfert SD↔AC interne)
  - CESSION     → 0  (transfert M1→M2, bilan global nul)

Pertes/Gains = Σ(Cuve.niveau_actuel) − Produit.stock_actuel
  → Visible dans l'état stock ouverture/fermeture mensuel.
"""
from decimal import Decimal


def _delta_lignes(lignes_qs):
    """
    Calcule le delta de volume ambiant pour un queryset de LigneMouvement.
    ENTREE → positif, SORTIE → négatif.
    ACQUITTEMENT et CESSION n'ont pas d'impact physique.
    """
    delta = Decimal('0')
    for ligne in lignes_qs:
        vol = Decimal(str(ligne.volume_ambiant)) if ligne.volume_ambiant is not None else Decimal('0')
        type_mvt = ligne.mouvement.type_mouvement
        if type_mvt == 'ENTREE':
            delta += vol
        elif type_mvt == 'SORTIE':
            delta -= vol
        # ACQUITTEMENT : l'ENTREE SOUS_DOUANE est déjà comptée — pas d'impact physique
        # CESSION : mouvement comptable uniquement
    return delta


def recalculer_stock_cuve(cuve):
    """
    Recalcule Cuve.niveau_actuel :
      1. Part du volume de la dernière MesureCuve VALIDÉE (jaugeage physique).
      2. Ajoute les volumes ENTREE (ACQUITTE et SOUS_DOUANE),
         soustrait les volumes SORTIE des LigneMouvement postérieures
         à ce jaugeage.
         NB : ACQUITTEMENT non ajouté car l'ENTREE SOUS_DOUANE est déjà comptée.
    Si aucun jaugeage validé : niveau_actuel = 0.
      La distribution par cuve est inconnue sans jaugeage ; c'est
      recalculer_stock_produit qui porte le total via l'inventaire global.

    Filtre temporel selon le type de jaugeage :
      - AVR (avant livraison) : les mouvements du MÊME jour sont inclus (__gte)
        car le jaugeage est pris avant les opérations du jour.
      - APR (après) / J (normal) : les mouvements du même jour sont exclus (__gt)
        car le jaugeage capture déjà l'état en fin de journée.
    """
    from SGDS.models import MesureCuve, LigneMouvement

    # ── 1. Dernière mesure de jaugeage VALIDÉE ────────────────────────
    mesure = (
        MesureCuve.objects
        .filter(cuve=cuve, jaugeage__est_valide=True)
        .select_related('jaugeage', 'cuve__parametre_jaugeage')
        .order_by(
            '-jaugeage__date_jaugeage',
            '-jaugeage__heure_jaugeage',
            '-jaugeage__date_creation',
        )
        .first()
    )

    if mesure is None:
        # Aucun jaugeage validé : distribution par cuve inconnue → niveau à 0.
        # recalculer_stock_produit utilise l'inventaire global directement dans ce cas.
        base_volume   = Decimal('0')
        date_jaugeage = None
        type_jaugeage = None
    else:
        v = mesure.volume_ambiant_depot  # @property calculée
        base_volume   = Decimal(str(v)) if v is not None else Decimal('0')
        date_jaugeage = mesure.jaugeage.date_jaugeage
        type_jaugeage = mesure.jaugeage.type_jaugeage   # Fix #4 : conserver le type

    # ── 2. Mouvements depuis ce jaugeage ──────────────────────
    lignes_qs = (
        LigneMouvement.objects
        .filter(cuve=cuve)
        .select_related('mouvement')
    )
    if mesure is not None:
        # Filtre basé sur le DATETIME de validation du jaugeage :
        # on inclut uniquement les mouvements CRÉÉS après la validation.
        # Cela évite d'exclure des mouvements saisis le même jour que le jaugeage
        # mais APRÈS sa validation (problème avec le filtre date seul).
        date_validation = mesure.jaugeage.date_validation
        if date_validation is not None:
            lignes_qs = lignes_qs.filter(
                mouvement__date_saisie__gt=date_validation
            )
        else:
            # Fallback si date_validation absente (jaugeage non encore validé)
            if type_jaugeage == 'AVR':
                lignes_qs = lignes_qs.filter(mouvement__date_mouvement__gte=date_jaugeage)
            else:
                lignes_qs = lignes_qs.filter(mouvement__date_mouvement__gt=date_jaugeage)

    delta = Decimal('0')
    for ligne in lignes_qs:
        vol      = Decimal(str(ligne.volume_ambiant)) if ligne.volume_ambiant is not None else Decimal('0')
        type_mvt = ligne.mouvement.type_mouvement
        # Fix #5 : suppression de `regime = ligne.mouvement.regime_douanier` (dead code)

        if type_mvt == 'ENTREE':
            # Entrée physique dans la cuve (acquitté ou sous douane)
            delta += vol
        elif type_mvt == 'ACQUITTEMENT':
            # L'ENTREE SOUS_DOUANE est déjà comptée : pas d'impact physique
            pass
        elif type_mvt == 'SORTIE':
            delta -= vol
        # CESSION : mouvement comptable uniquement, pas d'impact stock physique

    cuve.niveau_actuel = base_volume + delta
    cuve.save(update_fields=['niveau_actuel'])


def recalculer_stock_produit(produit):
    """
    Recalcule Produit.stock_actuel selon deux cas :

    Cas 1 — Aucun jaugeage validé :
      stock = Σ(inventaires_initiaux) + Σ(ENTREE: volume_ambiant_recu)
                                       − Σ(SORTIE: volume_ambiant_sortie)
      Formule comptable pure, identique à _calculer_stock_global.

    Cas 2 — Jaugeage validé présent :
      stock = Σ(Cuve.niveau_actuel)
            + delta des LigneMouvement SANS cuve APRÈS le dernier jaugeage.

      Cuve.niveau_actuel = dernier jaugeage + mouvements après jaugeage
      (calculé par recalculer_stock_cuve).

      Les LigneMouvement sans cuve AVANT le jaugeage ne sont PAS ajoutées :
      le jaugeage physique les a déjà capturées dans la mesure des cuves.
      Seules les lignes APRÈS le jaugeage (non encore mesurées) sont intégrées.

      → Après validation d'un jaugeage APR/J (end-of-day) :
          Cuve.niveau_actuel = valeur jaugée (aucun mouvement postérieur)
          stock_actuel       = Σ(valeurs jaugées) = stock de fermeture du jour.

    Pertes/Gains = stock_actuel (physique) vs stock comptable
                 → visible dans l'état stock ouverture/fermeture mensuel.

    Sauvegarde (update_fields=['stock_actuel', 'date_maj_stock']).
    """
    from django.db.models import Sum
    from django.utils import timezone
    from SGDS.models import Cuve, InventaireInitialMarketeur, MesureCuve, LigneMouvement, Mouvement

    # ── Chercher le dernier jaugeage validé pour ce produit ──────────────
    derniere_mesure = (
        MesureCuve.objects
        .filter(cuve__produit=produit, jaugeage__est_valide=True)
        .select_related('jaugeage', 'cuve__parametre_jaugeage')
        .order_by(
            '-jaugeage__date_jaugeage',
            '-jaugeage__heure_jaugeage',
            '-jaugeage__date_creation',
        )
        .first()
    )

    if derniere_mesure is None:
        # ── Cas 1 : aucun jaugeage → formule comptable (Mouvement headers) ──
        total_inv = (
            InventaireInitialMarketeur.objects
            .filter(produit=produit)
            .aggregate(s=Sum('volume_ambiant'))['s']
        ) or Decimal('0')
        delta = Decimal('0')
        for mouv in Mouvement.objects.filter(produit=produit):
            if mouv.type_mouvement == 'ENTREE':
                delta += Decimal(str(mouv.volume_ambiant_recu or 0))
            elif mouv.type_mouvement == 'SORTIE':
                delta -= Decimal(str(mouv.volume_ambiant_sortie or 0))
        total = Decimal(str(total_inv)) + delta

    else:
        # ── Cas 2 : jaugeage présent → formule physique ───────────────────
        # stock = Σ(Cuve.niveau_actuel) + lignes sans cuve APRÈS jaugeage
        total_cuves = (
            Cuve.objects
            .filter(produit=produit)
            .aggregate(s=Sum('niveau_actuel'))['s']
        ) or Decimal('0')

        # Même logique que recalculer_stock_cuve : filtre sur datetime de validation
        date_validation_j = derniere_mesure.jaugeage.date_validation
        date_j            = derniere_mesure.jaugeage.date_jaugeage
        type_j            = derniere_mesure.jaugeage.type_jaugeage

        lignes_sans_cuve = LigneMouvement.objects.filter(
            produit=produit,
            cuve__isnull=True,
        ).select_related('mouvement')

        if date_validation_j is not None:
            # Mouvements créés APRÈS la validation du jaugeage → non capturés par lui
            lignes_sans_cuve = lignes_sans_cuve.filter(
                mouvement__date_saisie__gt=date_validation_j
            )
        else:
            # Fallback date si date_validation absente
            if type_j == 'AVR':
                lignes_sans_cuve = lignes_sans_cuve.filter(
                    mouvement__date_mouvement__gte=date_j
                )
            else:
                lignes_sans_cuve = lignes_sans_cuve.filter(
                    mouvement__date_mouvement__gt=date_j
                )

        total = Decimal(str(total_cuves)) + _delta_lignes(lignes_sans_cuve)

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
