from django.urls import path

from .views import (
    AuditLogView, CreerUtilisateurView, DetailUtilisateurView,
    ListeUtilisateursView, ModifierUtilisateurView, MonProfilView,
    ListeRolesView, DetailRoleView, CreerRoleView, ModifierRoleView,
    SupprimerRoleView, ListePermissionsView,
)

urlpatterns = [
    # Utilisateurs
    path('utilisateurs/',                   ListeUtilisateursView.as_view(),   name='users_liste'),
    path('utilisateurs/nouveau/',           CreerUtilisateurView.as_view(),    name='users_creer'),
    path('utilisateurs/<int:pk>/',          DetailUtilisateurView.as_view(),   name='users_detail'),
    path('utilisateurs/<int:pk>/modifier/', ModifierUtilisateurView.as_view(), name='users_modifier'),
    path('mon-profil/',                     MonProfilView.as_view(),           name='users_mon_profil'),
    path('audit/',                          AuditLogView.as_view(),            name='users_audit'),

    # Rôles
    path('roles/',                    ListeRolesView.as_view(),       name='roles_liste'),
    path('roles/nouveau/',            CreerRoleView.as_view(),        name='roles_creer'),
    path('roles/<int:pk>/',           DetailRoleView.as_view(),       name='roles_detail'),
    path('roles/<int:pk>/modifier/',  ModifierRoleView.as_view(),     name='roles_modifier'),
    path('roles/<int:pk>/supprimer/', SupprimerRoleView.as_view(),    name='roles_supprimer'),
    path('permissions/',              ListePermissionsView.as_view(), name='permissions_liste'),
]
