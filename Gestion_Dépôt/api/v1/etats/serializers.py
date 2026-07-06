"""
Serializers pour les états — noms alignés sur le contrat mobile.
"""
from decimal import Decimal

from rest_framework import serializers

D = {'max_digits': 14, 'decimal_places': 3}


# ── Carte de stock ────────────────────────────────────────────────

class StockGlobalLigneSerializer(serializers.Serializer):
    date             = serializers.DateField()
    reference        = serializers.CharField(allow_null=True, allow_blank=True)
    type             = serializers.CharField()
    entree_ambiant   = serializers.DecimalField(**D)
    entree_15        = serializers.DecimalField(**D)
    sortie_ambiant   = serializers.DecimalField(**D)
    sortie_15        = serializers.DecimalField(**D)
    stock_ambiant    = serializers.DecimalField(**D)
    stock_15         = serializers.DecimalField(**D)


class StockGlobalResponseSerializer(serializers.Serializer):
    # Contexte (nouveaux champs)
    marketeur_nom           = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    produit_id              = serializers.IntegerField(allow_null=True, required=False)
    produit_nom             = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    produit_sigle           = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    periode_id              = serializers.IntegerField(allow_null=True, required=False)
    periode_nom             = serializers.CharField(allow_blank=True, required=False)
    # Données
    stock_ouverture_ambiant = serializers.DecimalField(**D)
    lignes                  = StockGlobalLigneSerializer(many=True)
    cumul_entrees_ambiant   = serializers.DecimalField(**D)
    cumul_entrees_15        = serializers.DecimalField(**D)
    cumul_sorties_ambiant   = serializers.DecimalField(**D)
    cumul_sorties_15        = serializers.DecimalField(**D)
    stock_final_ambiant     = serializers.DecimalField(**D)
    stock_final_15          = serializers.DecimalField(**D)


# ── Récapitulatif par produit ─────────────────────────────────────

class RecapProduitSerializer(serializers.Serializer):
    produit_id               = serializers.IntegerField()
    produit_nom              = serializers.CharField()
    produit_sigle            = serializers.CharField()
    nb_entrees               = serializers.IntegerField()
    volume_entree_ambiant    = serializers.DecimalField(**D)
    volume_entree_15         = serializers.DecimalField(**D)
    nb_sorties               = serializers.IntegerField()
    volume_sortie_ambiant    = serializers.DecimalField(**D)
    nb_cessions              = serializers.IntegerField()
    volume_cession_ambiant   = serializers.DecimalField(**D)
    nb_acquittements         = serializers.IntegerField()
    volume_acquit_ambiant    = serializers.DecimalField(**D)
    stock_ouverture_ambiant  = serializers.DecimalField(**D, required=False, default=Decimal('0'))
    stock_final_ambiant      = serializers.DecimalField(**D)


class RecapTotauxSerializer(serializers.Serializer):
    nb_mouvements            = serializers.IntegerField()
    nb_entrees               = serializers.IntegerField()
    volume_entree_ambiant    = serializers.DecimalField(**D)
    nb_sorties               = serializers.IntegerField()
    volume_sortie_ambiant    = serializers.DecimalField(**D)
    nb_cessions              = serializers.IntegerField()
    volume_cession_ambiant   = serializers.DecimalField(**D)
    nb_acquittements         = serializers.IntegerField()
    volume_acquit_ambiant    = serializers.DecimalField(**D)
    stock_ouverture_ambiant  = serializers.DecimalField(**D, required=False, default=Decimal('0'))
    stock_final_ambiant      = serializers.DecimalField(**D)


class RecapSerializer(serializers.Serializer):
    marketeur_nom            = serializers.CharField()
    periode_id               = serializers.IntegerField(allow_null=True, required=False)
    periode_nom              = serializers.CharField(allow_blank=True, required=False)
    par_produit              = RecapProduitSerializer(many=True)
    totaux                   = RecapTotauxSerializer()


# ── Référentiels ──────────────────────────────────────────────────

class ProduitDispoSerializer(serializers.Serializer):
    id     = serializers.IntegerField()
    nom    = serializers.CharField()
    sigle  = serializers.CharField(allow_null=True, allow_blank=True)


class PeriodeSerializer(serializers.Serializer):
    id     = serializers.IntegerField()
    nom    = serializers.CharField()
    statut = serializers.CharField()
    mois   = serializers.IntegerField()
    annee  = serializers.IntegerField()
    # Les périodes sont par dépôt (champs additifs — rétrocompatibles)
    depot_id  = serializers.IntegerField(allow_null=True, required=False)
    depot_nom = serializers.CharField(allow_blank=True, required=False)


# ── Stock Ouverture / Fermeture ────────────────────────────────────

class StockOuvertureLigneSerializer(serializers.Serializer):
    produit_id        = serializers.IntegerField()
    produit_nom       = serializers.CharField()
    produit_sigle     = serializers.CharField()
    stock_ouverture   = serializers.DecimalField(**D)
    entrees           = serializers.DecimalField(**D)
    sorties           = serializers.DecimalField(**D)
    stock_fermeture   = serializers.DecimalField(**D)


class StockOuvertureResponseSerializer(serializers.Serializer):
    marketeur_nom   = serializers.CharField()
    periode_id      = serializers.IntegerField(allow_null=True)
    periode_nom     = serializers.CharField(allow_blank=True)
    lignes          = StockOuvertureLigneSerializer(many=True)
    total_ouverture = serializers.DecimalField(**D)
    total_entrees   = serializers.DecimalField(**D)
    total_sorties   = serializers.DecimalField(**D)
    total_fermeture = serializers.DecimalField(**D)


# ── Frais de Passage ───────────────────────────────────────────────

class FraisPassageProduitSerializer(serializers.Serializer):
    produit_id    = serializers.IntegerField()
    produit_nom   = serializers.CharField()
    produit_sigle = serializers.CharField()
    prix_passage  = serializers.DecimalField(**D)
    is_global     = serializers.BooleanField()


class FraisPassageResponseSerializer(serializers.Serializer):
    tarif_global      = serializers.DecimalField(**D)
    date_application  = serializers.CharField(allow_blank=True)
    periode_id        = serializers.IntegerField(allow_null=True, required=False)
    periode_nom       = serializers.CharField(allow_blank=True, required=False)
    produits          = FraisPassageProduitSerializer(many=True)


# ── Coulage des marketeurs ─────────────────────────────────────────

class CoulageLigneSerializer(serializers.Serializer):
    periode_id    = serializers.IntegerField()
    periode_nom   = serializers.CharField()
    produit_id    = serializers.IntegerField(allow_null=True)
    produit_nom   = serializers.CharField(allow_blank=True)
    produit_sigle = serializers.CharField(allow_blank=True)
    brut_entree   = serializers.DecimalField(**D)
    coul_entree   = serializers.DecimalField(**D)
    entree_nette  = serializers.DecimalField(**D)
    sortie        = serializers.DecimalField(**D)
    qp_coul       = serializers.DecimalField(**D)
    volume_sorti  = serializers.DecimalField(**D)
    prix_unitaire = serializers.DecimalField(**D)
    montant       = serializers.DecimalField(**D)
    motif         = serializers.CharField(allow_blank=True)


class CoulageResponseSerializer(serializers.Serializer):
    marketeur_nom       = serializers.CharField()
    lignes              = CoulageLigneSerializer(many=True)
    total_montant       = serializers.DecimalField(**D)
    total_volume_sorti  = serializers.DecimalField(**D)
