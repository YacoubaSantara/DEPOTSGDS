"""
Serializers mouvements — noms de champs alignés sur le contrat mobile.
"""
from rest_framework import serializers

D = {'max_digits': 14, 'decimal_places': 3, 'allow_null': True}


class MouvementListSerializer(serializers.Serializer):
    id               = serializers.IntegerField()
    reference        = serializers.CharField(allow_null=True, allow_blank=True)
    type             = serializers.CharField()
    produit_id       = serializers.IntegerField()
    produit          = serializers.CharField()
    produit_sigle    = serializers.CharField(allow_null=True, allow_blank=True)
    regime           = serializers.CharField(allow_null=True)
    date             = serializers.DateField()
    quantite_ambiant = serializers.DecimalField(**D)
    quantite_15      = serializers.DecimalField(**D)
    observation      = serializers.CharField(allow_null=True, allow_blank=True)


class MouvementDetailSerializer(MouvementListSerializer):
    # Entrée
    provenance                = serializers.CharField(allow_null=True)
    bl_expediteur             = serializers.CharField(allow_null=True)
    bl_client                 = serializers.CharField(allow_null=True)
    date_chargement           = serializers.DateField(allow_null=True)
    date_dechargement         = serializers.DateField(allow_null=True)
    volume_ambiant_expediteur = serializers.DecimalField(**D)
    volume_ambiant_recu       = serializers.DecimalField(**D)
    volume_15c_recu           = serializers.DecimalField(**D)
    perte_gain_reception      = serializers.DecimalField(**D)
    camion_immatriculation    = serializers.CharField(allow_null=True)
    chauffeur_nom             = serializers.CharField(allow_null=True)

    # Sortie
    destination               = serializers.CharField(allow_null=True)
    numero_permis_sortie      = serializers.CharField(allow_null=True)
    volume_ambiant_sortie     = serializers.DecimalField(**D)
    volume_15c_sortie         = serializers.DecimalField(**D)
    mode_reglement            = serializers.CharField(allow_null=True)

    # Cession
    cession_destinataire      = serializers.CharField(allow_null=True)
    cession_volume_ambiant    = serializers.DecimalField(**D)
    cession_volume_15c        = serializers.DecimalField(**D)
    cession_motif             = serializers.CharField(allow_null=True)

    # Acquittement
    acquittement_volume_ambiant        = serializers.DecimalField(**D)
    acquittement_reference_declaration = serializers.CharField(allow_null=True)
    acquittement_date_declaration      = serializers.DateField(allow_null=True)


class MouvementListResponseSerializer(serializers.Serializer):
    count       = serializers.IntegerField()
    page        = serializers.IntegerField()
    page_size   = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    results     = MouvementListSerializer(many=True)
