"""
Serializers pour l'authentification JWT.
"""
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        write_only=True,
        help_text="Nom d'utilisateur"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Mot de passe"
    )

    def validate(self, attrs):
        username = attrs.get('username', '').strip()
        password = attrs.get('password', '')

        if not username or not password:
            raise serializers.ValidationError(
                _("Le nom d'utilisateur et le mot de passe sont obligatoires.")
            )

        user = authenticate(
            request=self.context.get('request'),
            username=username,
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                _("Identifiants incorrects. Vérifiez votre nom d'utilisateur et mot de passe.")
            )

        if not user.is_active:
            raise serializers.ValidationError(
                _("Ce compte est désactivé. Contactez l'administrateur.")
            )

        # Vérifier que l'utilisateur est bien un marketeur lié
        if not getattr(user, 'is_marketeur_role', False):
            raise serializers.ValidationError(
                _("Ce compte n'a pas accès à l'application mobile.")
            )

        if not getattr(user, 'marketeur', None):
            raise serializers.ValidationError(
                _("Aucun marketeur associé à ce compte. Contactez l'administrateur.")
            )

        attrs['user'] = user
        return attrs


class TokenResponseSerializer(serializers.Serializer):
    """Réponse après login réussi."""
    access  = serializers.CharField(read_only=True, help_text="Token d'accès JWT (15 min)")
    refresh = serializers.CharField(read_only=True, help_text="Token de rafraîchissement (7 jours)")
    user    = serializers.SerializerMethodField()

    def get_user(self, obj):
        from api.v1.permissions import permissions_dict

        user = obj.get('user')
        if not user:
            return {}
        mkt = getattr(user, 'marketeur', None)
        return {
            'id':              user.id,
            'username':        user.username,
            'full_name':       user.get_full_name() or user.username,
            'email':           user.email,
            'marketeur_id':    mkt.pk if mkt else None,
            'marketeur_nom':   mkt.raison_sociale if mkt else None,
            'marketeur_sigle': mkt.sigle if mkt else None,
            'permissions':     permissions_dict(user),
        }
