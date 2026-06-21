from django.urls import path
from . import views

# Django fournit nativement <uuid:...> et <slug:...> — aucun register_converter nécessaire.

urlpatterns = [

    # Tableau de bord admin
    path('tableau-de-bord/',  views.admin_dashboard, name='admin_dashboard'),

    # Inventaire initial marketeur
    path('inventaire-initial/',                                    views.inventaire_initial_liste,    name='inventaire_initial_liste'),
    path('inventaire-initial/saisir/',                             views.inventaire_initial_saisir,   name='inventaire_initial_saisir'),
    path('inventaire-initial/saisie-masse/',                       views.inventaire_initial_masse,    name='inventaire_initial_masse'),
    path('inventaire-initial/<uuid:uuid>/supprimer/',              views.inventaire_initial_supprimer, name='inventaire_initial_supprimer'),


    # Espace Marketeur (client)
    path('mon-espace/',             views.client_dashboard,   name='client_dashboard'),
    path('mon-espace/mouvements/',  views.client_mouvements,  name='client_mouvements'),
    path('mon-espace/mouvements/<uuid:uuid>/<slug:slug>/', views.client_mouvement_detail, name='client_mouvement_detail'),
    path('mon-espace/carte-stock/',              views.carte_stock,                   name='client_carte_stock'),
    path('mon-espace/carte-stock/export/',       views.carte_stock_export,            name='client_carte_stock_export'),
    path('mon-espace/stock-global/',             views.stock_global_marketeur,        name='client_stock_global'),
    path('mon-espace/stock-global/export/',      views.stock_global_marketeur_export, name='client_stock_global_export'),

    # Espace Marketeur - Etats mensuels
    path('mon-espace/mensuel/stock-ouverture/',            views.etat_stock_ouverture_marketeur,              name='client_mensuel_stock_ouverture'),
    path('mon-espace/mensuel/stock-fermeture/',            views.etat_stock_fermeture_marketeur,              name='client_mensuel_stock_fermeture'),
    path('mon-espace/mensuel/coulage-repartition/',        views.etat_coulage_repartition_marketeur,          name='client_mensuel_coulage_repartition'),
    path('mon-espace/mensuel/coulage-repartition/export/', views.etat_coulage_repartition_marketeur_export,   name='client_mensuel_coulage_repartition_export'),
    path('mon-espace/mensuel/stock-15/',                   views.etat_stock_mensuel_15_marketeur,             name='client_mensuel_stock_15'),
    path('mon-espace/mensuel/stock-15/export/',            views.etat_stock_mensuel_15_marketeur_export,      name='client_mensuel_stock_15_export'),
    path('mon-espace/mensuel/stock-ambiant/',              views.etat_stock_ambiant_marketeur,                name='client_mensuel_stock_ambiant'),
    path('mon-espace/mensuel/stock-ambiant/export/',       views.etat_stock_ambiant_marketeur_export,         name='client_mensuel_stock_ambiant_export'),
    path('mon-espace/mensuel/frais-passage/',              views.etat_frais_passage_mensuel_marketeur,        name='client_mensuel_frais_passage'),
    path('mon-espace/mensuel/frais-passage/export/',       views.etat_frais_passage_mensuel_marketeur_export, name='client_mensuel_frais_passage_export'),

    # Etats (admin)
    path('etat/carte-stock/',                                                      views.etat_carte_stock_redirect,  name='etat_carte_stock_list'),
    path('etat/carte-stock/<uuid:marketeur_uuid>/<slug:marketeur_slug>/',          views.carte_stock_admin,          name='etat_carte_stock'),
    path('etat/carte-stock/<uuid:marketeur_uuid>/<slug:marketeur_slug>/export/',   views.carte_stock_export_admin,   name='etat_carte_stock_export'),
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
    path('etat/mensuel/stock-15/',                   views.etat_stock_mensuel_15,                  name='etat_mensuel_stock_15'),
    path('etat/mensuel/stock-15/export/',            views.etat_stock_mensuel_15_export,           name='etat_mensuel_stock_15_export'),
    path('etat/mensuel/stock-ambiant/',              views.etat_stock_ambiant,                     name='etat_mensuel_stock_ambiant'),
    path('etat/mensuel/stock-ambiant/export/',       views.etat_stock_ambiant_export,              name='etat_mensuel_stock_ambiant_export'),
    path('etat/mensuel/frais-passage/',              views.etat_frais_passage_mensuel,             name='etat_mensuel_frais_passage'),
    path('etat/mensuel/frais-passage/export/',       views.etat_frais_passage_mensuel_export,      name='etat_mensuel_frais_passage_export'),

    # Societe / Depot
    path('administration/societe/', views.societe_detail, name='societe_detail'),

    # Marketeurs
    path('marketeurs/',                                               views.marketeur_list,   name='marketeur_list'),
    path('marketeurs/nouveau/',                                       views.marketeur_create, name='marketeur_create'),
    path('marketeurs/<uuid:uuid>/<slug:slug>/',                       views.marketeur_detail, name='marketeur_detail'),
    path('marketeurs/<uuid:uuid>/<slug:slug>/modifier/',              views.marketeur_update, name='marketeur_update'),
    path('marketeurs/<uuid:uuid>/<slug:slug>/supprimer/',             views.marketeur_delete, name='marketeur_delete'),

    # Camions
    path('camions/',                                                  views.camion_list,   name='camion_list'),
    path('camions/nouveau/',                                          views.camion_create, name='camion_create'),
    path('camions/<uuid:uuid>/<slug:slug>/',                          views.camion_detail, name='camion_detail'),
    path('camions/<uuid:uuid>/<slug:slug>/modifier/',                 views.camion_update, name='camion_update'),
    path('camions/<uuid:uuid>/<slug:slug>/supprimer/',                views.camion_delete, name='camion_delete'),

    # Chauffeurs
    path('chauffeurs/',                                               views.chauffeur_list,   name='chauffeur_list'),
    path('chauffeurs/nouveau/',                                       views.chauffeur_create, name='chauffeur_create'),
    path('chauffeurs/<uuid:uuid>/<slug:slug>/',                       views.chauffeur_detail, name='chauffeur_detail'),
    path('chauffeurs/<uuid:uuid>/<slug:slug>/modifier/',              views.chauffeur_update, name='chauffeur_update'),
    path('chauffeurs/<uuid:uuid>/<slug:slug>/supprimer/',             views.chauffeur_delete, name='chauffeur_delete'),
    path('chauffeurs/<uuid:uuid>/<slug:slug>/badge/',                 views.chauffeur_badge,  name='chauffeur_badge'),

    # Familles
    path('familles/',                                                 views.famille_list,   name='famille_list'),
    path('familles/nouvelle/',                                        views.famille_create, name='famille_create'),
    path('familles/<uuid:uuid>/<slug:slug>/',                         views.famille_detail, name='famille_detail'),
    path('familles/<uuid:uuid>/<slug:slug>/modifier/',                views.famille_update, name='famille_update'),
    path('familles/<uuid:uuid>/<slug:slug>/supprimer/',               views.famille_delete, name='famille_delete'),

    # Produits
    path('produits/',                                                 views.produit_list,   name='produit_list'),
    path('produits/nouveau/',                                         views.produit_create, name='produit_create'),
    path('produits/<uuid:uuid>/<slug:slug>/',                         views.produit_detail, name='produit_detail'),
    path('produits/<uuid:uuid>/<slug:slug>/modifier/',                views.produit_update, name='produit_update'),
    path('produits/<uuid:uuid>/<slug:slug>/supprimer/',               views.produit_delete, name='produit_delete'),

    # Cuves
    path('cuves/',                                                    views.cuve_list,   name='cuve_list'),
    path('cuves/nouvelle/',                                           views.cuve_create, name='cuve_create'),
    path('cuves/<uuid:uuid>/<slug:slug>/',                            views.cuve_detail, name='cuve_detail'),
    path('cuves/<uuid:uuid>/<slug:slug>/modifier/',                   views.cuve_update, name='cuve_update'),
    path('cuves/<uuid:uuid>/<slug:slug>/supprimer/',                  views.cuve_delete, name='cuve_delete'),

    # Parametres de jaugeage
    path('parametres-jaugeage/',                                      views.parametre_list,          name='parametre_list'),
    path('parametres-jaugeage/<uuid:uuid>/<slug:slug>/',              views.parametre_detail,        name='parametre_detail'),
    path('cuves/<uuid:cuve_uuid>/<slug:cuve_slug>/parametres-jaugeage/', views.parametre_create_update, name='parametre_create_update'),
    path('parametres-jaugeage/<uuid:uuid>/<slug:slug>/supprimer/',    views.parametre_delete,        name='parametre_delete'),

    # Jaugeages
    path('jaugeages/',                                                views.jaugeage_list,    name='jaugeage_list'),
    path('jaugeages/nouveau/',                                        views.jaugeage_create,  name='jaugeage_create'),
    path('jaugeages/<uuid:uuid>/<slug:slug>/',                        views.jaugeage_detail,  name='jaugeage_detail'),
    path('jaugeages/<uuid:uuid>/<slug:slug>/modifier/',               views.jaugeage_update,  name='jaugeage_update'),
    path('jaugeages/<uuid:uuid>/<slug:slug>/supprimer/',              views.jaugeage_delete,  name='jaugeage_delete'),
    path('jaugeages/<uuid:uuid>/<slug:slug>/saisie/',                 views.jaugeage_saisie,    name='jaugeage_saisie'),
    path('jaugeages/<uuid:uuid>/<slug:slug>/rapport/',                views.jaugeage_rapport,   name='jaugeage_rapport'),
    path('jaugeages/<uuid:uuid>/<slug:slug>/valider/',                views.valider_jaugeage,   name='jaugeage_valider'),
    path('jaugeages/<uuid:uuid>/<slug:slug>/devalider/',              views.devalider_jaugeage, name='jaugeage_devalider'),

    # Parametres metrologiques
    path('parametres-metrologiques/',          views.parametres_metrologiques, name='parametres_metrologiques'),

    # Documents justificatifs
    path('mouvements/<uuid:mouvement_uuid>/<slug:mouvement_slug>/documents/upload/', views.mouvement_documents_upload,   name='mouvement_documents_upload'),
    path('documents/<uuid:document_uuid>/supprimer/',                                views.mouvement_document_supprimer, name='mouvement_document_supprimer'),
    path('documents/<uuid:document_uuid>/voir/',                                     views.mouvement_document_voir,      name='mouvement_document_voir'),

    # Mouvements
    path('mouvements/',                                               views.mouvement_liste,          name='mouvement_liste'),
    path('mouvements/export-pdf/',                                    views.mouvements_liste_pdf,     name='mouvements_liste_pdf'),
    path('mouvements/nouveau/',                                       views.mouvement_creer,          name='mouvement_creer'),
    path('mouvements/calcul-preview/',                                views.mouvement_calcul_preview, name='mouvement_calcul_preview'),
    path('mouvements/<uuid:uuid>/<slug:slug>/',                       views.mouvement_detail,         name='mouvement_detail'),
    path('mouvements/<uuid:uuid>/<slug:slug>/pdf/',                   views.mouvement_detail_pdf,     name='mouvement_detail_pdf'),
    path('mouvements/<uuid:uuid>/<slug:slug>/bordereau/',             views.mouvement_bordereau,      name='mouvement_bordereau'),
    path('mouvements/<uuid:uuid>/<slug:slug>/bordereau.pdf',          views.mouvement_bordereau_pdf,  name='mouvement_bordereau_pdf'),
    path('mouvements/<uuid:uuid>/<slug:slug>/modifier/',              views.mouvement_modifier,       name='mouvement_modifier'),
    path('mouvements/<uuid:uuid>/<slug:slug>/supprimer/',             views.mouvement_supprimer,      name='mouvement_supprimer'),

    # Espace marketeur — export mouvements PDF
    path('mon-espace/mouvements/export-pdf/', views.client_mouvements_pdf,    name='client_mouvements_pdf'),

    # Notifications marketeur
    path('espace/notifications/<uuid:notif_uuid>/lue/', views.notif_marquer_lue,    name='notif_marquer_lue'),
    path('espace/notifications/tout-lire/',             views.notif_tout_marquer_lu, name='notif_tout_marquer_lu'),

    # Periodes comptables
    path('periodes/',         views.ListePeriodesView.as_view(),  name='periode_liste'),
    path('periodes/ouvrir/',  views.OuvrirPeriodeView.as_view(),  name='periode_ouvrir'),

    # Exercices comptables
    path('exercices/',                   views.ListeExercicesView.as_view(),  name='exercice_liste'),
    path('exercices/<int:annee>/cloturer/', views.ClotureExerciceView.as_view(), name='exercice_cloturer'),

    # Coulage - Repartition mensuelle
    path('coulage/',                                                                          views.ListePeriodesCoulageView.as_view(), name='coulage_liste'),
    path('coulage/<uuid:periode_uuid>/<slug:periode_slug>/',                                  views.RepartitionCoulageView.as_view(),   name='coulage_detail'),
    path('coulage/<uuid:periode_uuid>/<slug:periode_slug>/cloturer/',                         views.ClotureCoulageView.as_view(),       name='coulage_cloture'),
    path('coulage/<uuid:periode_uuid>/<slug:periode_slug>/export/',                           views.ExportCoulageExcelView.as_view(),   name='coulage_export'),

    # Suivi evolution journalier
    path('coulage/<uuid:periode_uuid>/<slug:periode_slug>/suivi/<uuid:produit_uuid>/<slug:produit_slug>/',        views.SuiviEvolutionView.as_view(),   name='suivi_evolution'),
    path('coulage/<uuid:periode_uuid>/<slug:periode_slug>/suivi/<uuid:produit_uuid>/<slug:produit_slug>/export/', views.ExportSuiviExcelView.as_view(), name='suivi_export'),

    # Frais de passage
    path('coulage/<uuid:periode_uuid>/<slug:periode_slug>/frais-passage/',                    views.FraisPassageView.as_view(),            name='frais_passage'),
    path('coulage/<uuid:periode_uuid>/<slug:periode_slug>/frais-passage/export/',             views.ExportFraisPassageExcelView.as_view(), name='frais_passage_export'),
]
