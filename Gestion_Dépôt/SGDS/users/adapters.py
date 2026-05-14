from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect


class SGDSSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Autorise la connexion SSO (Google/Microsoft) uniquement aux emails
    déjà enregistrés dans la base Django par un administrateur.
    Empêche la création automatique de comptes inconnus.
    """
    def pre_social_login(self, request, sociallogin):
        User = get_user_model()
        email = sociallogin.user.email

        if not email:
            messages.error(
                request,
                "Le fournisseur SSO n'a pas transmis votre adresse email.",
            )
            raise ImmediateHttpResponse(redirect('connexion'))

        try:
            user = User.objects.get(email=email)
            if not sociallogin.is_existing:
                sociallogin.connect(request, user)
        except User.DoesNotExist:
            messages.error(
                request,
                f"Aucun compte SGDS n'est associé à l'adresse {email}. "
                "Contactez votre administrateur pour créer votre compte "
                "avant de vous connecter via Google ou Microsoft.",
            )
            raise ImmediateHttpResponse(redirect('connexion'))
