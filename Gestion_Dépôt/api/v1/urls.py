"""
Routes API v1 — SGDS Mobile.

Préfixe : /api/v1/

  Auth
  ────
  POST   auth/login/         → obtenir JWT
  POST   auth/refresh/       → renouveler l'access token
  POST   auth/logout/        → invalider le refresh token

  Dashboard
  ─────────
  GET    dashboard/          → KPIs + derniers mouvements

  Mouvements
  ──────────
  GET    mouvements/         → liste paginée (filtres disponibles)
  GET    mouvements/{id}/    → détail d'un mouvement

  États
  ─────
  GET    etats/stock-global/ → état global de stock
  GET    etats/produits/     → produits disponibles (pour filtres)
  GET    etats/periodes/     → périodes comptables (pour filtres)

  Profil
  ──────
  GET    profil/             → mon profil
  PATCH  profil/             → modifier mon profil
  POST   profil/password/    → changer mon mot de passe
"""
from django.urls import path

from api.v1.auth.views          import LoginView, LogoutView, TokenRefreshAPIView
from api.v1.dashboard.views     import DashboardView
from api.v1.mouvements.views    import MouvementListView, MouvementDetailView, MouvementBordereauPdfView, MouvementDocumentsView, DocumentDetailView
from api.v1.etats.views         import (
    StockGlobalView, RecapView, ProduitsView, PeriodesView,
    StockOuvertureFermetureView, FraisPassageView, CoulageView,
)
from api.v1.profil.views        import ProfilView, ChangePasswordView
from api.v1.notifications.views import NotificationsView

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────
    path('auth/login/',   LoginView.as_view(),        name='api_login'),
    path('auth/refresh/', TokenRefreshAPIView.as_view(), name='api_token_refresh'),
    path('auth/logout/',  LogoutView.as_view(),       name='api_logout'),

    # ── Dashboard ─────────────────────────────────────────────
    path('dashboard/',    DashboardView.as_view(),    name='api_dashboard'),

    # ── Mouvements ────────────────────────────────────────────
    path('mouvements/',                              MouvementListView.as_view(),      name='api_mouvements_list'),
    path('mouvements/<int:pk>/',                     MouvementDetailView.as_view(),       name='api_mouvement_detail'),
    path('mouvements/<int:pk>/bordereau.pdf/',       MouvementBordereauPdfView.as_view(), name='api_mouvement_bordereau_pdf'),
    path('mouvements/<int:pk>/documents/',           MouvementDocumentsView.as_view(),    name='api_mouvement_documents'),
    path('documents/<int:pk>/',                      DocumentDetailView.as_view(),     name='api_document_detail'),

    # ── États ─────────────────────────────────────────────────
    path('etats/stock-global/',    StockGlobalView.as_view(),            name='api_stock_global'),
    path('etats/recap/',           RecapView.as_view(),                  name='api_recap'),
    path('etats/stock-ouverture/', StockOuvertureFermetureView.as_view(), name='api_stock_ouverture'),
    path('etats/frais-passage/',   FraisPassageView.as_view(),           name='api_frais_passage'),
    path('etats/coulage/',         CoulageView.as_view(),                name='api_coulage'),
    path('etats/produits/',        ProduitsView.as_view(),               name='api_produits'),
    path('etats/periodes/',        PeriodesView.as_view(),               name='api_periodes'),

    # ── Profil ────────────────────────────────────────────────
    path('profil/',           ProfilView.as_view(),        name='api_profil'),
    path('profil/password/',  ChangePasswordView.as_view(), name='api_change_password'),

    # ── Notifications ─────────────────────────────────────────
    path('notifications/',    NotificationsView.as_view(), name='api_notifications'),
]
