from django.urls import path
from . import views

urlpatterns = [

    # Tableau de bord admin
    path('tableau-de-bord/',  views.admin_dashboard, name='admin_dashboard'),

    # Inventaire initial marketeur
    path('inventaire-initial/',                          views.inventaire_initial_liste,    name='inventaire_initial_liste'),
    path('inventaire-initial/saisir/',                   views.inventaire_initial_saisir,   name='inventaire_initial_saisir'),
    path('inventaire-initial/saisie-masse/',             views.inventaire_initial_masse,    name='inventaire_initial_masse'),
    path('inventaire-initial/<int:pk>/supprimer/',       views.inventaire_initial_supprimer, name='inventaire_initial_supprimer'),


    # Espace Marketeur (client)
    path('mon-espace/',             views.client_dashboard,   name='client_dashboard'),
    path('mon-espace/mouvements/',  views.client_mouvements,  name='client_mouvements'),
    path('mon-espace/carte-stock/',              views.carte_stock,                   name='client_carte_stock'),
    path('mon-espace/carte-stock/export/',       views.carte_stock_export,            name='client_carte_stock_export'),
    path('mon-espace/stock-global/',             views.stock_global_marketeur,        name='client_stock_global'),
    path('mon-espace/stock-global/export/',      views.stock_global_marketeur_export, name='client_stock_global_export'),

    # Espace Marketeur - Etats mensuels
    path('mon-espace/mensuel/coulage-repartition/',        views.etat_coulage_repartition_marketeur,          name='client_mensuel_coulage_repartition'),
    path('mon-espace/mensuel/coulage-repartition/export/', views.etat_coulage_repartition_marketeur_export,   name='client_mensuel_coulage_repartition_export'),
    path('mon-espace/mensuel/stock-a/',                    views.etat_stock_mensuel_a_marketeur,              name='client_mensuel_stock_a'),
    path('mon-espace/mensuel/stock-a/export/',             views.etat_stock_mensuel_a_marketeur_export,       name='client_mensuel_stock_a_export'),
    path('mon-espace/mensuel/stock-b/',                    views.etat_stock_mensuel_b_marketeur,              name='client_mensuel_stock_b'),
    path('mon-espace/mensuel/stock-b/export/',             views.etat_stock_mensuel_b_marketeur_export,       name='client_mensuel_stock_b_export'),
    path('mon-espace/mensuel/frais-passage/',              views.etat_frais_passage_mensuel_marketeur,        name='client_mensuel_frais_passage'),
    path('mon-espace/mensuel/frais-passage/export/',       views.etat_frais_passage_mensuel_marketeur_export, name='client_mensuel_frais_passage_export'),

    # Etats (admin)
    path('etat/carte-stock/',                           views.etat_carte_stock_redirect,  name='etat_carte_stock_list'),
    path('etat/carte-stock/<int:marketeur_pk>/',        views.carte_stock_admin,          name='etat_carte_stock'),
    path('etat/carte-stock/<int:marketeur_pk>/export/', views.carte_stock_export_admin,   name='etat_carte_stock_export'),
    path('etat/stock-global/',                          views.stock_global_admin,         name='etat_stock_global'),
    path('etat/stock-global/export/',                   views.stock_global_admin_export,  name='etat_stock_global_export'),

    # Etats mensuels (admin / chef depot)
    path('etat/mensuel/stock-ouverture/',            views.etat_stock_ouverture_fermeture,         name='etat_mensuel_stock_ouverture'),
    path('etat/mensuel/stock-ouverture/export/',     views.etat_stock_ouverture_fermeture_export,  name='etat_mensuel_stock_ouverture_export'),
    path('etat/mensuel/stock-fermeture/',            views.etat_stock_fermeture,                   name='etat_mensuel_stock_fermeture'),
    path('etat/mensuel/stock-fermeture/export/',     views.etat_stock_fermeture_export,            name='etat_mensuel_stock_fermeture_export'),
    path('etat/mensuel/global-depot/',               views.etat_global_mensuel_depot,              name='etat_mensuel_global_depot'),
    path('etat/mensuel/global-depot/export/',        views.etat_global_mensuel_depot_export,       name='etat_mensuel_global_depot_export'),
    path('etat/mensuel/rjj/',                        views.etat_global_mensuel_rjj,                name='etat_mensuel_rjj'),
    path('etat/mensuel/rjj/export/',                 views.etat_global_mensuel_rjj_export,         name='etat_mensuel_rjj_export'),
    path('etat/mensuel/coulage-repartition/',        views.etat_coulage_repartition,               name='etat_mensuel_coulage_repartition'),
    path('etat/mensuel/coulage-repartition/export/', views.etat_coulage_repartition_export,        name='etat_mensuel_coulage_repartition_export'),
    path('etat/mensuel/stock-a/',                    views.etat_stock_mensuel_a,                   name='etat_mensuel_stock_a'),
    path('etat/mensuel/stock-a/export/',             views.etat_stock_mensuel_a_export,            name='etat_mensuel_stock_a_export'),
    path('etat/mensuel/stock-b/',                    views.etat_stock_mensuel_b,                   name='etat_mensuel_stock_b'),
    path('etat/mensuel/stock-b/export/',             views.etat_stock_mensuel_b_export,            name='etat_mensuel_stock_b_export'),
    path('etat/mensuel/frais-passage/',              views.etat_frais_passage_mensuel,             name='etat_mensuel_frais_passage'),
    path('etat/mensuel/frais-passage/export/',       views.etat_frais_passage_mensuel_export,      name='etat_mensuel_frais_passage_export'),

    # Societe / Depot
    path('administration/societe/', views.societe_detail, name='societe_detail'),

    # Marketeurs
    path('marketeurs/',                        views.marketeur_list,   name='marketeur_list'),
    path('marketeurs/nouveau/',                views.marketeur_create, name='marketeur_create'),
    path('marketeurs/<int:pk>/',               views.marketeur_detail, name='marketeur_detail'),
    path('marketeurs/<int:pk>/modifier/',      views.marketeur_update, name='marketeur_update'),
    path('marketeurs/<int:pk>/supprimer/',     views.marketeur_delete, name='marketeur_delete'),

    # Camions
    path('camions/',                           views.camion_list,   name='camion_list'),
    path('camions/nouveau/',                   views.camion_create, name='camion_create'),
    path('camions/<int:pk>/',                  views.camion_detail, name='camion_detail'),
    path('camions/<int:pk>/modifier/',         views.camion_update, name='camion_update'),
    path('camions/<int:pk>/supprimer/',        views.camion_delete, name='camion_delete'),

    # Chauffeurs
    path('chauffeurs/',                        views.chauffeur_list,   name='chauffeur_list'),
    path('chauffeurs/nouveau/',                views.chauffeur_create, name='chauffeur_create'),
    path('chauffeurs/<int:pk>/',               views.chauffeur_detail, name='chauffeur_detail'),
    path('chauffeurs/<int:pk>/modifier/',      views.chauffeur_update, name='chauffeur_update'),
    path('chauffeurs/<int:pk>/supprimer/',     views.chauffeur_delete, name='chauffeur_delete'),
    path('chauffeurs/<int:pk>/badge/',         views.chauffeur_badge,  name='chauffeur_badge'),

    # Familles
    path('familles/',                          views.famille_list,   name='famille_list'),
    path('familles/nouvelle/',                 views.famille_create, name='famille_create'),
    path('familles/<int:pk>/',                 views.famille_detail, name='famille_detail'),
    path('familles/<int:pk>/modifier/',        views.famille_update, name='famille_update'),
    path('familles/<int:pk>/supprimer/',       views.famille_delete, name='famille_delete'),

    # Produits
    path('produits/',                          views.produit_list,   name='produit_list'),
    path('produits/nouveau/',                  views.produit_create, name='produit_create'),
    path('produits/<int:pk>/',                 views.produit_detail, name='produit_detail'),
    path('produits/<int:pk>/modifier/',        views.produit_update, name='produit_update'),
    path('produits/<int:pk>/supprimer/',       views.produit_delete, name='produit_delete'),

    # Cuves
    path('cuves/',                             views.cuve_list,   name='cuve_list'),
    path('cuves/nouvelle/',                    views.cuve_create, name='cuve_create'),
    path('cuves/<int:pk>/',                    views.cuve_detail, name='cuve_detail'),
    path('cuves/<int:pk>/modifier/',           views.cuve_update, name='cuve_update'),
    path('cuves/<int:pk>/supprimer/',          views.cuve_delete, name='cuve_delete'),

    # Parametres de jaugeage
    path('parametres-jaugeage/',                              views.parametre_list,          name='parametre_list'),
    path('parametres-jaugeage/<int:pk>/',                     views.parametre_detail,        name='parametre_detail'),
    path('cuves/<int:cuve_pk>/parametres-jaugeage/',          views.parametre_create_update, name='parametre_create_update'),
    path('parametres-jaugeage/<int:pk>/supprimer/',           views.parametre_delete,        name='parametre_delete'),

    # Jaugeages
    path('jaugeages/',                         views.jaugeage_list,    name='jaugeage_list'),
    path('jaugeages/nouveau/',                 views.jaugeage_create,  name='jaugeage_create'),
    path('jaugeages/<int:pk>/',                views.jaugeage_detail,  name='jaugeage_detail'),
    path('jaugeages/<int:pk>/modifier/',       views.jaugeage_update,  name='jaugeage_update'),
    path('jaugeages/<int:pk>/supprimer/',      views.jaugeage_delete,  name='jaugeage_delete'),
    path('jaugeages/<int:pk>/saisie/',         views.jaugeage_saisie,    name='jaugeage_saisie'),
    path('jaugeages/<int:pk>/rapport/',        views.jaugeage_rapport,   name='jaugeage_rapport'),
    path('jaugeages/<int:pk>/valider/',        views.valider_jaugeage,   name='jaugeage_valider'),
    path('jaugeages/<int:pk>/devalider/',      views.devalider_jaugeage, name='jaugeage_devalider'),

    # Parametres metrologiques
    path('parametres-metrologiques/',          views.parametres_metrologiques, name='parametres_metrologiques'),

    # Mouvements
    path('mouvements/',                        views.mouvement_liste,          name='mouvement_liste'),
    path('mouvements/nouveau/',                views.mouvement_creer,          name='mouvement_creer'),
    path('mouvements/calcul-preview/',         views.mouvement_calcul_preview, name='mouvement_calcul_preview'),
    path('mouvements/<int:pk>/',               views.mouvement_detail,         name='mouvement_detail'),
    path('mouvements/<int:pk>/modifier/',      views.mouvement_modifier,       name='mouvement_modifier'),
    path('mouvements/<int:pk>/supprimer/',     views.mouvement_supprimer,      name='mouvement_supprimer'),

    # Notifications marketeur
    path('espace/notifications/<int:notif_id>/lue/', views.notif_marquer_lue,    name='notif_marquer_lue'),
    path('espace/notifications/tout-lire/',          views.notif_tout_marquer_lu, name='notif_tout_marquer_lu'),

    # Periodes comptables
    path('periodes/',         views.ListePeriodesView.as_view(),  name='periode_liste'),
    path('periodes/ouvrir/',  views.OuvrirPeriodeView.as_view(),  name='periode_ouvrir'),

    # Coulage - Repartition mensuelle
    path('coulage/',                                         views.ListePeriodesCoulageView.as_view(), name='coulage_liste'),
    path('coulage/<int:periode_id>/',                        views.RepartitionCoulageView.as_view(),   name='coulage_detail'),
    path('coulage/<int:periode_id>/cloturer/',               views.ClotureCoulageView.as_view(),       name='coulage_cloture'),
    path('coulage/<int:periode_id>/export/',                 views.ExportCoulageExcelView.as_view(),   name='coulage_export'),

    # Suivi evolution journalier
    path('coulage/<int:periode_id>/suivi/<int:produit_id>/',        views.SuiviEvolutionView.as_view(),       name='suivi_evolution'),
    path('coulage/<int:periode_id>/suivi/<int:produit_id>/export/', views.ExportSuiviExcelView.as_view(),     name='suivi_export'),

    # Frais de passage
    path('coulage/<int:periode_id>/frais-passage/',                 views.FraisPassageView.as_view(),            name='frais_passage'),
    path('coulage/<int:periode_id>/frais-passage/export/',          views.ExportFraisPassageExcelView.as_view(), name='frais_passage_export'),
]
