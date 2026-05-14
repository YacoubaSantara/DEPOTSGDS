"""
Serializers pour le profil utilisateur.
"""
from rest_framework import serializers


class ProfilSerializer(serializers.Serializer):
    """Profil complet de l'utilisateur connecté."""
    id             = serializers.IntegerField()
    username       = serializers.CharField()
    full_name      = serializers.CharField()
    email          = serializers.EmailField(allow_blank=True)
    telephone      = serializers.CharField(allow_null=True)
    poste          = serializers.CharField(allow_null=True)
    date_joined    = serializers.DateTimeField()
    derniere_ip    = serializers.CharField(allow_null=True)
    marketeur_id         = serializers.IntegerField(allow_null=True)
    marketeur_nom        = serializers.CharField(allow_null=True)
    marketeur_sigle      = serializers.CharField(allow_null=True)
    photo_url            = serializers.CharField(allow_null=True)
    total_mouvements     = serializers.IntegerField()
    volume_total_ambiant = serializers.FloatField()


class UpdateProfilSerializer(serializers.Serializer):
    """Champs modifiables du profil."""
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name  = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email      = serializers.EmailField(required=False, allow_blank=True)
    telephone  = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Changement de mot de passe."""
    ancien_mot_de_passe  = serializers.CharField(write_only=True)
    nouveau_mot_de_passe = serializers.CharField(write_only=True, min_length=8)
    confirmation         = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['nouveau_mot_de_passe'] != attrs['confirmation']:
            raise serializers.ValidationError(
                {'confirmation': 'Les deux mots de passe ne correspondent pas.'}
            )
        return attrs
