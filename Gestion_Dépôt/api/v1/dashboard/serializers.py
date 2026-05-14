"""
Serializers pour le tableau de bord marketeur.
Noms de champs alignés sur le contrat mobile.
"""
from rest_framework import serializers


class StockProduitSerializer(serializers.Serializer):
    produit_id      = serializers.IntegerField()
    produit_nom     = serializers.CharField()
    produit_sigle   = serializers.CharField(allow_null=True, allow_blank=True)
    stock_ambiant   = serializers.DecimalField(max_digits=14, decimal_places=3)
    stock_15        = serializers.DecimalField(max_digits=14, decimal_places=3)
    sd_ambiant      = serializers.DecimalField(max_digits=14, decimal_places=3)
    ac_ambiant      = serializers.DecimalField(max_digits=14, decimal_places=3)
    sd_15           = serializers.DecimalField(max_digits=14, decimal_places=3)
    ac_15           = serializers.DecimalField(max_digits=14, decimal_places=3)
    total           = serializers.DecimalField(max_digits=14, decimal_places=3)
    capacite        = serializers.DecimalField(max_digits=14, decimal_places=3)


class DernierMouvementSerializer(serializers.Serializer):
    id               = serializers.IntegerField()
    type             = serializers.CharField()
    date             = serializers.DateField()
    produit          = serializers.CharField()
    quantite_ambiant = serializers.DecimalField(max_digits=14, decimal_places=3, allow_null=True)
    quantite_15      = serializers.DecimalField(max_digits=14, decimal_places=3, allow_null=True)
    reference        = serializers.CharField(allow_null=True, allow_blank=True)


class DashboardSerializer(serializers.Serializer):
    marketeur_nom        = serializers.CharField()
    stocks               = StockProduitSerializer(many=True)
    derniers_mouvements  = DernierMouvementSerializer(many=True)
    total_mouvements     = serializers.IntegerField()
    total_entrees        = serializers.DecimalField(max_digits=14, decimal_places=3)
    total_sorties        = serializers.DecimalField(max_digits=14, decimal_places=3)
    nb_entrees           = serializers.IntegerField()
    nb_sorties           = serializers.IntegerField()
    taux_remplissage     = serializers.FloatField()
    total_ambiant_hier   = serializers.DecimalField(max_digits=14, decimal_places=3)
    delta_hier           = serializers.FloatField()
