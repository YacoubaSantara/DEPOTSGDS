"""
Serializers Camion pour l'API mobile.
"""
from rest_framework import serializers

from SGDS.models import Camion, CompartimentCamion


class CompartimentCamionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CompartimentCamion
        fields = ['id', 'numero', 'capacite']


class CamionSerializer(serializers.ModelSerializer):
    compartiments = CompartimentCamionSerializer(many=True, required=False)

    class Meta:
        model  = Camion
        fields = [
            'id', 'uuid', 'immatriculation', 'marque', 'modele',
            'capacite_totale', 'nombre_compartiments', 'type_produit',
            'statut', 'notes', 'compartiments',
            'date_enregistrement', 'date_modification',
        ]
        read_only_fields = ['id', 'uuid', 'date_enregistrement', 'date_modification']

    def create(self, validated_data):
        compartiments = validated_data.pop('compartiments', [])
        camion = Camion.objects.create(**validated_data)
        self._sync_compartiments(camion, compartiments)
        return camion

    def update(self, instance, validated_data):
        compartiments = validated_data.pop('compartiments', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if compartiments is not None:
            self._sync_compartiments(instance, compartiments)
        return instance

    def _sync_compartiments(self, camion, compartiments):
        camion.compartiments.all().delete()
        CompartimentCamion.objects.bulk_create([
            CompartimentCamion(camion=camion, numero=c['numero'], capacite=c['capacite'])
            for c in compartiments
        ])
