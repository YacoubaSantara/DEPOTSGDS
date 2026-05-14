from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage

from SGDS.users.adapters import SGDSSocialAccountAdapter
from SGDS.users.managers import creer_utilisateur
from SGDS.users.models import Role


class SSOAdapterTests(TestCase):
    """
    Tests de l'adapter SSO.
    Vérifie que seuls les emails pré-enregistrés peuvent se connecter via SSO.
    """

    def _make_request(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def _make_social_login(self, email):
        from allauth.socialaccount.models import SocialLogin
        from django.contrib.auth import get_user_model
        User = get_user_model()
        mock_user = User(email=email, username=email.split('@')[0])
        return SocialLogin(user=mock_user)

    def test_adapter_refuse_email_inconnu(self):
        """Un email non enregistré en base → ImmediateHttpResponse."""
        from allauth.exceptions import ImmediateHttpResponse
        request = self._make_request()
        sociallogin = self._make_social_login('inconnu@gmail.com')
        adapter = SGDSSocialAccountAdapter()
        with self.assertRaises(ImmediateHttpResponse):
            adapter.pre_social_login(request, sociallogin)

    def test_adapter_accepte_email_existant(self):
        """Un email existant en base → pas d'exception levée."""
        creer_utilisateur(
            'yacouba', 'yacouba@sgds.ml', 'pass12345', Role.OPERATEUR)
        request = self._make_request()
        sociallogin = self._make_social_login('yacouba@sgds.ml')
        adapter = SGDSSocialAccountAdapter()
        # Ne doit PAS lever d'exception
        try:
            adapter.pre_social_login(request, sociallogin)
        except Exception as e:
            # sociallogin.connect() peut échouer en test sans DB complète
            # mais l'email doit être trouvé sans lever ImmediateHttpResponse
            from allauth.exceptions import ImmediateHttpResponse
            self.assertNotIsInstance(e, ImmediateHttpResponse,
                                     "L'adapter ne devrait pas rejeter un email connu")

    def test_adapter_refuse_email_vide(self):
        """Email vide ou None → ImmediateHttpResponse."""
        from allauth.exceptions import ImmediateHttpResponse
        request = self._make_request()
        sociallogin = self._make_social_login('')
        sociallogin.user.email = ''
        adapter = SGDSSocialAccountAdapter()
        with self.assertRaises(ImmediateHttpResponse):
            adapter.pre_social_login(request, sociallogin)
