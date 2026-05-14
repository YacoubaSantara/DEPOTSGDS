from django.urls import path
from . import views

urlpatterns = [

    # ── Authentification ─────────────────────────────────────
    path('auth/connexion/',   views.connexion,   name='connexion'),
    path('auth/deconnexion/', views.deconnexion, name='deconnexion'),
]
