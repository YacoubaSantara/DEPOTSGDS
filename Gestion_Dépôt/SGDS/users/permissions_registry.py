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
            ('voir_mouvement',      'Consulter les mouvements'),
            ('ajouter_mouvement',   'Créer un mouvement'),
            ('modifier_mouvement',  'Modifier un mouvement'),
            ('supprimer_mouvement', 'Supprimer un mouvement'),
            ('exporter_mouvement',  'Exporter les mouvements'),
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
            ('voir_cuve',         'Consulter les cuves'),
            ('modifier_cuve',     'Modifier une cuve'),
            ('voir_produit',      'Consulter les produits'),
            ('modifier_produit',  'Modifier un produit'),
            ('voir_camion',       'Consulter les camions'),
            ('modifier_camion',   'Modifier un camion'),
            ('voir_chauffeur',    'Consulter les chauffeurs'),
            ('modifier_chauffeur','Modifier un chauffeur'),
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
        ],
    },
}


# Mapping rôle système → permissions par défaut
# Reproduit exactement la matrice SGDS/users/permissions.py
ROLES_SYSTEME_PERMISSIONS = {
    'SUPERADMIN': '__ALL__',

    'CHEF_DEPOT': [
        'voir_mouvement', 'ajouter_mouvement', 'modifier_mouvement',
        'supprimer_mouvement', 'exporter_mouvement',
        'voir_jaugeage', 'ajouter_jaugeage', 'modifier_jaugeage',
        'valider_jaugeage', 'supprimer_jaugeage',
        'voir_periode', 'ouvrir_periode', 'cloturer_periode',
        'voir_coulage', 'exporter_coulage',
        'voir_frais_passage', 'exporter_frais_passage',
        'voir_suivi_evolution',
        'voir_marketeur', 'ajouter_marketeur', 'modifier_marketeur',
        'voir_cuve', 'modifier_cuve',
        'voir_produit', 'modifier_produit',
        'voir_camion', 'modifier_camion',
        'voir_chauffeur', 'modifier_chauffeur',
        'voir_utilisateur', 'voir_audit',
        'voir_societe', 'modifier_societe',
    ],

    'OPERATEUR': [
        'voir_mouvement', 'ajouter_mouvement', 'modifier_mouvement',
        'voir_jaugeage', 'ajouter_jaugeage', 'modifier_jaugeage',
        'valider_jaugeage',
        'voir_periode',
        'voir_coulage', 'voir_frais_passage', 'voir_suivi_evolution',
        'voir_marketeur', 'voir_cuve', 'voir_produit',
        'voir_camion', 'voir_chauffeur',
    ],

    'COMPTABLE': [
        'voir_mouvement', 'exporter_mouvement',
        'voir_jaugeage',
        'voir_periode',
        'voir_coulage', 'exporter_coulage',
        'voir_frais_passage', 'exporter_frais_passage',
        'voir_suivi_evolution',
        'voir_marketeur', 'voir_cuve', 'voir_produit',
    ],

    'LECTEUR': [
        'voir_mouvement', 'voir_jaugeage', 'voir_periode',
        'voir_coulage', 'voir_frais_passage', 'voir_suivi_evolution',
        'voir_marketeur', 'voir_cuve', 'voir_produit',
        'voir_camion', 'voir_chauffeur',
    ],
}
