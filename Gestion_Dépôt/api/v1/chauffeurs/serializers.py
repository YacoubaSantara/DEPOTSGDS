"""
Serializers Chauffeur pour l'API mobile.
"""
from rest_framework import serializers

from SGDS.models import Camion, Chauffeur


class ChauffeurSerializer(serializers.ModelSerializer):
    camion = serializers.PrimaryKeyRelatedField(
        queryset=Camion.objects.none(), required=False, allow_null=True,
    )
    camion_immatriculation = serializers.SerializerMethodField()

    class Meta:
        model  = Chauffeur
        fields = [
            'id', 'uuid', 'nom', 'prenom', 'telephone', 'telephone2', 'email',
            'numero_permis', 'categorie_permis', 'numero_employe',
            'statut', 'camion', 'camion_immatriculation', 'date_embauche', 'notes',
        ]
        read_only_fields = ['id', 'uuid', 'numero_employe']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request is not None:
            marketeur = getattr(request.user, 'marketeur', None)
            self.fields['camion'].queryset = Camion.objects.filter(marketeur=marketeur)

    def get_camion_immatriculation(self, obj):
        return obj.camion.immatriculation if obj.camion_id else None

    def create(self, validated_data):
        if not validated_data.get('numero_employe'):
            validated_data['numero_employe'] = Chauffeur.get_next_numero()
        return Chauffeur.objects.create(**validated_data)
