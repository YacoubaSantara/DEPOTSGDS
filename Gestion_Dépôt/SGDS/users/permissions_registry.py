"""
Référentiel central des permissions métier SGDS.
Ajouter ici toute nouvelle permission, puis lancer :
    python manage.py sync_permissions
"""

PERMISSIONS_REGISTRY = {
    'mouvements': {
        'libelle': 'Mouvements',
        'icone': '📦',
        'permissions': [
            ('voir_mouvement',        'Consulter les mouvements'),
            ('voir_detail_mouvement', 'Voir le détail d\'un mouvement'),
            ('ajouter_mouvement',     'Créer un mouvement'),
            ('modifier_mouvement',    'Modifier un mouvement'),
            ('supprimer_mouvement',   'Supprimer un mouvement'),
            ('exporter_mouvement',    'Exporter les mouvements'),
        ],
    },
    'jaugeages': {
        'libelle': 'Jaugeages',
        'icone': '⚖️',
        'permissions': [
            ('voir_jaugeage',      'Consulter les jaugeages'),
            ('ajouter_jaugeage',   'Créer un jaugeage'),
            ('modifier_jaugeage',  'Modifier un jaugeage'),
            ('valider_jaugeage',   'Valider un jaugeage'),
            ('supprimer_jaugeage', 'Supprimer un jaugeage'),
        ],
    },
    'periodes': {
        'libelle': 'Périodes comptables',
        'icone': '📅',
        'permissions': [
            ('voir_periode',     'Consulter les périodes'),
            ('ouvrir_periode',   'Ouvrir une nouvelle période'),
            ('cloturer_periode', 'Clôturer une période'),
        ],
    },
    'exercices': {
        'libelle': 'Exercices comptables',
        'icone': '🗂️',
        'permissions': [
            ('voir_exercice',     'Consulter les exercices'),
            ('cloturer_exercice', 'Clôturer un exercice'),
        ],
    },
    'coulage': {
        'libelle': 'Coulage & Facturation',
        'icone': '💰',
        'permissions': [
            ('voir_coulage',           'Consulter la répartition du coulage'),
            ('exporter_coulage',       'Exporter les rapports coulage'),
            ('voir_frais_passage',     'Consulter les frais de passage'),
            ('exporter_frais_passage', 'Exporter les frais de passage'),
            ('voir_suivi_evolution',   "Consulter le suivi d'évolution"),
        ],
    },
    'referentiels': {
        'libelle': 'Référentiels',
        'icone': '📚',
        'permissions': [
            ('voir_marketeur',    'Consulter les marketeurs'),
            ('ajouter_marketeur', 'Créer un marketeur'),
            ('modifier_marketeur','Modifier un marketeur'),
            ('supprimer_marketeur','Supprimer un marketeur'),
            ('voir_inventaire',   "Consulter l'inventaire initial"),
            ('voir_cuve',         'Consulter les cuves'),
            ('modifier_cuve',     'Modifier une cuve'),
            ('voir_parametre_jaugeage', 'Consulter les paramètres de jaugeage'),
            ('voir_produit',      'Consulter les produits'),
            ('modifier_produit',  'Modifier un produit'),
            ('voir_famille',      'Consulter les familles'),
            ('voir_camion',       'Consulter les camions'),
            ('ajouter_camion',    'Créer un camion'),
            ('modifier_camion',   'Modifier un camion'),
            ('supprimer_camion',  'Supprimer un camion'),
            ('voir_chauffeur',    'Consulter les chauffeurs'),
            ('ajouter_chauffeur', 'Créer un chauffeur'),
            ('modifier_chauffeur','Modifier un chauffeur'),
            ('supprimer_chauffeur','Supprimer un chauffeur'),
            ('voir_parametre_metrologique', 'Consulter les paramètres métrologiques'),
        ],
    },
    'administration': {
        'libelle': 'Administration',
        'icone': '⚙️',
        'permissions': [
            ('voir_utilisateur',    'Consulter les utilisateurs'),
            ('gerer_utilisateur',   'Créer/modifier/désactiver les utilisateurs'),
            ('gerer_role',          'Gérer les rôles et permissions'),
            ('voir_audit',          "Consulter le journal d'audit"),
            ('modifier_parametres', 'Modifier les paramètres système'),
            ('voir_societe',        'Consulter la fiche société / dépôt'),
            ('modifier_societe',    'Modifier la fiche société / dépôt'),
            ('gerer_depot',         'Gérer la liste des dépôts'),
            ('voir_gabarit_email_etat_mensuel',    "Consulter/modifier le gabarit d'email des états mensuels"),
            ('voir_historique_envoi_etat_mensuel', "Consulter l'historique des envois d'états mensuels"),
            ('voir_gabarit_email_mouvement',       "Consulter/modifier le gabarit d'email des mouvements"),
        ],
    },
    'etats': {
        'libelle': 'États & rapports',
        'icone': '📊',
        'permissions': [
            ('voir_etat', "Consulter les états et rapports de stock (espace marketeur)"),
            ('voir_carte_stock',        'Consulter la carte de stock'),
            ('voir_stock_global',       'Consulter le stock global'),
            ('voir_stock_ouverture_fermeture', 'Consulter le stock ouverture/fermeture mensuel'),
            ('voir_etat_global_depot',  "Consulter l'état global dépôt mensuel"),
            ('voir_etat_rjj',           "Consulter l'état RJJ mensuel"),
            ('voir_etat_stock_15',      'Consulter le stock à 15° mensuel'),
            ('voir_etat_stock_ambiant', 'Consulter le stock ambiant mensuel'),
        ],
    },
}


# Mapping rôle système → permissions par défaut
# Reproduit exactement la matrice SGDS/users/permissions.py
ROLES_SYSTEME_PERMISSIONS = {
    'SUPERADMIN': '__ALL__',

    'CHEF_DEPOT': [
        'voir_mouvement', 'voir_detail_mouvement',
        'ajouter_mouvement', 'modifier_mouvement',
        'supprimer_mouvement', 'exporter_mouvement',
        'voir_jaugeage', 'ajouter_jaugeage', 'modifier_jaugeage',
        'valider_jaugeage', 'supprimer_jaugeage',
        'voir_periode', 'ouvrir_periode', 'cloturer_periode',
        'voir_exercice', 'cloturer_exercice',
        'voir_coulage', 'exporter_coulage',
        'voir_frais_passage', 'exporter_frais_passage',
        'voir_suivi_evolution',
        'voir_marketeur', 'ajouter_marketeur', 'modifier_marketeur',
        'voir_inventaire',
        'voir_cuve', 'modifier_cuve', 'voir_parametre_jaugeage',
        'voir_produit', 'modifier_produit',
        'voir_famille',
        'voir_camion', 'ajouter_camion', 'modifier_camion', 'supprimer_camion',
        'voir_chauffeur', 'ajouter_chauffeur', 'modifier_chauffeur', 'supprimer_chauffeur',
        'voir_utilisateur', 'voir_audit',
        'voir_societe', 'modifier_societe',
        'voir_gabarit_email_etat_mensuel', 'voir_historique_envoi_etat_mensuel', 'voir_gabarit_email_mouvement',
        'voir_parametre_metrologique',
        'voir_carte_stock', 'voir_stock_global', 'voir_stock_ouverture_fermeture',
        'voir_etat_global_depot', 'voir_etat_rjj', 'voir_etat_stock_15', 'voir_etat_stock_ambiant',
    ],

    'OPERATEUR': [
        'voir_mouvement', 'voir_detail_mouvement',
        'ajouter_mouvement', 'modifier_mouvement',
        'voir_jaugeage', 'ajouter_jaugeage', 'modifier_jaugeage',
        'valider_jaugeage',
        'voir_periode', 'voir_exercice',
        'voir_coulage', 'voir_frais_passage', 'voir_suivi_evolution',
        'voir_marketeur', 'voir_inventaire', 'voir_cuve', 'voir_produit', 'voir_famille',
        'voir_parametre_jaugeage', 'voir_parametre_metrologique',
        'voir_camion', 'ajouter_camion', 'modifier_camion',
        'voir_chauffeur', 'ajouter_chauffeur', 'modifier_chauffeur',
        'voir_carte_stock', 'voir_stock_global',
        'voir_etat_global_depot', 'voir_etat_rjj', 'voir_etat_stock_15', 'voir_etat_stock_ambiant',
    ],

    'COMPTABLE': [
        'voir_mouvement', 'voir_detail_mouvement', 'exporter_mouvement',
        'voir_jaugeage',
        'voir_periode', 'voir_exercice',
        'voir_coulage', 'exporter_coulage',
        'voir_frais_passage', 'exporter_frais_passage',
        'voir_suivi_evolution',
        'voir_marketeur', 'voir_inventaire', 'voir_cuve', 'voir_produit', 'voir_famille',
        'voir_parametre_jaugeage', 'voir_parametre_metrologique',
        'voir_camion', 'voir_chauffeur',
        'voir_carte_stock', 'voir_stock_global',
        'voir_etat_global_depot', 'voir_etat_rjj', 'voir_etat_stock_15', 'voir_etat_stock_ambiant',
    ],

    'LECTEUR': [
        'voir_mouvement', 'voir_detail_mouvement',
        'voir_jaugeage', 'voir_periode', 'voir_exercice',
        'voir_coulage', 'voir_frais_passage', 'voir_suivi_evolution',
        'voir_marketeur', 'voir_inventaire', 'voir_cuve', 'voir_produit', 'voir_famille',
        'voir_parametre_jaugeage', 'voir_parametre_metrologique',
        'voir_camion', 'voir_chauffeur',
        'voir_carte_stock', 'voir_stock_global',
        'voir_etat_global_depot', 'voir_etat_rjj', 'voir_etat_stock_15', 'voir_etat_stock_ambiant',
    ],

    # Accès espace marketeur : @marketeur_required vérifie le rôle légataire
    # (user.is_marketeur_role), ET chaque vue est aussi décorée par
    # voir_required(codename) — retirer une permission ici bloque réellement
    # le menu/l'écran correspondant pour les marketeurs, ce n'est plus
    # seulement déclaratif.
    'MARKETEUR': [
        'voir_mouvement', 'voir_detail_mouvement', 'exporter_mouvement',
        'voir_camion', 'ajouter_camion', 'modifier_camion', 'supprimer_camion',
        'voir_chauffeur', 'ajouter_chauffeur', 'modifier_chauffeur', 'supprimer_chauffeur',
        'voir_coulage', 'voir_frais_passage',
        'voir_etat',
    ],
}
